# k9localstt
Major update to K9 in preparation for moving to ROS2.  Splits major programs down into smaller modules with Redis and MQTT acting as the integration point of the robot state (Redis acting as a shared black board and MQTT being used to provide pub/sub between modules).
* **k9_audio_sm.py** - Audio controller with voice recognition, finite state machine and offline wakeword.  Can issue MQTT messages that indicate state changes for the motor state machine.  The controller integrates the following Python modules:
  * Back panel (back_lights.py)
  * Eye lights (eyes.py)
  * Ear control (ears.py)
  * Finite state machine (state.py)
  * Offline speech to text (Deepspeech)
  * Hotword detection (Porcupine)
  * Offline text to speech (k9tts.py)
  * Redis Short term memory (memory.py)
  * Wolfram QA or GPT3 (wolframqy.py or k9gpt3conv.py)
  * K9's speech client (voice.py)
* **k9_speechserver.py** - provides speech to text capability that can be used by multiple modules on a FIFO basis
* **k9_oak_pipe** - A complex Oak-lite sensor pipeline that is used to provide scanning functions from the Oak stereoscopic camea.  This includes the scanning functionality to support heeling, following and collision avoidance.  All data is simplified and stored in Redis for other modules to use:
  * Detect person at a distance (for heeling; recorded in Redis as 'person')
  * Follow a nearby obstacle (recorded in Redis as 'follow')
  * Oak-d-lite based point cloud (multiple points recorded as 'oak')
* **lidar360.py** - a simple sensor pipeline that translates raw information from the back panel lidar sensor into Redis point cloud inserts (recorded as 'back') for consumption by the Motor Controller.
* **k9_motor_sm.py** - Python Motor Controller with a finite state machine that listens for state change events from MQTT and retrieves information about the environment from Redis.  Supported states include the motors being under manual control, following someone, scanning for someone, turning and moving forward.


https://www.hackster.io/dmitrywat/offline-speech-recognition-on-raspberry-pi-4-with-respeaker-c537e7

# Create and activate a virtualenv

virtualenv -p python3 $HOME/tmp/deepspeech-venv/

source $HOME/tmp/deepspeech-venv/bin/activate

# Install DeepSpeech

pip3 install deepspeech

sudo pip3 install pvporcupinedemo

pip3 install pyaudio

pip3 install webrtcvad

pip3 install halo

Research:

https://github.com/mozilla/DeepSpeech-examples/blob/r0.9/mic_vad_streaming/mic_vad_streaming.py

python3 vad_streaming.py -m deepspeech-0.7.1-models.tflite -s deepspeech-0.7.1-models.scorer

curl -LO https://github.com/mozilla/STT/releases/download/v0.9.3/deepspeech-0.9.3-models.tflite

curl -LO https://github.com/mozilla/STT/releases/download/v0.9.3/deepspeech-0.9.3-models.scorer
