import time
from back_panel import BackLights
from  voice import Voice
bl = BackLights()
k9voice =  Voice()

modes = ["original","colour","colourflow","diagnonal","two","three","four","six","red","green","blue","rows","on","off"]
for mode in modes:
    bl.cmd(mode)
    k9voice.speak(mode)
    time.sleep(5.0) 