import serial
from CalcLidarData import CalcLidarData
import math
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
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
bx2, by2 = [-1.5,3]
ll = np.array([bx1, by1])  # lower-left
ur = np.array([bx2, by2])  # upper-right

# TODO need a routine to calculate blockers behind the dog
# https://stackoverflow.com/questions/33051244/numpy-filter-points-within-bounding-box
# https://stackoverflow.com/questions/42352622/finding-points-within-a-bounding-box-with-numpy


#last = time.time()
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
            # Check if it is safe to turn
            # A negative figure means it isn't; a positive one means it is
            # the scale of the value gives an indication of how safe it is 
            # to rotate
            minimum_distance = np.nanmin(min_dists - boundary)
            mem.storeState("rotate",minimum_distance)
            # Visualize
            # convert the polar co-ordinates into x and y arrrays
            x = min_dists * np.cos(mid_points)
            y = min_dists * np.sin(mid_points)
            points = np.column_stack((x,y))
            inidx = np.all(np.logical_and(ll <= points, points <= ur), axis=1)
            inbox = points[inidx]
            try:
                min_x = np.nanmax(inbox[:,0]) # nearest point to dog
            except ValueError:
                min_x = -25.0 # default is 2.5m away
            mem.storeState("reverse",min_x)
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
            # Now get next set of readings
            angles.clear()
            distances.clear()
            i = 0


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