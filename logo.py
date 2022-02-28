# -*- coding: utf-8 -*-
#
# K9's Movement Subsystem - Autonomous Motor Driver
#
# authored by Richard Hopkins March 2021
#
# Licensed under The Unlicense, so free for public domain use
#
# This program provides K9 with a stack of instructions for his movement

import time
import math
import sys
import argparse

sys.path.append('/home/pi/k9-chess-angular/python')

sim = False

# Wheel circumference is 0.436m, with 200 clicks per turn
# Each click is 0.002179m (assumes each wheel is 0.139m)
CLICK2METRES = 0.002179  # converts clicks to metres
WALKINGSPEED = 1.4  # top speed of robot in metres per second
TOPSPEED = int(WALKINGSPEED/CLICK2METRES)  # calculate and store max velocity
ACCELERATION = int(TOPSPEED/5)  # accelerate to top speed in 5s
HALF_WHEEL_GAP = 0.1011
TURNING_CIRCLE = 2*math.pi*HALF_WHEEL_GAP/CLICK2METRES  # clicks in a full spin
#print("Turning circle:" + str(TURNING_CIRCLE))
M1_QPPS = 1987   # max speed of wheel in clicks per second
M2_QPPS = 1837
M1_P = 10.644  # Proportional element of feedback for PID controller
M2_P = 9.768
M1_I = 2.206  # Integral element of feedback for PID controller
M2_I = 2.294
M1_D = 0.0  # Derived element of feedback for PID controller
M2_D = 0.0

TARGET_POS_X = 1.0 # desired x stopping point from wheel centre
TARGET_POS_Y = 0.0 # desired y stopping point from wheel centre

CAM_POS_X = 0.0 # x position of camera from between wheel centre
CAM_POS_Y = 0.0 # y position of camera from between wheel centre

def main():
    global sim
    parser = argparse.ArgumentParser(description='Moves robot using logo commands.')
    parser.add_argument('command',
                        choices=['arc','fd','bk','lt','rt','stop'],
                        help='movement command')
    parser.add_argument('parameter',
                        type=float,
                        default=0.0,
                        nargs='?',
                        help='distance in metres or angle in radians')
    parser.add_argument('radius',
                        type=float,
                        default=0.0,
                        nargs='?',
                        help='radius of arc in metres (arc  only)')
    parser.add_argument('-t', '--test',
                        action='store_true',
                        help='execute in simulation mode')
    args = parser.parse_args()
    sim = args.test
    verb = args.command
    object1 = args.parameter
    object2 = args.radius
    if sim:
        print("Test mode active")
    else:
        init_rc()
    if (verb == "arc"):
        globals()[verb](object1, object2)
    else:
        globals()[verb](object1)


def motor_speed(m1_speed, m2_speed):
    ''' Make robot move based on joystick
    '''
    factor = min(M1_QPPS, M2_QPPS)
    m1_click = int(m1_speed * factor)
    m2_click = int(m2_speed * factor)
    rc.SpeedAccelM1M2(address=rc_address,
                        accel=ACCELERATION,
                        speed1=m1_click,
                        speed2=m2_click)


def calc_destination(x_pos, y_pos):
    ''' Calculate destination relative to robot
    '''
    ret_x = x_pos + CAM_POS_X - TARGET_POS_X
    ret_y = y_pos + CAM_POS_Y - TARGET_POS_Y
    return ret_x, ret_y

def calc_circle_arc(x_pos, y_pos):
    ''' Calculate a circle arc based on an target position
    '''
    # following calculation only works for a 90 degree or less field of view
    if x_pos == 0:
        raise ValueError('Cannot calculate circle arc of infinite radius')
    radius = (x_pos**2 + y_pos**2) / (2* x_pos)
    extent = math.asin(y_pos/radius)
    return radius, extent

def stop():
    '''Lock motors to stop motion
    '''
    global rc
    # print("Stopping")
    if not sim:
        rc.SpeedM1M2(address=rc_address, m1=0, m2=0)
        #rc.SpeedAccelDistanceM1M2(address=rc_address,
        #                          accel=int(ACCELERATION),
        #                          speed1=0,
        #                          distance1=0,
        #                          speed2=0,
        #                          distance2=0,
        #                          buffer=int(1))
    # print("Stop done")

def get_speed():
    ''' Returns speeds of motors
    '''
    global rc
    m1_speed = rc.ReadSpeedM1(rc_address)
    m2_speed = rc.ReadSpeedM2(rc_address)
    return m1_speed, m2_speed

def motors_moving():
    ''' Detects that motors are moving
    '''
    m1_speed, m2_speed = get_speed()
    return ((m1_speed[1] != 0) or (m2_speed[1] != 0))

def buffer_full():
    ''' Detects if moves have finished
    '''
    global rc
    buffers = rc.ReadBuffers(rc_address)
    return ((buffers[1] != 0x80) or (buffers[2] != 0x80))

def finished_move():
    ''' Detects that buffer is empty and motors are at rest
    '''
    return not(motors_moving() or buffer_full())

def calc_turn_modifier(radius):
    '''Calculates a velocity modifier; based on the radius
    of the turn.  As the radius tends to zero (i.e. spinning on the spot),
    then modifier will reduce velocity to 10% of normal.
    As the radius increases, the allowed maximum speed will increase.

    Arguments:
    radius -- the radius of the turn being asked for in metres
    '''
    radius = abs(radius)
    turn_modifier = 1 - (0.9/(radius+1))
    print("logo: calc_turn_modifier: " + str(turn_modifier))
    return turn_modifier

def calc_click_vel(clicks, turn_mod):
    '''Calculates target velocity for motors

    Arguments:
    clicks -- a signed click distance
    turn_mod -- a modifier based on radius of turn

    '''
    sign_modifier = 1.0
    if (clicks < 0.0):
        sign_modifier = -1.0
    click_vel = math.sqrt(abs(float(2.0*clicks*ACCELERATION*turn_mod)))
    if (click_vel > TOPSPEED*turn_mod):
        click_vel = TOPSPEED*turn_mod
    if (click_vel < 1.0):
        click_vel = 1.0
    print("logo: calc_click_vel: " + str(click_vel*sign_modifier))
    return click_vel*sign_modifier

def calc_accel(velocity, distance):
    '''Calculates desired constant acceleration
    
    Arguments:
    velocity -- the desired change in velocity
    distance -- the distance to change the velocity over
    '''
    accel = int(abs((velocity**2.0)/(2.0*distance)))
    return accel

def forward(distance):
    '''Moves K9 forward by 'distance' metres

    Arguments:
    distance -- the distance to move in metres
    '''
    global rc
    clicks = int(round(distance/CLICK2METRES))
    click_vel = calc_click_vel(clicks=clicks, turn_mod=1)
    accel = calc_accel(click_vel, clicks/2.0)
    print("logo fd: clicks: " + str(clicks) + " velocity: " + str(click_vel))
    if not sim:                       
        rc.SpeedAccelDistanceM1M2(address=rc_address,
                                  accel=accel,
                                  speed1=int(round(click_vel)),
                                  distance1=int(abs(clicks/2.0)),
                                  speed2=int(round(click_vel)),
                                  distance2=int(abs(clicks/2.0)),
                                  buffer=1)
        rc.SpeedAccelDistanceM1M2(address=rc_address,
                                  accel=accel,
                                  speed1=0,
                                  distance1=int(abs(clicks/2.0)),
                                  speed2=0,
                                  distance2=int(abs(clicks/2.0)),
                                  buffer=0)

fd = fwd = forwards = forward

def backward(distance):
    '''Moves K9 backward by 'distance' metres
    '''
    forward(-1*distance)

back = bk = backwards = backward

def left(angle, fast = False):
    '''Spins K9 by 'angle' radians
    '''
    global rc
    fraction = angle / ( 2 * math.pi )
    clicks = TURNING_CIRCLE * fraction
    if not fast:
        turn_modifier = calc_turn_modifier(radius = 0)
    else:
        turn_modifier = 1.0
    click_vel = calc_click_vel(clicks=clicks, turn_mod=turn_modifier)
    if not fast:
        accel = int(abs(click_vel * click_vel / ( 2.0 * clicks / 2.0)))
    else:
        accel = ACCELERATION
    if not sim:
        rc.SpeedAccelDistanceM1M2(address=rc_address,
                                  accel=accel,
                                  speed1=int(round(-click_vel)),
                                  distance1=abs(int(round(clicks/2.0))),
                                  speed2=int(round(click_vel)),
                                  distance2=abs(int(round(clicks/2.0))),
                                  buffer=int(1))
        rc.SpeedAccelDistanceM1M2(address=rc_address,
                                  accel=accel,
                                  speed1=int(0),
                                  distance1=abs(int(round(clicks/2.0))),
                                  speed2=int(0),
                                  distance2=abs(int(round(clicks/2.0))),
                                  buffer=int(0))
    print("logo lt: speed=" + str(click_vel) + " distance=" + str(clicks) + "\n")

lt = left

def right(angle, fast=False):
    '''Moves K9 right by 'angle' radians
    '''
    left( -1 * angle, fast = fast)

rt = right

def arc(radius, extent):
    '''Moves K9 in a circle or arc

    Arguments:
    radius -- radius in metres
    extent -- signed size of arc in radians e.g. -3.141 will move K9 in a
              a 180 semi-circle to the right

    '''
    global rc
    if extent > 0.0:
        distance1 = int(abs(extent * (radius + HALF_WHEEL_GAP) / CLICK2METRES))
        distance2 = int(abs(extent * (radius - HALF_WHEEL_GAP) / CLICK2METRES))
    else:
        distance1 = int(abs(extent * (radius - HALF_WHEEL_GAP) / CLICK2METRES))
        distance2 = int(abs(extent * (radius + HALF_WHEEL_GAP) / CLICK2METRES))
    turn_mod = calc_turn_modifier(radius)
    click_vel1 = calc_click_vel(clicks=distance1, turn_mod=turn_mod)
    click_vel2 = calc_click_vel(clicks=distance2, turn_mod=turn_mod)
    accel1 = int(abs(click_vel1 * click_vel1 / ( 2.0 * distance1 / 2.0)))
    accel2 = int(abs(click_vel2 * click_vel2 / ( 2.0 * distance2 / 2.0)))
    accel = max(accel1,accel2)
    if not sim:
        rc.SpeedAccelDistanceM1M2(address=rc_address,
                                    accel=accel,
                                    speed1=int(round(click_vel1)),
                                    distance1=int(round(distance1/2.0)),
                                    speed2=int(round(click_vel2)),
                                    distance2=int(round(distance2/2.0)),
                                    buffer=int(1))
        rc.SpeedAccelDistanceM1M2(address=rc_address,
                                    accel=accel,
                                    speed1=int(0),
                                    distance1=int(round(distance1/2.0)),
                                    speed2=int(0),
                                    distance2=int(round(distance2/2.0)),
                                    buffer=int(0))
    print("logo arc: m1 speed=" + str(click_vel1) + " distance=" + str(distance1))
    print("logo arc: m2 speed=" + str(click_vel2) + " distance=" + str(distance2) + "\n")

circle = arc

def init_rc():
    global rc
    global rc_address
    #  Initialise the roboclaw motorcontroller
    print("logo: initialising roboclaw driver...")
    from roboclaw_3 import Roboclaw
    rc_address = 0x80
    rc = Roboclaw("/dev/roboclaw", 115200)
    rc.Open()
    # Get roboclaw version to test if is attached
    version = rc.ReadVersion(rc_address)
    if version[0] is False:
        print("logo init: roboclaw get version failed")
        sys.exit()
    else:
        print("logo init:",repr(version[1]))

    # Set motor controller variables to those required by K9
    rc.SetM1VelocityPID(rc_address, M1_P, M1_I, M1_D, M1_QPPS)
    rc.SetM2VelocityPID(rc_address, M2_P, M2_I, M2_D, M2_QPPS)
    rc.SetMainVoltages(rc_address,240,292) # 24V min, 29.2V max
    rc.SetPinFunctions(rc_address,2,0,0)
    # Zero the motor encoders
    rc.ResetEncoders(rc_address)

    # Print Motor PID Settings
    m1pid = rc.ReadM1VelocityPID(rc_address)
    m2pid = rc.ReadM2VelocityPID(rc_address)
    print("logo init: m1 p: " + str(m1pid[1]) + ", i:" + str(m1pid[2]) + ", d:" + str(m1pid[3]))
    print("m2 p: " + str(m2pid[1]) + ", i:" + str(m2pid[2]) + ", d:" + str(m2pid[3]))
    # Print Min and Max Main Battery Settings
    minmaxv = rc.ReadMinMaxMainVoltages(rc_address) # get min max volts
    print ("logo init: min main battery: " + str(int(minmaxv[1])/10.0) + "V")
    print ("logo init: max main battery: " + str(int(minmaxv[2])/10.0) + "V")
    # Print S3, S4 and S5 Modes
    S3mode=['Default','E-Stop (latching)','E-Stop','Voltage Clamp','Undefined']
    S4mode=['Disabled','E-Stop (latching)','E-Stop','Voltage Clamp','M1 Home']
    S5mode=['Disabled','E-Stop (latching)','E-Stop','Voltage Clamp','M2 Home']
    pinfunc = rc.ReadPinFunctions(rc_address)
    print ("logo init: s3 pin: " + S3mode[pinfunc[1]])
    print ("logo init: s4 pin: " + S4mode[pinfunc[2]])
    print ("logo init: s5 pin: " + S5mode[pinfunc[3]])
    print("logo init: roboclaw motor controller initialised...")

# if executed from the command line then execute arguments as functions
if __name__ == '__main__':
    main()
else:
    init_rc()
