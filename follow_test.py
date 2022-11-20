from memory import Memory
import time

mem = Memory()
while True:
    target_dict = mem.retrieveLastSensorReading("follow")
    person_dict = mem.retrieveLastSensorReading("person")
    # chose the detected legs over person targetting
    if target_dict["angle"] != 0 or target_dict["distance"] != 0 :
        print("Active legs being used")
        angle = target_dict["angle"]
        move = target_dict["distance"]
    elif person_dict["angle"] !=0 or person_dict["distance"] != 0:
        print("Active person being used")
        angle = person_dict["angle"]
        move = person_dict["distance"]
    # if there is nothing detected, then aim for
    # the last detected set of legs
    else:
        target_dicts = mem.retrieveSensorReadings("follow")
        print("Historic legs being used for direction purposes")
        for target_dict in target_dicts:
            if target_dict["angle"] != 0:
                angle = target_dict["angle"]
                move = 0
                break
    # move if the angle or distance is not zero
    if angle != 0 or move !=0:
        print("Following: direction:", angle, "distance:", move)
        damp_angle = 3.0
        damp_distance = 2.0
        if abs(angle) >= (0.1 * damp_angle) :
            if mem.retrieveState("rotate") > 0.0:
                print("Turning: ",str(angle / damp_angle))
            else:
                print("Turn blocked")
                time.sleep(3.0)
        else:
            if abs(move) >= (0.05 * damp_distance) :
                distance = move / damp_distance
                safe_forward = mem.retrieveState("forward")
                # nb should also retrieve a backward state
                if  safe_forward > distance:
                    print("Moving forward detected distance: ", str(distance) )
                else:
                    print("Moving forward safe distance: ", str(safe_forward))