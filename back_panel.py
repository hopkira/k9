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
# python3 pyboard.py --device /dev/tty.usbmodem387A384631342 -f cp panel.py :main.py
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
import ast

class BackLights():
    def __init__(self) -> None:
        self.ser = serial.Serial(
            port='/dev/backpanel', # replace with your device name
            baudrate = 9600,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=1
            )

    def __write(self,text:str) -> None:
        print("Back panel:",text)
        self.ser.write(str.encode(text+"\n"))

    def __sw_light(self, cmd:str, lights:list) -> None:
        for light in lights:
            text = "light " + str(light) + " " + cmd
            self.__write(text)

    def cmd(self,text:str) -> None:
        self.__write(text)

    def on(self):
        self.__write("original")

    def off(self):
        self.__write("off")

    def turn_on(self, lights:list):
        self.__sw_light("on",lights)
    
    def turn_off(self, lights:list):
        self.__sw_light("off",lights)

    def toggle(self, lights:list):
        self.__sw_light("toggle",lights)

    def tv_on(self):
        self.__write("tvon")

    def tv_off(self):
        self.__write("tvoff")

    def get_switch_state(self) -> list:
        self.switch_state = []
        self.__write("switchstate")
        input = self.ser.readlines()
        print("I heard:" + str(input))
        lst = ast.literal_eval(input.decode('unicode_escape').strip()[1:])
        self.switch_state = [bool(x) for x in lst]
        print(str(self.switch_state))
        return self.switch_state
            