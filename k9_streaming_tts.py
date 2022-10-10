#!/usr/bin/env python
# coding: utf-8
# Author: Richard Hopkins
# Date: 31 August 2022
#
# This program runs a server to generate audio
# from text.
#
# Socket element based on:
# https://github.com/watson-developer-cloud/python-sdk/blob/master/examples/speaker_text_to_speech.py
#
import sys
import requests
import os
import pyaudio
import time
from subprocess import Popen

from ibm_watson import TextToSpeechV1
from ibm_watson.websocket import SynthesizeCallback
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

from memory import Memory
from eyes import Eyes

mem = Memory()
eyes = Eyes()

eye_level = None

import paho.mqtt.client as mqtt
print("MQTT found...")
from queue import Queue
print("Queues forming...")

# Create authentication and point to URL
authenticator = IAMAuthenticator(os.getenv("WATSON_STT_APIKEY"))
text_to_speech = TextToSpeechV1(authenticator = authenticator)
text_to_speech.set_service_url(os.getenv("WATSON_STT_URL"))
speech_file = os.getenv("PATH_TO_SPEECH_WAV")

class Play(object):
    """
    Wrapper to play the audio in a blocking mode
    """
    def __init__(self):
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 22050
        self.chunk = 1024
        self.pyaudio = None
        self.stream = None

    def start_streaming(self):
        self.pyaudio = pyaudio.PyAudio()
        self.stream = self._open_stream()
        self._start_stream()

    def _open_stream(self):
        stream = self.pyaudio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            output=True,
            frames_per_buffer=self.chunk,
            start=False
        )
        return stream

    def _start_stream(self):
        self.stream.start_stream()

    def write_stream(self, audio_stream):
        self.stream.write(audio_stream)

    def complete_playing(self):
        self.stream.stop_stream()
        self.stream.close()
        self.pyaudio.terminate()


class MySynthesizeCallback(SynthesizeCallback):
    def __init__(self):
        SynthesizeCallback.__init__(self)
        self.play = Play()

    def on_connected(self):
        self.play.start_streaming()

    def on_error(self, error):
        print('Error received: {}'.format(error))

    def on_timing_information(self, timing_information):
        print(timing_information)

    def on_audio_stream(self, audio_stream):
        self.play.write_stream(audio_stream)

    def on_close(self):
        self.play.complete_playing()



# These values control K9s voice
SPEED_DEFAULT = 150
SPEED_DOWN = 125
AMP_UP = 100
AMP_DEFAULT = 50
AMP_DOWN = 25
PITCH_DEFAULT = 99
PITCH_DOWN = 89
SOX_VOL_UP = 25
SOX_VOL_DEFAULT = 20
SOX_VOL_DOWN = 15
SOX_PITCH_UP = 100
SOX_PITCH_DEFAULT = 0
SOX_PITCH_DOWN = -100

def connected(timeout: float = 1.0) -> bool:
    try:
        requests.head("http://www.ibm.com/", timeout=timeout)
        return False # temporary change for testing (use local voice)
    except requests.ConnectionError:
        return False

def speak(speech:str) -> None:
    # mem.storeState("speaking",True)

    print('Speech server:', speech)
    if not connected():
        speak_local(speech)
    else:
        speak_socket(speech)
    mem.storeState("speaking",0.0)

def speak_socket(speech:str) -> None:
    tts_callback = MySynthesizeCallback()
    speech = "<speak><prosody pitch='+16st' rate='-20%'>" + speech + "</prosody></speak>"
    text_to_speech.synthesize_using_websocket(speech,
                                    tts_callback,
                                    accept='audio/wav',
                                    voice='en-GB_JamesV3Voice'
                                    )
    tts_callback.on_close()
    del tts_callback


def speak_watson(speech:str) -> None:
    # speech = speech.translate(None, "|<>")
    speech = "<speak><prosody pitch='+14st' rate='-20%'>" + speech + "</prosody></speak>"
    with open(speech_file, 'wb') as audio_file:
        audio_file.write(
            text_to_speech.synthesize(
                speech,
                voice='en-GB_JamesV3Voice',
                accept='audio/wav'        
            ).get_result().content)
    cmd = ['aplay', speech_file]
    speaking = Popen(cmd)
    Popen.wait(speaking)
    return

def speak_local(speech:str) -> None:
    '''
    Fallback speech option.
    Break speech up into clauses using | and speak each one with
    various pitches, volumes and distortions
    to make the voice more John Leeson like
    > will raise the pitch and amplitude
    < will lower it
    '''
    speaking = None
    clauses = speech.split("|")
    for clause in clauses:
        if clause and not clause.isspace():
            if clause[:1] == ">":
                clause = clause[1:]
                pitch = PITCH_DEFAULT
                speed = SPEED_DOWN
                amplitude = AMP_UP
                sox_vol = SOX_VOL_UP
                sox_pitch = SOX_PITCH_UP
            elif clause[:1] == "<":
                clause = clause[1:]
                pitch = PITCH_DOWN
                speed = SPEED_DOWN
                amplitude = AMP_DOWN
                sox_vol = SOX_VOL_DOWN
                sox_pitch = SOX_PITCH_DOWN
            else:
                pitch = PITCH_DEFAULT
                speed = SPEED_DEFAULT
                amplitude = AMP_DEFAULT
                sox_vol = SOX_VOL_DEFAULT
                sox_pitch = SOX_PITCH_DEFAULT
            #cmd = "espeak -v en-rp '%s' -p %s -s %s -a %s -z" % (clause, pitch, speed, amplitude)
            cmd = ['espeak','-v','en-rp',str(clause),'-p',str(pitch),'-s',str(speed),'-a',str(amplitude)]
            speaking = Popen(cmd)
            Popen.wait(speaking)
    return

def mqtt_callback(client, userdata, message):
    """
    Enables K9 to receive an MQTT message and place it in a queue
    """
    payload = str(message.payload.decode("utf-8"))
    queue.put(payload)

queue = Queue()
client = mqtt.Client("k9-speech-server")
client.connect("localhost")
client.on_message = mqtt_callback # attach function to callback
client.subscribe("k9/events/speech", qos=2)
# self.client.subscribe("/ble/advertise/watch/m")
client.loop_start()
print("Speech MQTT interface active")
speaking = False
try:
    while True:
        time.sleep(0.2)
        while not queue.empty():
            tts_callback = MySynthesizeCallback()
            speaking = True
            old_eye_level = eyes.get_level()
            eyes.set_level(0.5)
            mem.storeState("speaking",1.0)
            utterance = queue.get()
            if utterance is None:
                continue
            print("Voice server:", utterance)
            speak(utterance)
        if speaking == True:
            speaking = False
            mem.storeState("speaking",0.0)
            eyes.set_level(old_eye_level)
            
except KeyboardInterrupt:
    client.loop_stop()
    "K9 silenced and MQTT client stopped"
    sys.exit(0) 
