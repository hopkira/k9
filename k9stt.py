import pvporcupine
import deepspeech
import pyaudio
from audio_tools import VADAudio
from state import State
from pvrecorder import PvRecorder
from secrets import * 
from datetime import datetime
from eyes import Eyes
from back_lights import BackLights
import numpy as np
from k9tts import speak

# Define K9 States   

class Waitforhotword(State):

    '''
    The child state where the k9 is waiting for the hotword
    '''
    def __init__(self):
        super(Waitforhotword, self).__init__()
        self.porcupine = pvporcupine.create(
            access_key = ACCESS_KEY,
            keyword_paths=['/home/pi/k9localstt/canine_en_raspberry-pi_v2_0_0.ppn']
        )   
        self.recorder = PvRecorder(device_index=-1, frame_length=self.porcupine.frame_length)
        self.recorder.start()
        print(f'Using device: {self.recorder.selected_device}')
        k9eyes.set_level(0.001)
        while True:
            pcm = self.recorder.read()
            result = self.porcupine.process(pcm)
            if result >= 0:
                print('Detected hotword')
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
        self.vad_audio = VADAudio(aggressiveness=1,
        device=None,
        input_rate=16000,
        file=None)
        self.stream_context = model.createStream()
        print("Listening: init complete")
        k9eyes.set_level(0.01)
        while True:
            self.frames = self.vad_audio.vad_collector()
            for frame in self.frames:
                if frame is not None:
                    self.stream_context.feedAudioContent(np.frombuffer(frame, np.int16))
                else:
                    print("Stream finished")
                    global command
                    command = self.stream_context.finishStream()
                    del self.stream_context
                    print("Listen.run() - I heard:",command)
                    if command != "":
                        self.vad_audio.destroy()
                        if 'stop listening' in command:
                            self.on_event('stop_listening')
                            espeak("Stopping listening")
                        else:
                            self.on_event('command_received')
                    else:
                        self.stream_context = model.createStream()

    def on_event(self, event):
        if event == 'stop_listening':
            return Waitforhotword()
        if event == 'command_received':
            return Responding()
        return self

class Responding(State):

    '''
    The child state where K9 processes a response to the text
    '''
    def __init__(self):
        print("Responding.init() - started")
        super(Responding, self).__init__()
        k9eyes.set_level(0.5)
        response = "I heard you say" + command
        print(response)
        speak(response)
        self.on_event('responded')

    def on_event(self, event):
        if event == 'responded':
            return Listening()
        return self

model = deepspeech.Model("/home/pi/k9localstt/deepspeech-0.7.1-models.tflite")
model.enableExternalScorer("/home/pi/k9localstt/deepspeech-0.7.1-models.scorer")
command = ""

# Define FSM
class K9Assistant(object):
    def __init__(self):
        k9lights.on()
        speak("Entering listen mode")
        self.state = Waitforhotword()

    def on_event(self, event):
        self.state = self.state.on_event(event)
        print("Event:", event)

k9eyes = Eyes()
k9lights = BackLights()

try:
    k9assistant = K9Assistant()
except KeyboardInterrupt:
    speak("K9 listen module stopped")
    k9lights.off()
    k9eyes.set_level(0)