# Client that leverages the CoquiTTS server
# Coqui server started with the command line (use full paths if not in the model directory)

# tts-server --model_path ./checkpoint_1020000.pth --config_path ./config.json --use_cuda yes

# imports libraries

import sys
import time
import requests

from subprocess import Popen
from urllib.parse import urlencode
from urllib.request import urlretrieve

from memory import Memory
from eyes import Eyes

mem = Memory()
eyes = Eyes()

import paho.mqtt.client as mqtt
print("MQTT found...")
from queue import Queue
print("Queues forming...")

def connected(timeout: float = 1.0) -> bool:
    try:
        requests.head("http://www.ibm.com/", timeout=timeout)
        return False # temporary change for testing (use local voice)
    except requests.ConnectionError:
        return False
    
def speak(speech:str) -> None:
    print('Speech server:', speech)
    if not connected():
        speak_local(speech)
    else:
        speak_coqui(speech)
    mem.storeState("speaking",0.0)

def speak_coqui(speech:str) -> None:
    '''
    Use local coqui speech server to render speech
    '''
    mem.storeState("speaking",1.0)
    store_eyes = eyes.get_level()
    eyes.on()
    print('Speech server:', speech)
    speak_proc = None
    coqui_tts = "http://ros2.local:5002/api/tts"
    params = {"text":speech}
    query = urlencode(params)
    coqui_tts = coqui_tts + "?" + query
    response = urlretrieve(coqui_tts, "/home/pi/k9/speech.wav")
    cmd = ['aplay','/home/pi/k9/speech.wav']
    speak_proc = Popen(cmd)
    Popen.wait(speak_proc)
    eyes.set_level(store_eyes)
    mem.storeState("speaking",0.0)
    return


def speak_local(speech:str) -> None:
    '''
    Fallback speech option.
    '''
    mem.storeState("speaking",1.0)
    store_eyes = eyes.get_level()
    speak_proc = None
    pitch = 99
    speed = 150
    amplitude = 50
    cmd = ['espeak','-v','en-rp',str(speech),'-p',str(pitch),'-s',str(speed),'-a',str(amplitude)]
    speak_proc = Popen(cmd)
    Popen.wait(speak_proc)
    eyes.set_level(store_eyes)
    mem.storeState("speaking",0.0)
    return
    
    
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
        time.sleep(0.2)
        while not queue.empty():
            speaking = True
            utterance = queue.get()
            if utterance is None:
                continue
            print("Voice server:", utterance)
            speak(utterance)
        
except KeyboardInterrupt:
    client.loop_stop()
    "K9 silenced and MQTT client stopped"
    sys.exit(0) 