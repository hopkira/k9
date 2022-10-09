#!/bin/bash
python3 /home/pi/k9/k9_streaming_tts.py & # speech server
./start.sh depthAI k9_oak_pipe.py & # 3D camera pipeline
./start.sh depthAI k9_lidar360.py & # Rear LIDAR collision detect
python3 /home/pi/k9/k9_audio_sm.py & # Conversation state machine
python3 /home/pi/k9/k9_motor_sm.py & # Motor controller state machine
