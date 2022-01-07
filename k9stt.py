import pvporcupine
from pvrecorder import PvRecorder
from secrets import * 
from datetime import datetime

try:
    porcupine = pvporcupine.create(
    access_key = ACCESS_KEY,
    keyword_paths=['/home/pi/k9localstt/canine_en_raspberry-pi_v2_0_0.ppn']
    )

    recorder = PvRecorder(device_index=-1, frame_length=porcupine.frame_length)
    recorder.start()

    print(f'Using device: {recorder.selected_device}')

    while True:
        pcm = recorder.read()
        result = porcupine.process(pcm)
        if result >= 0:
            print('[%s] Detected %s' % (str(datetime.now()), str(result)))
except KeyboardInterrupt:
    print('Stopping....')
finally:
    if porcupine is not None:
        porcupine.delete()
    if recorder is not None:
        recorder.delete()
