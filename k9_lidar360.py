import serial
from CalcLidarData import CalcLidarData
import math
import time
import pandas as pd
import numpy as np
# from matplotlib import pyplot as plt
from memory import Memory

mem = Memory()

ser = serial.Serial(port='/dev/lidar360',
                    baudrate=230400,
                    timeout=5.0,
                    bytesize=8, 
                    parity='N',
                    stopbits=1)

tmpString = ""

angles = list()
distances = list()
lidar_start = 15
lidar_end = 76
segments = 90

# Create a number of bins covering 360 degrees (2xPI radians)
angle_bins = pd.interval_range(start = 0, end = 2*math.pi, periods = segments)
# Calculate a list of mid-points to calculate cartesian co-ords
mid_points = angle_bins.mid.tolist()
x1 = 1.5 + (6.0 * np.cos(mid_points))
y1 = 6.0 * np.sin(mid_points)
cartesian_boundary = np.column_stack((x1,y1))
# convert cartesian boundary to polar boundary
origin = [0,0]
boundary = np.linalg.norm(cartesian_boundary - origin, axis=1)
boundary = boundary[lidar_start:lidar_end]
mid_points = mid_points[lidar_start:lidar_end] # narrow list to angles that the device can see

# create cartesian bounding box for straight reverse
# collision detection
bx1, by1 = [-25,-3]
bx2, by2 = [0,3]
ll = np.array([bx1, by1])  # lower-left
ur = np.array([bx2, by2])  # upper-right

last_reading = time.time()
try:
    i = 0
    while True:
        loopFlag = True
        flag2c = False
        # collect 468 readings (complete circle)
        if len(angles) == 468 and len(distances) == 468:
            # if(i % 40 == 39):
            # create a numpy array from 468 angles/distances pair
            readings = np.column_stack((angles,distances))
            # work out which reading fits in which angle bin
            bin_index = pd.cut(readings[:,0], angle_bins)
            # put the distances into the right bins
            binned_distances = pd.Series(readings[:,1])
            # choose the closest reading in each bin
            min_dists = binned_distances.groupby([bin_index]).min()
            # turn the 90 min dist readings into an array
            min_dists = min_dists.values.reshape(segments)
            # narrow the min distances to the angles that can be seen
            min_dists = min_dists[lidar_start:lidar_end]
            # Given a narrowed range of minimum distances
            # find the index of the smallest minimum distance
            # then translate that index back into degrees.
            # The mimimum angle is 60 degrees and the maximum
            # is 300.
            min_bin_index = np.argmin(min_dists)
            angle_deg = (min_bin_index + 15) * 4
            angle_rad = math.radians(angle_deg)
            mem.storeState("rotate_angle", angle_rad)
            # Check if it is safe to turn
            # A negative figure means it isn't; a positive one means it is
            # the scale of the value gives an indication of how safe it is 
            # to rotate
            minimum_distances = min_dists - boundary
            # print(minimum_distances)
            minimum_distance = np.nanmin(minimum_distances)
            # print("Min dist:",minimum_distance)
            mem.storeState("rotate",minimum_distance)
            #  Determine how far the robot can move backwards
            # convert the polar co-ordinates into x and y arrrays
            x = min_dists * np.cos(mid_points)
            y = min_dists * np.sin(mid_points)
            points = np.column_stack((x,y))
            # find points inside the rectangle behind the dog
            inidx = np.all(np.logical_and(ll <= points, points <= ur), axis=1)
            inbox = points[inidx]
            min_x = 25.0
            if len(inbox) > 2: # more then two points means probably not sensor noise
                min_x = np.nanmax(inbox[:,0])
            mem.storeState("reverse",(min_x/10.0) + 0.3) # store in Redis in m
            '''
            # The following is for display only; not needed when running for real
            if minimum_distance > 0.0 :
                colour = 'g-'
                marker = 'go'
            else:
                colour = 'r-'
                marker = 'rx'
            outbox = points[np.logical_not(inidx)]
            rect = np.array([[bx1, by1], [bx1, by2], [bx2, by2], [bx2, by1], [bx1, by1]])
            plt.plot(inbox[:, 0], inbox[:, 1], 'rx',
                     outbox[:, 0], outbox[:, 1], marker,
                     rect[:, 0], rect[:, 1], 'r-')
            plt.plot(min_x,0,'rD') # reverse stop point
            plt.plot(x1, y1, colour) # plot turning boundary
            plt.gca().invert_yaxis()    
            plt.show()
            # plt.plot(x,y)
            #now = time.time()
            #print(now-last)
            #last = now
            '''
            # Now get next set of readings
            angles.clear()
            distances.clear()
            i = 0
            now_time = time.time()
            elapsed = now_time - last_reading
            # print("FFS:",1/elapsed)
            # last_reading = now_time
            if elapsed > 10:
                last_reading = now_time
                reverse = mem.retrieveStateMetadata("reverse")
                # print(reverse)
                print("Can't move more than","{:.1f}".format(abs(reverse['value'])),"m backward.")
                # rotate = mem.retrieveState("rotate")
                rotate_angle = mem.retrieveStateMetadata("rotate_angle")
                print("Angle to obstacle is ",round(math.degrees(rotate_angle['value']))," degees.")
                rotate = (mem.retrieveStateMetadata("rotate"))
                if rotate['value'] < 0 and abs(rotate['delta_v']) < 10:
                    print("Unsafe to rotate")
                else:
                    print("Safe to rotate")
                print("======== END OF READINGS ========")
            time.sleep(0.1)


        while loopFlag:
            b = ser.read()
            tmpInt = int.from_bytes(b, 'big')
            
            if (tmpInt == 0x54):
                tmpString +=  b.hex()+" "
                flag2c = True
                continue
            
            elif(tmpInt == 0x2c and flag2c):
                tmpString += b.hex()

                if(not len(tmpString[0:-5].replace(' ','')) == 90 ):
                    tmpString = ""
                    loopFlag = False
                    flag2c = False
                    continue

                lidarData = CalcLidarData(tmpString[0:-5])

                # Add angles and distance data to the lists
                angles.extend(lidarData.Angle_i)
                distances.extend(lidarData.Distance_i)

                tmpString = ""
                loopFlag = False
            else:
                tmpString += b.hex()+" "
            
            flag2c = False

        i +=1

except KeyboardInterrupt:
    ser.close()