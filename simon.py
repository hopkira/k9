#!/usr/bin/env python
# coding: utf-8
# Author: Richard Hopkins
# Date: 13 November 2022
#
# This program provides an additional
# robot state that plays Simon
#
import sys
import time
import random
import pyaudio
import wave
from back_panel import BackLights # k9 back lights
from voice import Voice
from listen import Listen
from eyes import Eyes # k9 led eyes
from memory import Memory

from state import State # Base FSM State class

k9eyes = Eyes()
k9lights = BackLights()
k9voice =  Voice()
k9stt = Listen()
mem = Memory()

MatchThis = ["Match these sequences","Follow these sequences","Copy me","Sequence follows","Can you remember these sequences?","Copy this","Match this","Sequences follow","K9 says copy this","Can you copy me?"]
EndOfGame = ["You scored","Your final score was","Your score is"]
Incorrect  = ["Incorrect button", "Error!", "Wrong button pressed", "Incorrect"]
TimeOut = ["Out of time", "Too slow", "Time expired", "Response too slow", "You are out of time"]

phrases = {
    "MatchThis" : MatchThis,
    "TimeOut" : TimeOut,
    "Incorrect" : Incorrect,
    "EndOfGame" : EndOfGame
}


class AudioStream:

    def __init__(self):
        """ Init audio stream """ 
        self.chunk  = 1024
        self.p = pyaudio.PyAudio()

    def play_file(self, file:str):
        self.wf = wave.open(file, 'rb')
        self.stream = self.p.open(
            format = self.p.get_format_from_width(self.wf.getsampwidth()),
            channels = self.wf.getnchannels(),
            rate = self.wf.getframerate(),
            output = True)
        data = self.wf.readframes(self.chunk)
        while data != b'':
            self.stream.write(data)
            data = self.wf.readframes(self.chunk)

    def close(self):
        """ Graceful shutdown """ 
        self.stream.close()
        self.p.terminate()


def blocking_speech(self,string:str):
    k9voice.speak(string)
    mem.storeState("speaking",1.0)
    while (mem.retrieveState("speaking") == 1.0):
        time.sleep(0.5)

def random_phrase(phrase:str) -> str:
    phrase_dict = phrases(phrase)
    length = len(phrase_dict)
    index = random.randint(0,length-1)
    message = phrase_dict[index] 
    return message


class Listening(State):
    def __init__(self):
        super(Listening, self).__init__()
        self.on_event('exit_program')

    def on_event(self, event):
        if event == 'exit_program':
            print("Returned state to Listening")
            sys.exit(0)
        return self


class Simon(State):
    '''
    The child state where K9 is playing Simon
    '''
    def __init__(self):
        super(Simon, self).__init__()
        self.simon_game = SimonGame()
        self.simon_game.game()
        self.on_event("game_over")

    def on_event(self, event):
        if event == 'game_over':
            return Listening ()
        return self


class K9SimonSM(object):
    '''
    A K9 finite state machine that starts in waiting state and
    will transition to a new state on when a transition event occurs.
    It also supports a run command to enable each state to have its
    own specific behaviours
    '''

    def __init__(self):
        ''' Initialise K9 in his Simon state. '''
        k9lights.on()
        k9eyes.set_level(1)
        blocking_speech("Entering Simon state")
        k9lights.off()
        k9eyes.set_level(0)
        self.state = Simon()

    def on_event(self,event):
        '''
        Process the incoming event using the on_event function of the
        current K9 state.  This may result in a change of state.
        '''

        # The next state will be the result of the on_event function.
        print("Event:",event, "raised in state", str(self.state).lower())
        self.state = self.state.on_event(event)


class SimonGame():
    '''
    Play a game of Simon
    '''

    def __init__(self):
        self.game_length = 3
        self.game_win = 32
        self.timeout = 3
        self.prefix = "/home/k9/music/FatBoy_trumpet-mp3_"
        self.suffix = ".wav"
        self.notes = ["E1","Db1","E2","A1","Db2","E4","A2","E3","E5","A3","Db3","E6"]

    def game(self):
        '''
        Controls game and score
        '''

        blocking_speech(random_phrase("MatchThis"))
        for move_num in range(self.game_length, self.game_win):
            if self.move(move_num):
                continue
            else:
                blocking_speech(random_phrase("EndOfGame"),str(move_num),"sequences")
                return

    def move(self, length:int) -> bool:
        '''
        Play and check a sequence of specific lengthh
        '''

        # K9 says match this pattern
        sequence = []
        play_stream = AudioStream()
        for seq in range(length):
            btn_num = random.randrange(12) + 1
            sequence.append(btn_num)
            k9lights.toggle(btn_num)
            note = self.prefix + self.notes[btn_num] + self.suffix
            play_stream.play_file(note)
        play_stream.close()
        for button in sequence:
            if self.right_button_pressed(button):
                continue
            else:
                return False
        return True

    def right_button_pressed(self, button:int) -> bool:
        '''
        Check if the button pressed is the right one

        '''

        start_time = time.time()
        start_state = k9lights.get_switch_state()
        while True:
            if time.time() - start_time > self.timeout:
                blocking_speech(random_phrase("TimeOut"))
                return False
            current_state = k9lights.get_switch_state()
            for num,state in enumerate(start_state):
                if start_state[num] ^ current_state[num] != 0:
                    if state == button:
                        return True
                    else:
                        blocking_speech(random_phrase("Incorrect"))
                        return False

try:
    k9 = K9SimonSM()

except KeyboardInterrupt:
    k9voice.speak("Inactive")
    k9lights.off()
    k9eyes.off()
    sys.exit(0)