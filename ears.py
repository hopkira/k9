import string
import time
#from urllib.parse import ParseResultBytes
import serial
import json
import math
from memory import Memory


class Ears():
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
        self.following = False

    def __write(self,text:string) -> None:
        print("Ears:",text)
        self.ser.write(str.encode(text+"()\n"))

    def stop(self) -> None:
        self.following = False
        self.__write("stop")

    def scan(self) -> None:
        self.following = False
        self.__write("scan")

    def fast(self) -> None:
        self.following = False
        self.__write("fast")

    def think(self) -> None :
        self.following = False
        self.__write("think")
    
    def follow_read(self) -> float:
        if self.following is False:
            self.__write("follow")
            self.following = True
        json_reading = self.ser.readline().decode("ascii")
        reading = json.loads(json_reading)
        dist = reading['distance']
        return dist

    def safe_rotate(self) -> bool:
        '''
        Performs an up to four second ear scan to
        detects if there is an obstacle to the side of K9's head
        that might collide with the robot as it rotates
        '''
        # define size of rectangle that could indicate a
        # potential collision
        safe_x = 0.3
        safe_y = 0.6
        duration = 4
        detected = False
        # start ears moving and scanning
        self.__write("fast")
        end_scan = time.time() + duration # time to end scan
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
        return not detected