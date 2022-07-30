#!/usr/bin/env python
# coding: utf-8
# Author: Richard Hopkins
# Date: 6 April 2022
#
# This program runs the base state machine for
# the K9 robot audio.  It responds to commands received
# by voice and sends MQTT messsages to the 
# motor state machine.
#
import sys
#from tkinter.messagebox import NO
import pvporcupine  # Porcupine hotword
import deepspeech  # Mozilla STT
import numpy as np
print("Numpy active...")
from state import State # Base FSM State class
print("State machine with state...")
from pvrecorder import PvRecorder # Porcupine hotword
print("Recorder, recording...")
from secrets import ACCESS_KEY # API key
print("Access key found....")
from eyes import Eyes # k9 led eyes
print("Eyes open...")
from back_lights import BackLights # k9 back lights
print("Backlights on...")
from ears import K9Ears # k9 radar ears
print("Ears wiggling...")
from k9gpt3conv import K9QA # wolfram qa skill
print("Know it all mode active...")
from k9tts import speak # speak in K9 voice
print("Speech initiated...")
import paho.mqtt.client as mqtt
print("MQTT found...")
from audio_tools import VADAudio # Voice activity detection
print("Audio tools working...")
from memory import Memory
print("All imports done!")

# Define K9 Audio States   

class Waitforhotword(State):
    '''
    The child state where the k9 is waiting for the hotword
    '''
    def __init__(self):
        super(Waitforhotword, self).__init__()
        k9lights.off()
        self.porcupine = pvporcupine.create(
            access_key = ACCESS_KEY,
            keyword_paths=['/home/pi/k9localstt/canine_en_raspberry-pi_v2_1_0.ppn']
        )   
        self.recorder = PvRecorder(device_index=-1, frame_length=self.porcupine.frame_length)
        self.recorder.start()
        print(f'Using device: {self.recorder.selected_device}')
        k9eyes.set_level(0.001)
        while True:
            pcm = self.recorder.read()
            result = self.porcupine.process(pcm)
            if result >= 0:
                print('Detected hotword')
                self.on_event('hotword_detected')

    def on_event(self, event):
        if event == 'hotword_detected':
            if self.porcupine is not None:
                self.porcupine.delete()
            if self.recorder is not None:
                self.recorder.delete()
            return Listening()
        return self


class Listening(State):
    '''
    The child state where K9 is now listening for an utterance
    '''
    def __init__(self):
        super(Listening, self).__init__()
        self.vad_audio = VADAudio(aggressiveness=1,
        device=None,
        input_rate=16000,
        file=None)
        self.stream_context = model.createStream()
        print("Listening: init complete")
        k9eyes.set_level(0.01)
        k9lights.on()
        while True:
            self.frames = self.vad_audio.vad_collector()
            for frame in self.frames:
                if frame is not None:
                    self.stream_context.feedAudioContent(np.frombuffer(frame, np.int16))
                else:
                    print("Stream finished")
                    self.command = self.stream_context.finishStream()
                    del self.stream_context
                    print("Listen.run() - I heard:",self.command)
                    if self.command != "":
                        self.vad_audio.destroy()
                        self.on_event('command_received')
                    else:
                        self.stream_context = model.createStream()

    def on_event(self, event):
        if event == 'command_received':
            return Responding(self.command)
        return self


class Responding(State):
    '''
    The child state where K9 processes a response to the text
    if command is not understood, Wolfram Mathematica will be
    used to retrieve a result
    '''
    def __init__(self, command):
        super(Responding, self).__init__()
        self.command = command
        print("Responding.init() - started")
        print(self.command)
        k9eyes.set_level(0.5)
        if 'listen' in self.command:
            speak("No longer listening")
            self.on_event('stop_listening')
        if ('here' in self.command) or ('over' in self.command):
            speak("Coming master")
            self.on_event('scanning')
        if 'follow' in self.command:
            speak("Folllowing master")
            self.on_event('follow')
        if 'stop' in self.command or 'stay' in self.command:
            speak("Staying master")
            self.on_event('stay')
        k9ears.think()
        answer = k9qa.ask_question(self.command)
        k9ears.stop()
        speak(answer)
        self.on_event('responded')

    def on_event(self, event):
        if event == 'responded':
            return Listening()
        if event == 'stop_listening':
            return Waitforhotword()
        if event == 'scanning':
            # send MQTT Message for come
            self.client.publish("k9/events/motor", payload="come", qos=2, retain=False)
            return Listening()
        if event == 'follow':
            # send MQTT Message for heel
            self.client.publish("k9/events/motor", payload="heel", qos=2, retain=False)
            return Listening()
        if event == 'stay':
            self.client.publish("k9/events/motor", payload="stay", qos=2, retain=False)
            return Listening()
        return self


class K9AudioSM:
    '''
    A K9 finite state machine that starts in waiting state and
    will transition to a new state on when a transition event occurs.
    It also supports a run command to enable each state to have its
    own specific behaviours
    '''

    def __init__(self):
        ''' Initialise K9 in his waiting state. '''

        self.last_message = ""
        self.client = mqtt.Client("k9-audio")
        self.client.connect("localhost")
        self.client.on_message = self.mqtt_callback # attach function to callback
        # self.client.subscribe("/ble/advertise/watch/m")
        self.client.subscribe("k9/events/audio", qos=2)
        k9lights.on()
        k9eyes.set_level(1)
        k9ears.scan()
        self.client.loop_start()
        speak("K9 is active")
        k9lights.off()
        k9eyes.set_level(0)
        k9ears.stop()
        self.state = Waitforhotword()

    def on_event(self,event):
        '''
        Process the incoming event using the on_event function of the
        current K9 state.  This may result in a change of state.
        '''

        # The next state will be the result of the on_event function.
        print("Event:",event, "raised in state", str(self.state).lower())
        self.state = self.state.on_event(event)

    def mqtt_callback(self,client, userdata, message):
        """
        Enables K9 to receive a message from an Epruino Watch via
        MQTT over Bluetooth (BLE) to place it into active or inactive States
        """

        payload = str(message.payload.decode("utf-8"))
        #if payload != self.last_message:
        #    self.last_message = payload
        #    event = payload[3:-1].lower()
        #    # print("Event: ",str(event))
        print(str(payload)," received by audio state machine")
        self.on_event(payload)


model = deepspeech.Model("/home/pi/k9localstt/deepspeech-0.9.3-models.tflite")
model.enableExternalScorer("/home/pi/k9localstt/deepspeech-0.9.3-models.scorer")

print("Deepspeech loaded")

k9eyes = Eyes()
k9lights = BackLights()
k9ears = K9Ears()
k9qa = K9QA()
mem = Memory()
try:
    dog = K9AudioSM

except KeyboardInterrupt:
    speak("Inactive")
    k9lights.off()
    k9eyes.set_level(0)
    sys.exit(0)