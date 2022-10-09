#!/usr/bin/env python
# coding: utf-8
# Author: Richard Hopkins
# Date: 6 April 2022
#
# This program runs the motor state machine for
# the K9 robot and responds to commands received
# by MQTT/Bluetooth.
#
import time
import sys
#import json
import math
#from tkinter.messagebox import NO
import logo # k9 movement library
from state import State # Base FSM State class
import paho.mqtt.client as mqtt
print("MQTT found...")
from queue import Queue
from memory import Memory
from voice import Voice
print("All imports done!")

mem = Memory()
voice = Voice()

# Define K9 Motor States

class ManualControl(State):
    '''
    The state where K9 is waiting for movement commands
    '''
    def __init__(self):
        super(ManualControl, self).__init__()
        logo.stop()
        while True:
            while not queue.empty():
                message = queue.get()
                if message is None:
                    continue
                self.on_event(message)

    def on_event(self, event):
        if event == 'ComeHere':
            return Scanning()
        if event == 'FollowMe':
            return Following()
        if event == 'TurnAbout':
            return Turn_Around()
        return self


class Scanning(State):
    '''
    The state where K9 is looking for the nearest person to follow
    '''
    def __init__(self):
        super(Scanning, self).__init__()
        while True:
            self.target = None
            self.target = mem.retrieveLastSensorReading("person")
            try:
                if self.target['distance'] != 0.0 and self.target['angle'] != 0.0 :
                    self.on_event('person_found')
            except KeyError:
                pass

    def on_event(self, event):
        if event == 'person_found':
            k9.voice("Coming master")
            return Turning(self.target)
        return self


class Turning(State):
    '''
    The child state where K9 is turning towards the target person
    '''
    def __init__(self, target):
        super(Turning, self).__init__()
        self.angle = target["angle"]
        self.distance = target["distance"]
        if abs(self.angle) > 0.2 :
            print("Turning: Moving ",self.angle," radians towards target")
            logo.right(self.angle)
        else:
            self.on_event('turn_finished')
        while True:
            if logo.finished_move():
                self.on_event('turn_finished')
            # check to see if rotation is safe
            if mem.retrieveState("rotate") < 0.0:
                self.on_event('turn_blocked')

    def on_event(self, event):
        if event == 'turn_finished':
            return Moving_Forward(self.distance)
        if event == 'turn_blocked':
            voice.speak("Turn blocked")
            return ManualControl()
        if event == 'StayHere':
            voice.speak("Staying put")
            return  ManualControl()
        return self


class Turn_Around(State):
    '''
    The child state where K9 rotates by 180 degrees
    '''
    def __init__(self):
        super(Turn_Around, self).__init__()
        logo.right(math.pi)
        while True:
            if logo.finished_move():
                self.on_event('turn_finished')
            # check to see if rotation is safe
            if mem.retrieveState("rotate") < 0.0:
                voice.speak("Turn blocked")
                self.on_event('turn_blocked')

    def on_event(self, event):
        if event == 'turn_blocked':
            return ManualControl()
        if event == 'turn_finished':
            return ManualControl()
        return self


class Moving_Forward(State):
    '''
    The child state where K9 is moving forwards to the target
    '''
    def __init__(self, distance):
        super(Moving_Forward, self).__init__()
        self.distance = distance
        # self.avg_dist = 4.0
        # z = float(self.target.depth_z)
        # distance = float(z - SWEET_SPOT)
        if self.distance > 0:
            print("Moving Forward: ",self.distance,"m")
            # logo.forwards(self.distance)
        else:
            print("Moving Forward: no need to move")
            self.on_event('target_reached')
        while True:
            if not logo.finished_move():
                pass
            else:
                self.on_event('target_reached')

    def on_event(self, event):
        if event == 'target_reached':
            voice.speak("Master!")
            return ManualControl()
        if event == 'StayHere':
            voice.speak("Staying put")
            return  ManualControl()
        return self


class Following(State):
    '''
    Having reached the target, now follow it blindly
    '''
    def __init__(self):
        super(Following, self).__init__()
        logo.stop()
        while True:
            #
            # ADD: Listen for 'stay' commands from MQTT
            # 
            # retrieve direction and distance from Redis
            target_dict = mem.retrieveLastSensorReading("follow")
            if target_dict["angle"] != 0 and target_dict["distance"] != 0 :
                self.angle = target_dict["angle"]
                self.move = target_dict["distance"]
                print("Following: direction:", self.angle, "distance:", self.move)
                damp_angle = 2.0
                damp_distance = 2.0
                if abs(self.angle) >= (0.1 * damp_angle) :
                    if mem.retrieveState("rotate") > 0.0:
                        logo.rt(self.angle / damp_angle, fast = True)
                        print("Turning: ",str(self.angle / damp_angle))
                    else:
                        voice.speak("Turn blocked")
                        time.sleep(3.0)
                else:
                    if abs(self.move) >= (0.05 * damp_distance) :
                        distance = self.move / damp_distance
                        safe_forward = mem.retrieveState("forward")
                        # nb should also retrieve a backward state
                        if  safe_forward > distance:
                            # logo.forward(distance)
                            print("Moving forward: ", str(distance) )
                        else:
                            # logo.forward(safe_forward)
                            print("Moving forward: ", str(safe_forward))

    def on_event(self, event):
        if event == 'StayHere':
            voice.speak("Staying here")
            return ManualControl()
        if event == 'turn_blocked':
            voice.speak("Turn blocked")
            return ManualControl()
        return self


class K9MotorSM:
    '''
    A K9 finite state machine that starts in manual control state and
    will transition to a new state on when a transition event occurs.
    '''

    def __init__(self):
        ''' Initialise K9 in his manual control state. '''
        self.state = ManualControl()

    def on_event(self,event):
        '''
        Process the incoming event using the on_event function of the
        current K9 state.  This may result in a change of state.
        '''

        # The next state will be the result of the on_event function.
        print("Event:",event, "raised in state", str(self.state).lower())
        self.state = self.state.on_event(event)


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
    '''
    try:
        k9
    except NameError:
        pass
    else:
        k9.state.on_event(payload)
    '''
    queue.put(payload)
    print(str(payload),"put on queue by motor state machine")

try:
    queue = Queue()
    client = mqtt.Client("k9-motor")
    client.connect("localhost")
    client.on_message = mqtt_callback # attach function to callback
    client.subscribe("k9/events/motor", qos=2)
    # self.client.subscribe("/ble/advertise/watch/m")
    client.loop_start()
    print("MQTT subscription interface active")
    print("Creating K9 Motor State Machine instance")
    k9 = K9MotorSM()
except KeyboardInterrupt:
    logo.stop()
    client.loop_stop()
    "Motors stopped and MQTT client stopped"
    sys.exit(0)