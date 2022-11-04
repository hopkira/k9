# K9 Robot Dog Software
## Featuring come, heel, chess playing and real time in character conversation.

Core repository for the 2022 version of the K9 robot dog software.  Designed to run on a 2GB or larger Raspberry Pi 4.

This repository contains a major update to K9 in preparation for moving the code base to ROS2.  It has split major programs down into smaller modules with Redis and MQTT acting as the integration point of the robot state (Redis acting as a shared black board and MQTT being used to provide pub/sub between modules).

## Starting and stopping
The various python programs that make up K9's run time can be started with
```console
./k9.sh
```
The script assumes you have Python virtual environments installed and have created a virtual environment called depthAI in line with the OAK-D installation instructions.

These programs can be stopped using: 
```console
pkill -f k9_
```

## Hardware Pre-requsites
This software is designed to work with the following hardware:
* Adafruit I2C PCA9685 Servo controller (for controlling lights and tail)
* Epsruino Pico connected via USB for LIDAR ears
* USB microphone
* RoboClaw PID motor controller controlling two motors with encoders
* OAK-D camera (either original or lite)

Most of the hardware access is via abstraction modules that can easily be repurposed leaving the core of the program (the audio and motor controllers) intact.

 Details on the hardware design of K9 are provided [here](https://k9-build.blogspot.com/p/this-post-provides-quick-tour-of-the.html).

## Cloud subscriptions
For full conversational capability, the software requires:
* an [IBM Cloud id](https://www.ibm.com/cloud) under the Lite (free) plan for speech generation;
* a free account with [PicoVoice](https://picovoice.ai/platform/porcupine/) to use the Porcupine hotword
* a GPT-3 account with [OpenAI](https://openai.com/api/) for responses and intents (this is not free once the initial credits have been used)

### Class diagram
The following picture describes the Python modules that make up K9 and the key relationships between the modules. Most calls between modules are local, direct Python calls, except those shown in green that are performed by MQTT.  Red arrows show persistent data sharing through Redis. Classes with a dark blue border are separate executable programs.
<img
  src="K9 class diagram.drawio.png"
  alt="K9 Class Diagram"
  title="K9 Class Diagram"
  style="display: inline-block; margin: 0 auto; max-width: 300px">

## k9_audio_sm.py
Main behaviour controller for voice interactions. Impressive, in character, conversations using OpenAI GPT and local speech understanding using Mozilla DeepSpeech. Intent of conversations also determined using GPT3.  When the internet is unavailable, the robot will fall back to simple interactions based on simple commands.

Audio controller with voice recognition, finite state machine and offline wakeword.  Hotword detection is via Porcupine as the Hotword State within the program. Can issue MQTT messages that indicate state changes for the motor state machine.  The controller integrates the following Python modules:

| Python module | Description |
|---|---|
|back_panel.py|Controls back panel flashing lights; used to indicate when K9 is thinking. The program talks to the panel.py MicroPython program that runs on a Pyboard Lite|
|eyes.py|Controls K9's eye lights to indicate listening activity (off = not listening; low level = listening for hotword; mid level = listening for audio command; high level = speaking, unable to listen)|
|ears.py|Controls the LIDAR ears - supports various speeds and LIDAR modes to help avoid collisions. Talks to the ears.js program running on an Espruino|
|state.py|Simple finite state machine class to simplify the core program|
|listen.py|Enables offline speech to text recognition via Mozilla Deepspeech. Uses the audio_tools.py file to capture voice.|
|memory.py|Provides a high level interface to Redis to act as K9's short term memory, primarily used to share state and information between modules|
|k9gpt3conv.py|Interface to OpenAI's GPT3 to determine K9's audio responses and the intent of user commands|
|voice.py|The speech client that sends MQTT messagess to the speechserver so they can be vocalised|
|k9_lichess_bot.py|Chess module that enables him to create Lichess.com games and play chess|

## k9_streaming_tts.py
Provides speech to text capability that can be used by multiple modules on a FIFO basis via MQTT.  Uses IBM Cloud TTS functionality over websockets when connected to the Internet.

## k9_oak_pipe.py
A complex Oak-lite sensor pipeline that is used to provide scanning functions from the Oak stereoscopic camea.  This includes the scanning functionality to support heeling, following and collision avoidance.  All data is simplified and stored in Redis for other modules to use:
  * Detect person at a distance (for heeling; recorded in Redis as 'person')
  * Follow a nearby obstacle (recorded in Redis as 'follow')
  * Oak-d-lite based point cloud (multiple points recorded as 'oak')

The program can be started standalone with the '-t' flag for testing purposes on a VNC/graphical terminal or native pi screen; this makes the program run an order of magnitude slower, but visualises each of the programs main functions  including:

 * An overhead view of the 73 degree forward looking point cloud (shown as a green line)
 * A false colour view of the depth camera output
 * A false colour view of the 5x8 forward point cloud which is used to determine how far ahead K9 can safely travel in a straight line
 * A full colour preview of the colour camera with:
   * bounding boxes for legs shown in red
   * bounding boxes for people in green
   * text indicating current frames per second
   * text indicating the safe distance K9 can move in a straight line

Requires a virtual environment to run, follow the DepthAI installation instructions (workon depthAI).

## k9_lidar360.py
A simple sensor pipeline that translates raw information from the back panel 360 LIDAR sensor into information about whether the robot can safely rotate and how far it can safely reverse.  This information is stored in Redis for other programs to use.  It uses CalcLidarData.py as the low level interface to the device.

## k9_motor_sm.py
Python Motor Controller with a finite state machine that listens for state change events from MQTT and retrieves information about the environment from Redis.  Supported states include the motors being under manual control, following someone, scanning for someone, turning and moving forward. Uses logo.py to precisely control motors and movement.


## Create and activate a virtualenv
Due to the large number of dependencies for these modules it is recommended that you create a Python 3 virtual environment called ```depthAI``` following the OAK-D instructions and then use ``pip3 install -r requirements`` to install the required Python packages.
