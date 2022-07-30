# k9localstt
Major update to K9 in preparation for moving to ROS2.  Splits major programs down into smaller modules with Redis acting as the integration point of the robot state.
* Finite state machine with offline wakeword that integrates the following Python modules:
  * Back panel
  * Eye lights
  * Ear control
  * Offline speech to text
  * Offline text to speech
  * Short term memory (Redis)
  * Wolfram QA or GPT3
* Oak-lite pipeline also integrated into Redis:
  * Detect person at a distance
  * Follow a nearby obstacle
  * Oak-d-lite based point cloud

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
