import pvporcupine
from state import State
from pvrecorder import PvRecorder
from secrets import * 
from datetime import datetime
from eyes import Eyes

# Start K9 dialogue states

class Waitforhotword(State):

    '''
    The child state where the k9 is waiting for the hotword
    '''
    def __init__(self):
        self.porcupine = pvporcupine.create(
            access_key = ACCESS_KEY,
            keyword_paths=['/home/pi/k9localstt/canine_en_raspberry-pi_v2_0_0.ppn']
        )   
        self.recorder = PvRecorder(device_index=-1, frame_length=self.porcupine.frame_length)
        self.recorder.start()
        print(f'Using device: {self.recorder.selected_device}')
        k9eyes.set_level(0.01)
        super(Waitforhotword, self).__init__()

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

# Start Dalek states
class Listening(State):

    '''
    The child state where K9 is now listening for an utterance
    '''
    def __init__(self):
        super(Listening, self).__init__()
        k9eyes.set_level(0.1)

    def run(self):
        pass

    def on_event(self, event):
        pass
        return self

class K9Assistant(object):
    def __init__(self):
        self.state = Waitforhotword()

    def run(self):
        self.state.run()

    def on_event(self, event):
        self.state = self.state.on_event(event) 

k9eyes = Eyes()
k9assistant = K9Assistant()

try:
    while True:
        k9assistant.run()
except KeyboardInterrupt:
    print("Assistant stopped")