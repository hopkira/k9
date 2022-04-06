# -*- coding: utf-8 -*-
#
# K9's Short Term Memory using Redis
#
# authored by Richard Hopkins February 2022
#
# Licensed under The Unlicense, so free for public domain use
#
# This program provides K9 with a short term memory that can recall
# all internal messages from sensors, motors, browser commands etc.
# for the last 10 seconds.  It also enables this history of messages to
# be quickly retrieved on a per sensor basis

import json
import time
import redis

print("Short term memory loaded...")


class Memory():
    '''
    K9 short term memory

    Arg:
        record (bool): When true, all messages will be recorded and not forgotten after 10 seconds

    Described in full in this post
    https://k9-build.blogspot.com/2018/02/using-redis-to-create-robot-short-term.html?q=redis
    '''
    
    def __init__(self, record = False):
        self.rec = record
        print("Connecting to local redis host")
        self.r = redis.Redis(host='127.0.0.1',port=6379)
        if self.rec:
            print("Recording data permanently") # let the user know they are in sim mode
        self.storeState("left:speed",0.0)
        self.storeState("right:speed",0.0)
            
    def storeState(self, key:str, value:float) -> None:
        '''Stores the value of a received key and the time it was stored as well as preserving the previous value

        Args:
            key (str): Name of the key
            value (float): New value for the key 
        '''
        print("Called: ", key, value)
        old_value = self.r.get(str(key) + ":now")
        if not old_value:
            old_value = 0.0
        print("Old value: ", old_value)
        self.r.set(str(key) + ":old", old_value )
        old_value = self.r.get(str(key) + ":time:now")
        if not old_value:
            old_value = 0.0
        print("Old time value: ", old_value)
        self.r.set(str(key) + ":time:old", old_value)
        self.r.set(str(key) + ":now",str(value))
        self.r.set(str(key) + ":time:now",str(time.time()))

    def retrieveState(self, key:str) -> str:
        '''Retrieves the last version of a desired key

        Args:
            key (str): Name of the key
        '''

        return self.r.get(str(key) + ":now")

    def getMsgKey(self):
        '''Uses redis to create a unique message key by incrementing message_num
        '''

        msg_key = "message:"+str(self.r.incr("message_num",amount=1))
        return msg_key

    def storeSensorReading(self, name:str, reading:float, angle:float) -> None:
        '''Stores a sensor reading as a JSON string, compatible with other sensor readings

        Args:
            name (str): Name of the sensor
            reading (float): Distance measured by sensor
            angle (float): Angle measured by sensor
        '''
        reading = {
            "type":"sensor",
            "sensor": str(name),
            "distance": reading,
            "angle": angle
        }
        json_data = json.dumps(reading)
        # json_data = '{"type":"sensor","sensor":"'+str(name)+'","distance":"'+str(reading)+'","angle":"'+str(angle)+'"}'
        self.storeSensorMessage(json_data)

    def storeSensorMessage(self, json_data:str):
        '''Stores a JSON string formatted sensor reading message

        Arg:
            json_data (json): store a string that is in JSON format
        '''

        # Parse message into dictionary of name value pairs
        message = {}
        message = json.loads(json_data)
        # print(message)
        msg_key = self.getMsgKey()
        # Create a transactional pipeline to store new message, this will be closed
        # and committed by the pipe.execute() command
        pipe = self.r.pipeline(transaction=True)
        # Store the whole of the message as a hash value
        pipe.hmset(msg_key,message)
        # Expire all messages after 10 seconds unless in record mode
        if not self.rec :
            pipe.expire(msg_key,10)
        # For each of the message generating devices e.g. sensors, create a list
        # where the most recent element is at the left of the list
        pipe.lpush("sensor:" + message["sensor"],msg_key)
        # Ensure that the list for each device doesn't get any longer than 40 messages so
        # stuff will fall of the right hand end of the list
        if not self.rec :
            pipe.ltrim("sensor:" + message["sensor"],0,40)
        # Execute all of the above as part of a single transactional interaction with the
        # Redis server
        pipe.execute()

    def retrieveSensorMessage(self, sensor):
        '''Retrieves the last message stored for a sensor

        Arg:
            sensor (str): Name of the sensor
        ''' 
        
        msg_key=self.r.lrange(sensor, 0, 0)
        msg = self.r.hmget(msg_key)
        return msg

    def retrieveSensorReadings(self, sensor:str) -> list:
        '''Retrieves all the values stored for a sensor
        
        Arg:
            sensor (str): Name of sensor
        '''
        msgs = []
        msg_key_list = self.r.lrange(sensor, 0, -1)
        for key in msg_key_list:
            msgs.append(json.loads(self.r.hmget(key)))
        return msgs

    def retrieveLastSensorReading(self, sensor:str) -> str:
        '''Retrieves the last value stored for a sensor

        Arg:
            sensor (str): Name of the sensor
        '''
        
        message = json.loads(self.retrieveSensorMessage(sensor))
        return message
