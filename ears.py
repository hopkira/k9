import time
from urllib.parse import ParseResultBytes
import serial
import json
import math
from memory import Memory


class K9Ears():
    """Class that communicates with the Espruino controlling K9's LIDAR ears"""

    def __init__(self) -> None:
        self.ser = serial.Serial(
            port='/dev/ears',
            baudrate = 115200,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=10
            )
        self.mem = Memory()

    def __write(self,text):
        self.ser.write(str.encode(text+"()\n"))

    def stop(self):
        self.__write("stop")

    def scan(self):
        self.__write("scan")

    def fast(self):
        self.__write("fast")

    def think(self):
        self.__write("think")
    
    def rotate_scan(self):
        '''
        Performs an up to four second ear scan to
        detects if there is an obstacle to the side of K9's head
        that might collide with the robot as it rotates
        '''
        # define size of rectangle that could indicate a
        # potential collision
        safe_x = 0.3
        safe_y = 0.6
        detected = False
        # start ears moving and scanning
        self.__write("fast")
        end_scan = time.time() + 4 # time to end scan
        #
        # now loop for up to four seconds and listen
        # for message; stop looping if a potential
        # collision is detected
        #
        while time.time() < end_scan and not detected:
            # receive and decode a json string messsage
            # from the Espruino
            json_reading = self.ser.readline().decode("ascii")
            reading = json.loads(json_reading)
            dist = reading['distance']
            angle = reading['angle']
            x = math.abs(dist * math.cos(angle))
            y = math.abs(dist * math.sin(angle))
            # check whether reading indicates a potential
            # rotation problem
            if x <= safe_x and y <= safe_y:
                detected = True
        # stop the ears moving
        self.__write("stop")
        #
        # if a potential collisison was detected then
        # store that in K9's shared short term memory
        #
        if detected:
            distance = safe_x - dist
            self.mem.storeState("rotate", distance)