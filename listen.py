""" Listening node for K9

This program publishes what K9 hears to an MQTT
topic that can be subscribed to by other programs.

"""

import paho.mqtt.client as mqtt
from audio_tools import VADAudio # Voice activity detection
import deepspeech  # Mozilla STT
import numpy as np
from state import State # Base FSM State class
import sys
from eyes import Eyes # k9 led eyes
from back_lights import BackLights # k9 back lights

# k9 lights
k9eyes = Eyes()
k9lights = BackLights()

# mqtt connection details
broker = "localhost"
port = 1883
topic = "/ble/advertise/watch/m"

# callback function from publish
def on_publish(client,userdata,result):
    print("listen.py - data published \n")
    pass

client= mqtt.Client("k9-listen")    # create MQTT client
client.on_publish = on_publish      # assign function to callback
client.connect(broker,port)         # establish connection

# load deepspeech models for STT
model = deepspeech.Model("/home/pi/k9localstt/deepspeech-0.9.3-models.tflite")
model.enableExternalScorer("/home/pi/k9localstt/deepspeech-0.9.3-models.scorer")

# load voice activiity detection capability
vad_audio = VADAudio(aggressiveness=1,
device=None,
input_rate=16000,
file=None)
stream_context = model.createStream()

class Listening(State):
    '''
    The state where K9 is listening for an utterance; this will
    be sent via an MQTT message
    '''
    def __init__(self):
        super(Listening, self).__init__()
        k9eyes.set_level(0.01)
        k9lights.on()
        try:
            while True:
                client.loop(0.1) # listen for off instruction
                frames = vad_audio.vad_collector()
                for frame in frames:
                    if frame is not None:
                        stream_context.feedAudioContent(np.frombuffer(frame, np.int16))
                    else:
                        print("listen.py - stream finished")
                        command = stream_context.finishStream()
                        del stream_context
                        print("listen.py -",command)
                        if "listen" in command:
                            return NotListening()
                        if command != "":
                            command = "voice_command:" + command
                            vad_audio.destroy()
                            ret = client.publish("/ble/advertise/watch/m",command)
                        else:
                            stream_context = model.createStream()
        except KeyboardInterrupt:
            stream_context.finishStream()
            vad_audio.destroy()
            client.disconnect()
            print("listen.py stopped by user in listening state")
            sys.exit(0)

    def on_event(self, event):
        if 'listen_off' in event:
            return NotListening()
        return self

class NotListening(State):
    '''
    The child state where K9 is not listening for an utterance
    '''
    def __init__(self):
        super(NotListening, self).__init__()
        k9eyes.set_level(0.001)
        k9lights.off()
        try:
            while True:
                client.loop(0.1) # listen for on instruction
        except KeyboardInterrupt:
            print("listen.py stopped by user during not listening state")
            client.disconnect()
            sys.exit(0)

    def on_event(self, event):
        if 'listen_on' in event:
            return Listening()
        return self

# TODO - CREATE FSM