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
import time
import random
#from tkinter.messagebox import NO
import requests
import pvporcupine  # Porcupine hotword
#import deepspeech  # Mozilla STT
#import numpy as np
#print("Numpy active...")
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
from ears import Ears # k9 radar ears
print("Ears wiggling...")
from k9gpt3conv import Respond # wolfram qa skill
print("Know it all mode active...")
#from k9tts import speak # speak in K9 voice
#print("Speech initiated...")
import paho.mqtt.client as mqtt
print("MQTT found...")
from tail import Tail
print("Tail activated!")
from  voice import Voice
print("Cleared voice...")
from listen import Listen
print("Able to listen...")
from k9_lichess_bot import ChessGame
print("Able to play chess!")
from memory import Memory
print("All imports done!")

# Standard phrases for K9 to use when needed
PraiseMe = ["Thanks are not necessary Master","Thank you Master","Happy to help Master","You are very welcome Master"]
PlayChess = ["Playing chess, Master","Chess is my favourite game","Prepare to lose!"]
QuestionMe = ["Apologies I do not understand","Not understood Master","I did not understand"]
StopListening = ["Entering silent mode", "No longer listening", "I will be quiet", "Conserving battery power"]
ComeHere = ["Coming master", "On my way", "Affirmative, coming!"]
FollowMe = ["Following master", "Affirmative, following you!", "Heeling master!"]
StayThere = ["Entering stationary mode", "Staying put master", "I will remain here", "Stopping"]
TurnAbout = ["Turning", "Turning around", "Turning about", "Reverse!"]
Blocked = ["I cannot rotate!","Warning obstruction", "Blocked", "Movement blocked", "Obstacle detected"]
phrases = { "PraiseMe" : PraiseMe,
            "PlayChess" : PlayChess,
            "QuestionMe" : QuestionMe,
            "StopListening" : StopListening,
            "ComeHere" : ComeHere,
            "FollowMe" : FollowMe,
            "StayThere" : StayThere,
            "TurnAbout" : TurnAbout,
            "Blocked" : Blocked}

# Define K9 Audio States   

class Waitforhotword(State):
    '''
    The child state where the k9 is waiting for the hotword
    '''
    def __init__(self):
        super(Waitforhotword, self).__init__()
        while (mem.retrieveState("speaking") == 1.0):
            time.sleep(0.2)
        k9lights.off()
        k9tail.center()
        k9eyes.set_level(0.001)
        print("Eyes set in hotword state")
        self.porcupine = pvporcupine.create(
            access_key = ACCESS_KEY,
            keyword_paths=['/home/pi/k9/canine_en_raspberry-pi_v2_1_0.ppn' ]
        )   
        self.recorder = PvRecorder(device_index=-1, frame_length=self.porcupine.frame_length)
        self.recorder.start()
        # print(f'Using device: {self.recorder.selected_device}')
        while True:
            pcm = self.recorder.read()
            result = self.porcupine.process(pcm)
            if result >= 0:
                print('AudioSM: Detected hotword')
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
        while (mem.retrieveState("speaking") == 1.0):
            time.sleep(0.2)
        self.command = None
        k9eyes.set_level(0.01)
        print("Eyes set in Listening state")
        self.command = k9stt.listen_for_command()
        print("Listening state heard:",self.command)
        k9eyes.set_level(0.0)
        self.on_event('command_received')

    def on_event(self, event):
        if event == 'command_received':
            return Responding(self.command)
        return self


class PlayChess(State):
    '''
    The child state where K9 is now listening for an utterance
    '''
    def __init__(self):
        super(PlayChess, self).__init__()
        chess_game = ChessGame()
        self.on_event('game_over')

    def on_event(self, event):
        if event == 'game_over':
            return Listening()
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
        # print("Responding.init() - started")
        # print(self.command)
        k9eyes.set_level(0.5)
        print("Eyes set in Responding state")
        k9ears.think()
        k9lights.on()
        if connected():
            intent, answer = k9qa.robot_response(self.command)
        else:
            if 'listen' in self.command:
                intent = 'StopListening'
            elif 'here' in self.command or 'over' in self.command:
                intent = 'ComeHere'
            elif 'follow' in self.command:
                intent = 'FollowMe'
            elif 'stop' in self.command or 'stay' in self.command:
                intent = 'StayThere'
            elif 'turn around' or 'about turn' in self.command:
                intent = 'TurnAbout'
            elif 'thank' in self.command:
                intent = 'PraiseMe'
                answer = random_phrase(intent)
            elif 'play chess' in self.command:
                intent = 'PlayChess'
            else:
                intent = 'QuestionMe'
                answer = random_phrase(intent)
        # Some phrases need a standard response
        answer_list = ('StopListening', 'ComeHere', 'FollowMe','StayThere','TurnAbout','PlayChess')
        if intent in answer_list:
            answer = random_phrase(intent)
        k9ears.stop()
        k9lights.off()
        print("Intent:",intent)
        mem.storeState("speaking",1.0)
        k9voice.speak(answer)
        self.on_event(intent)

    def notify_motors(self, event:str):
        client.publish(topic="k9/events/motor", payload = event, qos = 2, retain = False)

    def on_event(self, event:str) -> State:
        if event == 'StopListening':
            return Waitforhotword()
        elif event == 'ComeHere':
            k9tail.center()
            self.notify_motors(event)
            return Waitforhotword()
        elif event == 'FollowMe':
            k9tail.up()
            self.notify_motors(event)
            return Waitforhotword()
        elif event == 'StayThere':
            k9tail.down()
            self.notify_motors(event)
            return Waitforhotword()
        elif event == 'TurnAbout':
            self.notify_motors(event)
            return Waitforhotword()
        elif event == 'PraiseMe':
            k9tail.wag_h()
            return Listening()
        elif event == 'PlayChess':
            return PlayChess()
        else:
            return Listening()


class K9AudioSM(object):
    '''
    A K9 finite state machine that starts in waiting state and
    will transition to a new state on when a transition event occurs.
    It also supports a run command to enable each state to have its
    own specific behaviours
    '''

    def __init__(self):
        ''' Initialise K9 in his waiting state. '''
        k9lights.on()
        k9eyes.set_level(1)
        k9ears.scan()
        k9tail.center()
        k9voice.speak("Waiting for hotword")
        mem.storeState("speaking",1.0)
        while (mem.retrieveState("speaking") == 1.0):
            time.sleep(1.0)
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


def connected(timeout: float = 1.0) -> bool:
    try:
        requests.head("http://www.ibm.com/", timeout=timeout)
        return True
    except requests.ConnectionError:
        return False

def mqtt_callback(client, userdata, message):
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
    try:
        k9
    except NameError:
        pass
    else:
        k9.state.on_event(payload)

def random_phrase(phrase:str) -> str:
    phrase_dict = phrases(phrase)
    length = len(phrase_dict)
    index = random.randint(0,length-1)
    message = phrase_dict[index] 
    return message

# Set up mqtt client and subscribe to events
last_message = ""
client = mqtt.Client("k9-audio")
client.connect("localhost")
client.on_message = mqtt_callback # attach function to callback
# self.client.subscribe("/ble/advertise/watch/m")
client.subscribe("k9/events/audio", qos=2)
client.loop_start()
print("MQTT active...")

k9eyes = Eyes()
k9lights = BackLights()
k9ears = Ears()
k9qa = Respond()
k9tail = Tail()
mem = Memory()
k9voice =  Voice()
k9stt = Listen()

try:
    k9 = K9AudioSM()

except KeyboardInterrupt:
    k9voice.speak("Inactive")
    client.loop_stop()
    k9lights.off()
    k9eyes.off()
    k9tail.center()
    k9ears.stop()
    sys.exit(0)