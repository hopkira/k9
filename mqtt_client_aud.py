#!/usr/bin/env python
# coding: utf-8
# Author: Richard Hopkins
# Date: 7 April 2022
#
import paho.mqtt.client as mqtt
import sys
import time

class K9MQTT:
    '''
    K9MQTT
    '''

    def __init__(self):
        ''' Initialise K9 in his waiting state. '''

        self.last_message = ""
        self.client = mqtt.Client("k9-audio")
        self.client.connect("localhost")
        self.client.on_message = self.mqtt_callback # attach function to callback
        self.client.subscribe("/ble/advertise/watch/m")
        self.client.subscribe("k9/events/audio", qos=2)

    def mqtt_callback(self,client, userdata, message):
        """
        Enables K9 to receive a message from an Epruino Watch via
        MQTT over Bluetooth (BLE) to place it into active or inactive States
        """

        payload = str(message.payload.decode("utf-8"))
        print(message.topic, payload)
        if payload != self.last_message:
            self.last_message = payload
            event = payload[3:-1].lower()
            print("Event: ",str(event))

try:
    # adding  comment
    print("Creating K9 instance")
    k9 = K9MQTT()
    k9.client.loop_start()
    print("MQTT loop started")
    while True:
        for msg_num in range(10):
            # k9.client.loop(0.1)
            message =  "Send to Motor Event " + str(msg_num)
            k9.client.publish("k9/events/motor", payload=message, qos=2, retain=False)
            print(message)
            time.sleep(1.0)
except KeyboardInterrupt:
    k9.client.loop_stop()
    print('Exiting K9 client.')
    sys.exit(0)