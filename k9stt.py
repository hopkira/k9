import pvporcupine
import deepspeech
import pyaudio
from audio_tools import VADAudio
from state import State
from pvrecorder import PvRecorder
from secrets import * 
from datetime import datetime
from eyes import Eyes
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
        k9eyes.set_level(0.01)

    def run(self):
        pcm = self.recorder.read()
        result = self.porcupine.process(pcm)
        if result >= 0:
            print('Detected hotword')
            k9assistant.on_event('hotword_detected')

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
        k9eyes.set_level(0.1)
        print("Listening: init complete")

    def run(self):
        self.vad_audio = VADAudio(aggressiveness=1,
                device=None,
                input_rate=16000,
                file=None)
        self.stream_context = k9assistant.model.createStream()
        self.frames = self.vad_audio.vad_collector()
        for frame in self.frames:
            if frame is not None:
                self.stream_context.feedAudioContent(np.frombuffer(frame, np.int16))
                print(".")
            else:
                print("Stream finished")
                text = self.stream_context.finishStream()
                self.vad_audio.destroy()
                if 'stop listening' in text:
                    k9assistant.on_event('stop_listening')
                if text != "":
                    print("Listen.run() - I heard:",text)
                    k9assistant.command = text
                    k9assistant.on_event('command_received')

    def on_event(self, event):
        if event == 'stop_listening':
            return Waitforhotword()
        if event == 'command_received':
            return Responding()
        if event == 'try_again':
            return Listening()
        return self

class Responding():

    '''
    The child state where K9 processes a response to the text
    '''
    def __init__(self):
        super(Responding, self).__init__()
        k9eyes.set_level(0.5)

    def run(self):
        # say something
        # lower eye lights
        response = "Responding.run() - I heard " + k9assistant.command
        speak(response)
        k9assistant.on_event('responded')

    def on_event(self, event):
        if event == 'responded':
            return Listening()
        return self


# Define FSM
class K9Assistant(object):
    def __init__(self):
        self.model = deepspeech.Model("/home/pi/k9localstt/deepspeech-0.7.1-models.tflite")
        self.model.enableExternalScorer("/home/pi/k9localstt/deepspeech-0.7.1-models.scorer")
        speak("K9 initialized")
        self.state = Waitforhotword()

    def run(self):
        self.state.run()

    def on_event(self, event):
        self.state = self.state.on_event(event)
        print("Event:", event)

k9eyes = Eyes()
k9assistant = K9Assistant()

try:
    while True:
        k9assistant.run()
except KeyboardInterrupt:
    speak("K9 shutting down")