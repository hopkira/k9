# -*- coding: utf-8 -*-
#
# K9's Voice client
#
# authored by Richard Hopkins August 2023
#
# Licensed under The Unlicense, so free for public domain use
#
# This program interacts with the k9_speechserver.py program
# to give K9 a voice 

import paho.mqtt.client as mqtt
import time

class Voice():
    '''
    Simple client class so that K9 can speak 
    '''

    def __init__(self) -> None:
        self.client = mqtt.Client("k9-speech-client")
        self.client.connect(host = "localhost", port = 1883)
        self.client.on_publish = self.on_publish  
        self.client.loop_start()

    def speak(self, speech:str) -> None:
        print("Speech:",speech)
        self.client.publish(topic="k9/events/speech", payload=speech, qos = 2, retain = False)
        return

    def on_publish(self, client, userdata, mid):
        pass

v = Voice()

incr =  0

while True:
    v.speak("This is a soak test",incr)
    incr+=1
    time.sleep(5.0)