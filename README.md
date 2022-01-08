# k9localstt
Prototype of offline wakeword, STT and TTS for K9 robot



# Create and activate a virtualenv
virtualenv -p python3 $HOME/tmp/deepspeech-venv/
source $HOME/tmp/deepspeech-venv/bin/activate

# Install DeepSpeech
pip3 install deepspeech
sudo pip3 install pvporcupinedemo
pip3 install pyaudio

pip3 install webrtcvad
pip3 install halo

curl -LO https://github.com/mozilla/STT/releases/download/v0.7.1/deepspeech-0.7.1-models.tflite
curl -LO https://github.com/mozilla/STT/releases/download/v0.7.1/deepspeech-0.7.1-models.scorer

Research:

https://github.com/mozilla/DeepSpeech-examples/blob/r0.9/mic_vad_streaming/mic_vad_streaming.py

python3 vad_streaming.py -m deepspeech-0.7.1-models.tflite -s deepspeech-0.7.1-models.scorer

