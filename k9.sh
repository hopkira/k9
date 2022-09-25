#!/bin/bash
./python3 k9_streaming_tts.py &
./start.sh depthAI k9_oak_pipe.py &
./start.sh depthAI lidar360.py &
./python3 k9_audio_sm.py &
