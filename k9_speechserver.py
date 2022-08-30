import sys
from subprocess import Popen

from memory import Memory
from eyes import Eyes

mem = Memory()
eyes = Eyes()   

import paho.mqtt.client as mqtt
print("MQTT found...")
from queue import Queue
print("Queues forming...")

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

def speak(speech:str) -> None:
    '''
    Break speech up into clauses using | and speak each one with
    various pitches, volumes and distortions
    to make the voice more John Leeson like
    > will raise the pitch and amplitude
    < will lower it
    '''
    mem.storeState("speaking",True)
    store_eyes = eyes.get_level()
    eyes.on()
    print('Speech server:', speech)
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
    eyes.set_level(store_eyes)
    mem.storeState("speaking",False)

def mqtt_callback(client, userdata, message):
    """
    Enables K9 to receive an MQTT message and place it in a queue
    """
    payload = str(message.payload.decode("utf-8"))
    print("Server payload:", payload)
    queue.put(payload)

queue = Queue()
client = mqtt.Client("k9-speech-server")
client.connect("localhost")
client.on_message = mqtt_callback # attach function to callback
client.subscribe("k9/events/speech", qos=2)
# self.client.subscribe("/ble/advertise/watch/m")
client.loop_start()
print("Speech MQTT interface active")
try:
    while True:
        while not queue.empty():
            utterance = queue.get()
            if utterance is None:
                continue
            print("Voice server:", utterance)
            speak(utterance)
except KeyboardInterrupt:
    client.loop_stop()
    "K9 silenced and MQTT client stopped"
    sys.exit(0) 
