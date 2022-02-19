import time
import serial

class K9Ears():

    def __init__(self) -> None:
        self.ser = serial.Serial(
            port='/dev/ears',
            baudrate = 115200,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=10
        )

    def write(self,text):
        self.ser.write(text+"()")

    def stop(self):
        self.write("stop")

    def scan(self):
        self.write("scan")

    def fast(self):
        self.write("fast")

    def think(self):
        self.write("think")