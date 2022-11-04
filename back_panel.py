#!/usr/bin/env python
# coding: utf-8
# Author: Richard Hopkins
# Date: 3 Novelner 2022
#
# This program drives the MicroPython
# back light controller; it is designed
# to be backwards compatible with
# back_lights.py
# 
# The program interacts with the panel.py
# program.  The panel.py program can be uploaded
# to the micropython device using:
#
# pyboard.py --device /dev/tty.usbmodem388D384731342 -f cp panel.py :main.py
import serial

class BackLights():
    def __init__(self) -> None:
        self.ser = serial.Serial(
            port='/dev/tty.usbmodem388D384731342',
            baudrate = 115200,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=10
            )

    def command(self,text:str) -> None:
        print("Back panel:",text)
        self.ser.write(str.encode(text+"\n"))

    def __write(self,text:str) -> None:
        print("Back panel:",text)
        self.ser.write(str.encode(text+"\n"))

    def on(self):
        self.level = 1
        self.__write("on")

    def off(self):
        self.level = 0
        self.__write("off")

'''
import pyboard

class BackLights():
    def __init__(self) -> None:
        self.level = 0
        self.pyb = pyboard.Pyboard('/dev/tty.usbmodem388D384731342')

    def __write(self, text:str) -> None:
        print("Back panel:",text)
        self.pyb.enter_raw_repl()
        print(self.pyb.exec(text))
        self.pyb.exit_raw_repl()

    def ledoff(self) -> None:
        self.__write("on")

    def flash(self) -> None:
        self.__write("off")

    def on(self):
        self.level = 1
        self.state()

    def off(self):
        self.level = 0
        self.state()

    def state(self):
        value = int(self.level * 65535)
        #pca.channels[1].duty_cycle = value

    def get_level(self):
        return self.level
'''