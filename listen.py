""" Listening class for K9

This program listens converts speech into text.

"""

#import paho.mqtt.client as mqtt
from audio_tools import VADAudio # Voice activity detection
import deepspeech  # Mozilla STT
import numpy as np

class Listen():

    def __init__(self, lights):
        # load deepspeech models for STT
        self.model = deepspeech.Model("/home/pi/k9/deepspeech-0.9.3-models.tflite")
        self.model.enableExternalScorer("/home/pi/k9/deepspeech-0.9.3-models.scorer")
        self.back_panel = lights

    def listen_for_command(self) -> str:
        # put back panel lights into override mode
        turn_on_lights = [2,5,9,12]
        switch = 11
        self.back_panel.cmd("computer")
        self.back_panel.turn_on(turn_on_lights)
        self.start_state = self.back_panel.get_switch_state()
        # load voice activiity detection capability
        self.vad_audio = VADAudio(aggressiveness=1,
            device=None,
            input_rate=16000,
            file=None)
        self.stream_context = self.model.createStream()
        try:
            while True:
                self.current_state = self.back_panel.get_switch_state()
                if self.start_state[switch] ^ self.current_state[switch]:
                    self.stream_context.finishStream()
                    del self.stream_context
                    self.vad_audio.destroy()
                    return "button_stop_listening"
                frames = self.vad_audio.vad_collector()
                for frame in frames:
                    if frame is not None:
                        self.stream_context.feedAudioContent(np.frombuffer(frame, np.int16))
                    else:
                        command = self.stream_context.finishStream()
                        del self.stream_context
                        if command != "":
                            self.vad_audio.destroy()
                            return command
                        else:
                            self.stream_context = self.model.createStream()
        except KeyboardInterrupt:
            self.stream_context.finishStream()
            self.vad_audio.destroy()