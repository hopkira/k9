#!/usr/bin/env python
# coding: utf-8
# Author: Richard Hopkins
# Date: 12 Novelner 2022
#
# This program run on a Pi Pico
# running MicroPython
#
from sys import stdin
from time import sleep

import uselect
from machine import Pin

# Serial USB reading by Ben Renninson
# https://github.com/GSGBen/pico-serial
buffered_input = []
input_line_this_tick = ""
TERMINATOR = "\n"
latest_input_line = ""

patterns = {
    "computer": [[]],
    "manual": [[]],
    "original": [[5],[6],[8],[1],[10],[9],[12],[7],[2],[3]],
    "colour": [[3,6,8,9],[2,5,12],[1,7,10]],
    "colourflow": [[3],[6],[8],[9],[2],[5],[12],[1],[7],[10]],
    "diagonal" : [[9],[6],[3],[10],[7],[4],[11],[8],[12],[5],[2],[1]],
    "two": [[5,3],[9,8],[2,7],[6,12],[1,11],[10,4]],
    "three": [[1,10,8],[9,2,11],[5,7,4],[6,3,12]],
    "four": [[1,10,7,4],[9,2,11,8],[5,6,3,12]],
    "six": [[1,9,6,3,11,8],[5,2,10,7,4,12]],
    "red": [[3,6,8,9]],
    "green": [[2,5,12]],
    "blue": [[1,7,10]],
    "yellow": [[4,11]],
    "spiral": [[7],[6],[5],[9],[10],[11],[12],[8],[4],[3],[2],[1]],
    "chase_v": [[1],[5],[9],[10],[6],[2],[3],[7],[11],[12],[8],[4]],
    "chase_h": [[1],[2],[3],[4],[8],[7],[6],[5],[9],[10],[11],[12]],
    "cols" : [[1,5,9],[2,6,10],[3,7,11],[4,8,12]],
    "rows" : [[1,2,3,4],[5,6,7,8],[9,10,11,12]],
    "centre": [[1,2,3,4,5,8,9,10,11,12],[6,7]],
    "cross": [[1,4,6,7,9,12],[2,3,5,8,10,11]],
    "on": [[1,2,3,4,5,6,7,8,9,10,11,12]],
    "off": [[]]
}

speeds = {
    "fastest": 50,
    "fast"   : 100,
    "normal" : 200,
    "slow"   : 400,
    "slowest": 800
}

# These are the pins used to control the lights
# they correspond 1:1 with the pins used to
# monitor the switches 
light_pin_labels = list(range(12))
light_pins = []
for pin in light_pin_labels:
    light_pins.append(Pin(pin, Pin.OUT))

# Switch debounce time
debounce_time = 10

# Empty list of switchh states
switch_states = []

# Create list of switch pins
#switch_labels = [12,13,14,15,16,17,18,19,20,21,22,26]
switch_labels = [15,14,13,12,19,18,17,16,26,22,21,20]
switches = []
for switch in switch_labels:
    switches.append(Pin(switch, Pin.IN, Pin.PULL_UP))

def read_serial_input():
    global buffered_input, input_line_this_tick, TERMINATOR
    select_result = uselect.select([stdin], [], [], 0)
    while select_result[0]:
        input_character = stdin.read(1)
        buffered_input.append(input_character)
        select_result = uselect.select([stdin], [], [], 0)
    if TERMINATOR in buffered_input:
        line_ending_index = buffered_input.index(TERMINATOR)
        input_line_this_tick = "".join(buffered_input[:line_ending_index])
        if line_ending_index < len(buffered_input):
            buffered_input = buffered_input[line_ending_index + 1 :]
        else:
            buffered_input = []
    else:
        input_line_this_tick = ""

# main loop
def main():
    '''
    Main loop that allows for the selection and driving of
    the selected pattern, including a manual pattern that
    reflects the status of the physical switches
    '''
    pattern = "manual"
    seq = patterns[pattern]
    seq_len = len(seq)
    phase = 0
    wait = 150
    while True:
        # monitor for pressing a switch
        # set the lights in accordance
        # with the pattern
        if pattern == "computer":
            pass
        elif pattern == "manual":
            debounced = debounced_switches()
            for num, switch in enumerate(debounced):
                light_pins[num].value(int(switch))
        else:
            # Follow the automated pattern
            # First, turn off all lights,
            for num, pin in enumerate(light_pins):
                light_pins[num].value(0)
            # then turn on all
            # lights in this phase
            for pin in seq[phase]:
                light_pins[pin-1].value(1)
            phase += 1 # now increment the phase
            # go back to phase zero if done
            if phase > seq_len -1: 
                phase = 0
            sleep(wait/1000)
        # check for instructions from Pi
        read_serial_input()
        if input_line_this_tick:
            latest_input_line = input_line_this_tick
            command = ""
            command = latest_input_line.strip()
            # if the command is a light
            # sequence then switch to that
            # one and reset phase
            if command in patterns:
                pattern = command
                seq = patterns[pattern]
                seq_len = len(seq)
                phase = 0
            # if the command is speed
            # related then change
            # wait time
            elif command in speeds:
                wait = int(speeds[command])
            elif "light" in command:
                pattern = "computer"
                #  expects command in the forma
                # "light num action" where num is 1 to 12
                # and action is on|off|toggle
                num, action = tuple(command.strip("light").split())
                num = int(num)
                if action == "toggle":
                    value = not(debounced_switches()[num-1])
                elif action == 'on':
                    value = 1
                elif action == 'off':
                    value = 0
                light_pins[num-1].value(int(value))

def debounced_switches():
    global switch_states, switches, debounce_time
    # Record the state of all switches as true or false
    switch_values=[]
    for switch in switches:
        switch_values.append(bool(switch.value()))
    # Append the latest state of all switches to
    # the state list
    switch_states.append(switch_values)
    # Trim the number of states to match
    # the debounce timer by popping off
    # the top of the list if needed
    if len(switch_states) > debounce_time:
        switch_states.pop(0)
    # Transpose the state by switch 2D array so that each
    # switch becomes a row with its own history.  Then 
    # logically AND the history of each switch
    # Switches with all True, will be True, every other
    # state (including any bounciness) will be False
    debounced = [all(row) for row in zip(*switch_states)]
    return debounced

main()