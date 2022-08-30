# k9localstt
Major update to K9 in preparation for moving to ROS2.  Splits major programs down into smaller modules with Redis and MQTT acting as the integration point of the robot state (Redis acting as a shared black board and MQTT being used to provide pub/sub between modules).

##k9_audio_sm.py
Audio controller with voice recognition, finite state machine and offline wakeword.  Hotword detection is via Porcupine as State within the k9_audio_sm.py program. Can issue MQTT messages that indicate state changes for the motor state machine.  The controller integrates the following Python modules:

| Program | Description |
|---|---|
|back_lights.py|Back panel flashing lights|
|eyes.py|Eye lights to indicate K9's activity (low=listening for hotword; mid=listening for command; high=speaking|
|ears.py|Ear control - various speeds and LIDAR modes to avoid collisions|
|state.py|Finite state machine to simplify the core program|
|listen.py|K9 audio module incorporating offline speech to text via Mozilla Deepspeech|
|memory.py|Redis Short term memory, primarily used to share state and information between modules|
|k9gpt3conv.py|Wolfram QA or GPT3 to determine K9's response and the intent of user commands|
|voice.py|K9's speech client which sends MQTT messagess tot he speechserver|
|k9_lichess_bot.py|Chess module that enables him to play chess via Lichess.com|

##k9_speechserver.py
Provides speech to text capability that can be used by multiple modules on a FIFO basis via MQTT

##k9_oak_pipe
A complex Oak-lite sensor pipeline that is used to provide scanning functions from the Oak stereoscopic camea.  This includes the scanning functionality to support heeling, following and collision avoidance.  All data is simplified and stored in Redis for other modules to use:
  * Detect person at a distance (for heeling; recorded in Redis as 'person')
  * Follow a nearby obstacle (recorded in Redis as 'follow')
  * Oak-d-lite based point cloud (multiple points recorded as 'oak')

##lidar360.py
A simple sensor pipeline that translates raw information from the back panel lidar sensor into Redis point cloud inserts (recorded as 'back') for consumption by the Motor Controller.

##k9_motor_sm.py
Python Motor Controller with a finite state machine that listens for state change events from MQTT and retrieves information about the environment from Redis.  Supported states include the motors being under manual control, following someone, scanning for someone, turning and moving forward.

## Create and activate a virtualenv
Due to the large number of dependencies for these modules it is recommended that you create a Python 3 virtual environment and then use ``pip3 install -r requirements`` to install the required Python packages.
