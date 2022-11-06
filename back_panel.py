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
# python3 pyboard.py --device /dev/tty.usbmodem388D384731342 -f cp panel.py :main.py
#
# Light schemes:
#   original
#   colour
#   diagonal
#   two
#   three
#   four
#   six
#   red
#   green
#   blue
#   spiral
#   chase_v
#   chase_h
#   cols
#   rows
#   on
#   off
#
# Speeds (with ms delay)
#    fastest: 50
#    fast   : 100
#    normal : 200
#    slow   : 400
#    slowest: 800
#
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

    def __write(self,text:str) -> None:
        print("Back panel:",text)
        self.ser.write(str.encode(text+"\n"))

    def cmd(self,text:str) -> None:
        self.__write(text)

    def on(self):
        self.__write("original")

    def off(self):
        self.__write("off")