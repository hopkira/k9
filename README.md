# K9 Robot Dog Software
## Featuring come, heel, chess playing and real time in character conversation.

Core repository for the 2022 version of the K9 robot dog software.

Major update to K9 in preparation for moving to ROS2.  Splits major programs down into smaller modules with Redis and MQTT acting as the integration point of the robot state (Redis acting as a shared black board and MQTT being used to provide pub/sub between modules).

## k9_audio_sm.py
Main behaviour controller for voice interactions. Impressive, in character, conversations using OpenAI GPT and local speech understanding using Mozilla DeepSpeech. Intent of conversations also determined using GPT3.  When the internet is unavailable, the robot will fall back to simple interactions based on simple commands.

<img
  src="K9 class diagram.drawio.png"
  alt="K9 Class Diagram"
  title="K9 Class Diagram"
  style="display: inline-block; margin: 0 auto; max-width: 300px">

Audio controller with voice recognition, finite state machine and offline wakeword.  Hotword detection is via Porcupine as the Hotword State within the program. Can issue MQTT messages that indicate state changes for the motor state machine.  The controller integrates the following Python modules:

| Python module | Description |
|---|---|
|back_lights.py|Controls back panel flashing lights; used to indicate when K9 is thinking|
|eyes.py|Controls K9's eye lights to indicate listening activity (off = not listening; low level = listening for hotword; mid level = listening for audio command; high level = speaking, unable to listen)|
|ears.py|Controls the LIDAR ears - supports various speeds and LIDAR modes to help avoid collisions|
|state.py|Simple finite state machine class to simplify the core program|
|listen.py|Enables offline speech to text recognition via Mozilla Deepspeech. Uses the audio_tools.py file to capture voice.|
|memory.py|Provides a high level interface to Redis to act as K9's short term memory, primarily used to share state and information between modules|
|k9gpt3conv.py|Interface to OpenAI's GPT3 to determine K9's audio responses and the intent of user commands|
|voice.py|The speech client that sends MQTT messagess to the speechserver so they can be vocalised|
|k9_lichess_bot.py|Chess module that enables him to create Lichess.com games and play chess|

## k9_speechserver.py
Provides speech to text capability that can be used by multiple modules on a FIFO basis via MQTT

## k9_oak_pipe
A complex Oak-lite sensor pipeline that is used to provide scanning functions from the Oak stereoscopic camea.  This includes the scanning functionality to support heeling, following and collision avoidance.  All data is simplified and stored in Redis for other modules to use:
  * Detect person at a distance (for heeling; recorded in Redis as 'person')
  * Follow a nearby obstacle (recorded in Redis as 'follow')
  * Oak-d-lite based point cloud (multiple points recorded as 'oak')

## lidar360.py
A simple sensor pipeline that translates raw information from the back panel lidar sensor into Redis point cloud inserts (recorded as 'back') for consumption by the Motor Controller.

## k9_motor_sm.py
Python Motor Controller with a finite state machine that listens for state change events from MQTT and retrieves information about the environment from Redis.  Supported states include the motors being under manual control, following someone, scanning for someone, turning and moving forward. Uses logo.py to precisely control motors and movement.

## Create and activate a virtualenv
Due to the large number of dependencies for these modules it is recommended that you create a Python 3 virtual environment and then use ``pip3 install -r requirements`` to install the required Python packages.
