from memory import Memory
import time

def get_target(dict:dict) -> tuple:
    try:
        if dict["angle"] != 0 or dict["distance"] != 0 :
            print(str(dict))
            angle = dict["angle"]
            move = dict["distance"]
            return angle, move
    except KeyError:
        return False, False
    
def check_targets() -> tuple:
    angle = False
    move = False
    source = ""
    target_dict = mem.retrieveLastSensorReading("follow")
    person_dict = mem.retrieveLastSensorReading("person")
    if any((get_target(target_dict))):
        angle, move = get_target(target_dict)
        print("Legs:", angle, move)
    elif any((get_target(person_dict))):
        angle, move = get_target(person_dict)
        print("Person:", angle, move)
    else:
        target_dicts = mem.retrieveSensorReadings("follow")
        for target_dict in target_dicts:
            if any((get_target(target_dict))):
                angle, move = get_target(target_dict)
                age = target_dict["time"] - time.time()
                print(age,"s - old legs:", angle, move)
                break
    return angle, move

mem = Memory()
while True:
    time.sleep(1)
    angle = 0
    move = 0
    angle, move = check_targets()
    # move if the angle or distance is not zero
    if angle != 0 or move !=0:
        print("Target dir:", angle, "dist:", move)
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
                safe_backward = mem.retrieveState("reverse")
                # nb should also retrieve a backward state
                if distance >= 0:
                    if  safe_forward > distance:
                        print("Moving forward detected distance:", str(distance))
                    else:
                        print("Moving forward safe distance:", str(safe_forward))
                else:
                    if safe_backward < distance:
                        print("Moving backward detected distance:", str(distance))
                    else:
                        print("Moving backward safe distance:", str(safe_backward))
    else:
        print("Nothing detected, not moving")