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

class Voice():
    '''
    Simple client class so that K9 can speak 
    '''

    def __init__(self) -> None:
        self.client = mqtt.Client("k9-speech-client")
        self.client.connect("localhost")
        self.client.loop()
        
    def speak(self, speech:str) -> None:
        self.client.publish("k9/events/speech", payload = speech, qos = 2, retain = False)
        print("Voice published:",speech)