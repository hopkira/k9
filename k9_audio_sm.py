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
from back_panel import BackLights # k9 back lights
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
print("Short term memory remembering...")
sys.path.append('..')
from who_uni.qanda import Backhistory
print("Back history loaded...")
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


class NotListening(State):
    '''
    The child state where K9 is doing absolutely nothing
    '''
    def __init__(self):
        super(NotListening, self).__init__()
        k9eyes.set_level(0.0)
        k9lights.off()
        turn_on_lights = [1,3,7,10,12]
        hot_switch = 2
        listen_switch = 11
        k9lights.cmd('computer')
        k9lights.turn_on(turn_on_lights)
        start_state = k9lights.get_switch_state()
        while True:
            time.sleep(0.2)
            try:
                current_state = k9lights.get_switch_state()
                if (start_state[hot_switch] ^ current_state[hot_switch]):
                    self.on_event('button_press_hotword')  
                if (start_state[listen_switch] ^ current_state[listen_switch]):
                    self.on_event('button_press_listen')  
            except IndexError:
                pass
    def on_event(self, event):
        if event == "button_press_hotword":
            return Waitforhotword()
        if event == "button_press_listen":
            return Listening()
        return self


class Waitforhotword(State):
    '''
    The child state where the k9 is waiting for the hotword
    '''
    def __init__(self):
        super(Waitforhotword, self).__init__()
        while (mem.retrieveState("speaking") == 1.0):
            time.sleep(0.2)
        turn_on_lights = [1,3,6,8,9]
        switch = 0
        k9lights.cmd('computer')
        k9lights.off()
        k9lights.turn_on(turn_on_lights)
        start_state = k9lights.get_switch_state()
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
        while not(start_state[switch] ^ current_state[switch]):
            pcm = self.recorder.read()
            result = self.porcupine.process(pcm)
            if result >= 0:
                self.porcupine.delete()
                self.recorder.delete()
                self.on_event('hotword_detected')
            current_state = k9lights.get_switch_state()
        self.on_event('button_press_no_listen')

    def on_event(self, event):
        if event == 'hotword_detected':
            return Listening()
        if event == 'button_press_no_listen':
            return NotListening()
        return self


class Listening(State):
    '''
    The child state where K9 is now listening for an utterance
    '''
    def __init__(self):
        super(Listening, self).__init__()
        while (mem.retrieveState("speaking") == 1.0):
            time.sleep(0.2)
        k9lights.cmd("green")
        self.command = None
        k9eyes.set_level(0.01)
        print("Eyes set in Listening state")
        self.command = k9stt.listen_for_command()
        print("Listening state heard:",self.command)
        k9eyes.set_level(0.0)
        self.on_event(self.command)

    def on_event(self, event):
        if event == "button_stop_listening":
            return Waitforhotword()
        else:
            return Responding(event)


class Demonstration(State):
    '''
    The child state where K9 is basically showing off
    '''
    def __init__(self):
        super(Demonstration, self).__init__()
        k9lights.cmd("original")
        k9lights.cmd("slowest")
        self.block_speech("Good morning School")
        self.block_speech("I am Kay Nine. I am a robot dog.")
        self.block_speech("I am built from inexpensive computer components such as a Raspberry Pi.")
        self.block_speech("My software is published for free on the Internet.")
        k9lights.cmd("two")
        k9lights.cmd("slow")
        self.block_speech("I can go for walks and even spin around!")
        self.notify_motors("Turn90Right")
        self.block_speech("My side screen responds to touch.  I have two cameras.")
        k9eyes.set_level(1.0)
        time.sleep(0.5)
        k9eyes.set_level(0.0)
        self.block_speech("The one in my head is for recognizing people")
        self.block_speech("The one on my front sees in three dimensions so I can avoid obstacles.")
        k9lights.cmd("three")
        k9lights.cmd("normal")
        self.notify_motors("Turn90Right")
        self.block_speech("I can even wag my tail to show that I am happy to be here.")
        k9lights.cmd("four")
        k9lights.cmd("fast")
        k9tail.wag_h()
        k9tail.wag_v()
        self.notify_motors("Turn180Right")
        k9ears.think()
        self.block_speech("My ears and back include light detection and ranging sensors known as LIE DARR.")
        self.block_speech("They enable me to look all around me.")
        k9ears.stop()
        k9lights.cmd("six")
        k9lights.cmd("fastest")
        try:
            angle = float(mem.retrieveState("rotate_angle"))
            self.notify_motors("TurnAngle" + str(angle))
            self.block_speech("You are the nearest obstacle!")
        except KeyError or ValueError:
            print("Error: no target found for demo, so staying put.")
        k9lights.cmd("original")
        k9lights.cmd("normal")
        self.on_event('demo_complete')

    def block_speech(self, speech:str):
        k9voice.speak(speech)
        mem.storeState("speaking",1.0)
        while (mem.retrieveState("speaking") == 1.0):
            time.sleep(0.2)
        k9eyes.set_level(0.1)
        time.sleep(0.75)
        return

    def notify_motors(self, event:str):
        client.publish(topic="k9/events/motor", payload = event, qos = 2, retain = False)

    def on_event(self, event):
        if event == "demo_complete":
            return Waitforhotword()
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
        k9lights.on()
        k9eyes.set_level(0.5)
        print("Eyes set in Responding state")
        k9ears.think()
        #
        # If K9 is connected to the internet, then OpenAI GPT-3 is used to
        # determine both the best answer and intent of the vocal command.
        # If the intent is a quesion, then the internal history database
        # is used to answer the question; if it doesn't know the answer
        # K9 will fall back
        # to a less specific and inaccurat GPT3
        #
        # When disconnected from the Internet, K9 will use simple word
        # recognition to infer the intent and will respond with one of
        # a stock set of phrases.
        #
        '''
        try:
            person_dict = mem.retrievePerson()
            self.name = person_dict['name']
            self.gender = person_dict['gender']
            self.bearing = float(person_dict['bearing'])
        except KeyError:
            self.name = 'Unknown'
            self.gender = 'Unknown'
        '''
        if connected():
            print("Calling respond using:", self.command)
            intent, answer = k9qa.robot_response(self.command)
            # intent, answer = k9qa.robot_response(self.command)
            if intent == 'QuestionMe':
                answer = k9history.get_answer(self.command)
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
            elif 'demo' in self.command:
                intent = 'ShowOff'
            else:
                intent = 'QuestionMe'
                answer = k9history.get_answer(self.command)
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
        elif event == 'ShowOff':
            return Demonstration()
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
        k9lights.cmd("on")
        k9eyes.set_level(1.0)
        k9ears.scan()
        k9tail.wag_h()
        k9tail.wag_v()
        k9tail.center()
        k9voice.speak("Waiting for command")
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
    phrase_dict = phrases[phrase]
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
k9stt = Listen(k9lights)
k9history = Backhistory()

# mem.storePerson("richard", "male", 0.0)

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