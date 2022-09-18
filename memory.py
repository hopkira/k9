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
        self.r = redis.Redis(host='127.0.0.1',port=6379, decode_responses=True, charset="utf-8")
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
        #print("Key:", key,", new value:", value)
        old_value = self.r.get(str(key) + ":now")
        if not old_value:
            old_value = 0.0
        #print("Old value:", old_value)
        self.r.set(str(key) + ":old", old_value )
        old_value = self.r.get(str(key) + ":time:now")
        if not old_value:
            old_value = 0.0
        elapsed_time = int(time.time() - float(old_value))
        if elapsed_time >= 86400:
            print("Old value of",str(key),"set",round(elapsed_time/86400),"days ago.")
        elif elapsed_time >= 3600:
            print("Old value of",str(key),"set",round(elapsed_time/3600),"hours ago.")
        elif elapsed_time >= 60:
            print("Old value of",str(key),"set",round(elapsed_time/60),"minutes ago.")
        else:
            pass
            #print("Old value set", round(elapsed_time),"seconds ago.")
        self.r.set(str(key) + ":time:old", old_value)
        self.r.set(str(key) + ":now",str(value))
        self.r.set(str(key) + ":time:now",str(time.time()))

    def retrieveState(self, key:str) -> float:
        '''Retrieves the last version of a desired key

        Args:
            key (str): Name of the key
        '''

        try:
            state_value = float(self.r.get(str(key) + ":now"))
        except TypeError:
            return None
        return state_value

    def retrieveStateMetadata(self, key:str) -> dict:
        '''
        Returns a dictionary for a state that includes
        its current value, rate of change and age

        Args:
            key (str): Name of state
        '''
        try:
            now = float(self.r.get(key + ":now"))
            now_time = float(self.r.get(key + ":time:now"))
            old = float(self.r.get(key + ":old"))
            old_time = float(self.r.get(key + ":time:old"))
        except TypeError:
            return None
        try:
            delta_v = (now - old) / (now_time - old_time)
        except ZeroDivisionError:
            delta_v = None
        age = time.time() - now_time
        dict = {
            "key": key,
            "value": now,
            "old_value": old,
            "delta_v": delta_v,
            "age": age
        }
        return dict

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
            "angle": angle,
            "time": time.time()
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

    def getSensorKey(self,sensor:str) -> str:
        '''Returns name of sensor key

        Args:
            sensor (str): Name of the sensor
        '''

        return "sensor:" + sensor

    def floatDict(self, dict:dict, list:list=['distance','angle','time']) -> dict:
        '''Returns a dictionary with floats rather than strings

        Args:
            dict (dict): Dictionary to modify
            list (list): List of dictionary indices to modify 
        '''
        
        for index in list:
            try:
                dict[index] = float(dict[index])
            except KeyError:
                # print("Key error detected in Redis")
                pass
        return dict
 
    def retrieveSensorReading(self, sensor:str) -> dict:
        '''Retrieves the last message stored for a sensor
           as a dictionary

        Arg:
            sensor (str): Name of the sensor
        ''' 
        dict_key=self.r.lrange(self.getSensorKey(sensor), 0, 0)
        # msg = self.r.hmget(msg_key)
        try:
            dict = self.r.hgetall(dict_key[0])
        except IndexError:
            return None
        dict = self.floatDict(dict)
        return dict

    def retrieveSensorReadings(self, sensor:str) -> list:
        '''Retrieves all the values stored for a sensor
           as a list of dictionaries
        
        Arg:
            sensor (str): Name of sensor
        '''
        dict_list = []
        msg_key_list = self.r.lrange(self.getSensorKey(sensor), 0, -1)
        for key in msg_key_list:
            item = self.r.hgetall(key)
            item = self.floatDict(item)
            dict_list.append(item)
        return dict_list

    def retrieveLastSensorReading(self, sensor:str) -> dict:
        '''Retrieves the last value stored for a sensor
           as a dictionary

        Arg:
            sensor (str): Name of the sensor
        '''
        
        return self.retrieveSensorReading(sensor)
