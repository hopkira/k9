""" Listening class for K9

This program listens converts speech into text.

"""

import paho.mqtt.client as mqtt
from audio_tools import VADAudio # Voice activity detection
import deepspeech  # Mozilla STT
import numpy as np

class Listen():

    def __init__(self):
        # load deepspeech models for STT
        self.model = deepspeech.Model("/home/pi/k9localstt/deepspeech-0.9.3-models.tflite")
        self.model.enableExternalScorer("/home/pi/k9localstt/deepspeech-0.9.3-models.scorer")
        # load voice activiity detection capability
        self.vad_audio = VADAudio(aggressiveness=1,
            device=None,
            input_rate=16000,
            file=None)

    def listen_for_command(self) -> str:
        stream_context = self.model.createStream()
        try:
            while True:
                frames = self.vad_audio.vad_collector()
                for frame in frames:
                    if frame is not None:
                        stream_context.feedAudioContent(np.frombuffer(frame, np.int16))
                    else:
                        command = stream_context.finishStream()
                        del stream_context
                        if command != "":
                            return command
                        else:
                            stream_context = self.model.createStream()
        except KeyboardInterrupt:
            stream_context.finishStream()
            self.vad_audio.destroy()