#!/usr/bin/env python
# coding: utf-8
# Author: Richard Hopkins
# Date: 8 August 2022
#
# This program uses the Oak-Lite camera from Luxonis
# to support three key functions:
#   1. to identify the vector to the person in front of K9
#   2. to identify the vector to the nearest vertical obstacle
#      that is near K9 (that may not be recognisable as a person)
#   3. generate a point cloud to help avoid collisions
#   4. generate a focussed point cloud to avoid forward collisions

import time
from turtle import distance
print("Time started...")
import math
print("Counting on fingers... yep")
# import skimage.measure as skim
#print("Skikit ready to decimate...")
import depthai as dai
print("Depthai looking forward...")
import numpy as np
print("Numpy is running...")
import pandas as pd
print("Pandas are frolicking...")
import warnings
from memory import Memory
print("All imports done!")
from matplotlib import pyplot as plt
print("Picture drawing loaded...")

mem = Memory()

# Oak-Lite Horizontal FoV
cam_h_fov = 73.0

# Shared contraints 
min_range = 300.0 # default for device is mm
max_range = 1500.0 # default for device is mm
sweet_spot = min_range + (max_range - min_range) / 2.0

# Heel constants
heel_confidence = 0.7 # NN certainty that its a person
heel_lower = 200 # minimum depth for person detection
heel_upper = 5000 # maximu depth for person detection

# Path to NN model
nnBlob = "/home/pi/depthai-python/examples/models/mobilenet-ssd_openvino_2021.4_5shave.blob"

# Create OAK-D Lite pipeline
print("Creating Oak pipeline...")
pipeline = dai.Pipeline()

# Create nodes within pipeline
stereo = pipeline.create(dai.node.StereoDepth)
right = pipeline.create(dai.node.MonoCamera)
left = pipeline.create(dai.node.MonoCamera)
camRgb = pipeline.create(dai.node.ColorCamera)
spatialDetectionNetwork = pipeline.create(dai.node.MobileNetSpatialDetectionNetwork)
objectTracker = pipeline.create(dai.node.ObjectTracker)

# Configure stereo vision node
stereo.setLeftRightCheck(False)
stereo.setExtendedDisparity(False)
stereo.setSubpixel(False)
stereo.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_DENSITY)

# Configure mono camera nodes
right.setBoardSocket(dai.CameraBoardSocket.RIGHT)
left.setBoardSocket(dai.CameraBoardSocket.LEFT)
right.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
left.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)

# Configure colour camera node
camRgb.setPreviewSize(300, 300)
camRgb.setPreviewKeepAspectRatio(False)
camRgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
camRgb.setInterleaved(False)
camRgb.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)

# Configure Spatial Detection Neural Network Node
spatialDetectionNetwork.setBlobPath(nnBlob)
spatialDetectionNetwork.setConfidenceThreshold(heel_confidence)
spatialDetectionNetwork.input.setBlocking(False)
spatialDetectionNetwork.setBoundingBoxScaleFactor(0.5)
spatialDetectionNetwork.setDepthLowerThreshold(heel_lower)
spatialDetectionNetwork.setDepthUpperThreshold(heel_upper)

# Configure Object Tracker Node
objectTracker.setDetectionLabelsToTrack([15])
objectTracker.setTrackerType(dai.TrackerType.ZERO_TERM_COLOR_HISTOGRAM)
objectTracker.setTrackerIdAssignmentPolicy(dai.TrackerIdAssignmentPolicy.SMALLEST_ID)
objectTracker.inputTrackerFrame.setBlocking(False)
objectTracker.inputTrackerFrame.setQueueSize(2)

# Linking nodes together in pipeline
# Connect mono cameras to stereo pipe
left.out.link(stereo.left)
right.out.link(stereo.right)

# Connect colour camera preview to Spatial Detection Network pipeline
camRgb.preview.link(spatialDetectionNetwork.input)

# Connect colour camera video frame to Object Tracker pipeline
camRgb.video.link(objectTracker.inputTrackerFrame)

# Pass the video received.by the Spatial Detection Network to the to Object Tracker input
spatialDetectionNetwork.passthrough.link(objectTracker.inputDetectionFrame)

# Connext the output of the Spatial Detection Network to the input of the object tracker
spatialDetectionNetwork.out.link(objectTracker.inputDetections)

# Connect the depth output to the Spatial Detection Network depth input
stereo.depth.link(spatialDetectionNetwork.inputDepth)

# Define OAK-lite output streams
# Create depth output stream
xOut = pipeline.create(dai.node.XLinkOut)
xOut.setStreamName("depth")
stereo.depth.link(xOut.input)

# Create rgb output stream
#xOutRgb = pipeline.create(dai.node.XLinkOut)
#xOutRgb.setStreamName("rgb")
#camRgb.video.link(xOutRgb.input)

# Create tracker output stream
trackerOut = pipeline.create(dai.node.XLinkOut)
trackerOut.setStreamName("tracklets")
#objectTracker.passthroughTrackerFrame.link(xOutRgb.input)
objectTracker.out.link(trackerOut.input)

# Decimate the depth image by a factor of 4
config = stereo.initialConfig.get()
config.postProcessing.decimationFilter.decimationMode.NON_ZERO_MEDIAN
config.postProcessing.decimationFilter.decimationFactor = 4
stereo.initialConfig.set(config)


class Point_Cloud():
    '''
    Creates a point cloud that determines any obstacles in front of the robot
    '''

    def __init__(self):
        # Point cloud loop constants
        self.x_bins = pd.interval_range(start = -2000, end = 2000, periods = 40)
        self.y_bins = pd.interval_range(start = 0, end = 1600, periods = 16)
        self.fx = 1.4 # values found by measuring known sized objects at known distances
        self.fy = 3.3
        self.pc_width = 160
        self.cx = self.pc_width / 2
        self.pc_height = 100
        self.cy = self.pc_height / 2
        self.pc_max_range  = 10000.0
        self.pc_min_range  = 200.0
        self.column, self.row = np.meshgrid(np.arange(self.pc_width), np.arange(self.pc_height), sparse=True)
        # Pre-calculate the 40 angles in the point cloud
        self.angles_array = []
        angles = np.arange(-19.5, 20.5, 1)
        for angle in angles:
            my_angle = math.radians(angle / 19.5 * cam_h_fov / 2.0)
            round_angle = round(my_angle, 3)
            self.angles_array.append(round_angle)

    def record_point_cloud(self,depth_image):
        '''
        Distills the point cloud down to a single value that is the distance to the
        nearest obstacle that is directly in front of the robot
        '''

        # Ignore points too close or too far away
        valid = (depth_image >= self.pc_min_range) & (depth_image <= self.pc_max_range)
        # Calculate the point cloud using simple extrapolation from depth
        z = np.where(valid, depth_image, 0.0)
        x = np.where(valid, (z * (self.column - self.cx) /self.cx / self.fx) + 120.0 , self.pc_max_range)
        y = np.where(valid, 268 - (z * (self.row - self.cy) / self.cy / self.fy) , self.pc_max_range) # measured height is 268mm
        z2 = z.flatten()
        x2 = x.flatten()
        y2 = y.flatten()
        cloud = np.column_stack((x2,y2,z2))
        # Remove points that are projected to fall outside the field of view
        # points below floor level, above 1.6m or those more than 2m to the
        # sides of the robot are ignored
        in_scope = (cloud[:,1] < 1600) & (cloud[:,1] > 0) & (cloud[:,0] < 2000) & (cloud[:,0] > -2000)
        in_scope = np.repeat(in_scope, 3)
        in_scope = in_scope.reshape(-1, 3)
        scope = np.where(in_scope, cloud, np.nan)
        scope = scope[~np.isnan(scope).any(axis=1)]
        # place the points into a set of 10cm square bins
        x_index = pd.cut(scope[:,0], self.x_bins)
        y_index = pd.cut(scope[:,1], self.y_bins)
        binned_depths = pd.Series(scope[:,2])
        # simplify each bin to a single median value
        totals = binned_depths.groupby([y_index, x_index]).median()
        # shape the simplified bins into a 2D array
        totals = totals.values.reshape(16,40)
        # for each column in the array, find out the closest
        # bin; as the robot cannot duck or jump, the
        # y values are irrelevant
        point_cloud = np.nanmin(totals, axis = 0)
        # inject the resulting 40 sensor points into the
        # short term memory of the robot
        for index,point in enumerate(point_cloud):
            print(str(index),str(point))
            mem.storeSensorReading("oak",float(point),float(self.angles_array[index]))


class Fwd_Collision_Detect():
    '''
    Creates a focussed point cloud that determines any obstacles
    directly in front of the robot and returns the minimum distance
    to the closest
    '''

    def __init__(self):
        # Point cloud loop constants
        self.x_bins = pd.interval_range(start = -350, end = 350, periods = 7)
        self.y_bins = pd.interval_range(start = 0, end = 1600, periods = 1)
        self.fx = 1.4 # values found by measuring known sized objects at known distances
        self.fy = 3.3
        self.pc_width = 160
        self.cx = self.pc_width / 2
        self.pc_height = 100
        self.cy = self.pc_height / 2
        self.pc_max_range  = 10000.0
        self.pc_min_range  = 200.0
        self.column, self.row = np.meshgrid(np.arange(self.pc_width), np.arange(self.pc_height), sparse=True)

    def record_min_dist(self,depth_image):
        '''
        Distills the point cloud down to a single value that is the distance to the
        nearest obstacle that is directly in front of the robot
        '''

        # Ignore points too close or too far away
        valid = (depth_image >= self.pc_min_range) & (depth_image <= self.pc_max_range)
        # Calculate the point cloud using simple extrapolation from depth
        z = np.where(valid, depth_image, 0.0)
        x = np.where(valid, (z * (self.column - self.cx) /self.cx / self.fx) + 120.0 , self.pc_max_range)
        y = np.where(valid, 268 - (z * (self.row - self.cy) / self.cy / self.fy) , self.pc_max_range) # measured height is 268mm
        z2 = z.flatten()
        x2 = x.flatten()
        y2 = y.flatten()
        cloud = np.column_stack((x2,y2,z2))
        # Remove points that are projected to fall outside the field of view
        # points below floor level, above 1.6m or those more than 2m to the
        # sides of the robot are ignored
        in_scope = (cloud[:,1] < 1600) & (cloud[:,1] > 0) & (cloud[:,0] < 350) & (cloud[:,0] > -350)
        in_scope = np.repeat(in_scope, 3)
        in_scope = in_scope.reshape(-1, 3)
        scope = np.where(in_scope, cloud, np.nan)
        scope = scope[~np.isnan(scope).any(axis=1)]
        # place the points into a set of 10cm square bins
        x_index = pd.cut(scope[:,0], self.x_bins)
        y_index = pd.cut(scope[:,1], self.y_bins)
        binned_depths = pd.Series(scope[:,2])
        # simplify each bin to a single median value
        totals = binned_depths.groupby([y_index, x_index]).median()
        # shape the simplified bins into a 2D array
        totals = totals.values.reshape(1,7)
        # for each column in the array, find out the closest
        # bin; as the robot cannot duck or jump, the
        # y values are irrelevant
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            min_dist = np.nanmin(totals)
        # inject the resulting 40 sensor points into the
        # short term memory of the robot
        # point_cloud = point_cloud[16:24]
        # min_dist = np.amin(point_cloud)
        # mem.storeState("forward", min_dist)
        #plt.scatter(x2,-y2,c=z2,cmap='afmhot',s=10)
        #plt.xlim(-350,350)
        #plt.ylim(-200,1600)
        #plt.show()
        if not np.isnan(min_dist):
            mem.storeState("forward", float(min_dist/1000.0))
        pass
        

class Legs_Detector():
    ''''
    Detects legs and records the vector to them.  This is done by 
    detecting vertical slices of the image that include an object
    and then averaging the distance for each slice. Te valid slices
    are averaged to detemine the likely centre of the legs
    '''

    def __init__ (self):
        # decimate_level = 7 # reduces size of depth image
        # func = np.mean # averages cells during decimation
        self.keep_top = 0.85 # bottom 15% of image tends to include floor
        self.certainty = 0.7 # likelihood that a person in in the column

    def record_legs_vector(self,depth_image):
        '''
        Analysse image and record vector to legs
        '''
        # reduce the size of the depth image by decimating it by
        # a factor (numbers between 3 and 20 seem to work best)
        # remove the bottom of the image as the figures that
        # are valid are mostly floor
        pix_height, pix_width = depth_image.shape
        # pix_width = int(width / decimate_level)
        # pix_height = int(keep_top * height / decimate_level)
        # depth_image = skim.block_reduce(frame,(decimate_level,decimate_level),func)
        # just use the depth data within valid ranges
        valid_frame = (depth_image >= min_range) & (depth_image <= max_range)
        valid_image = np.where(valid_frame, depth_image, max_range)
        valid_image = valid_image[0:pix_height,:]
        # work out which columns are likely to contain a vertical object
        columns = np.sum(valid_image < max_range, axis = 0) >= (self.certainty*pix_height)
        columns = columns.reshape(1,-1)
        # work out the average distance per column for valid readings
        distance = np.average(valid_image, axis = 0)
        # eliminate any readings not in a column with a consistent vertical object
        useful_distances = distance * columns
        # narrow down the array to just those 'vertical' columns
        subset = useful_distances[np.where((useful_distances < max_range) & (useful_distances > 0.0))]
        # determine the average distance to all valid columns
        if len(subset) > 0:
            final_distance = np.average(subset)
        # determine the middle of the depth image
        mid_point = int((pix_width - 1.0 ) / 2.0)
        # collate a list of all the column numbers that have the
        # 'vertical' data in them
        indices = columns.nonzero()[1]
        # determine the average angle that these columns as a multiplier for the h_fov
        if len(indices) > 0 :
            direction = (np.average(indices) - mid_point) / pix_width
            angle = direction * math.radians(cam_h_fov)
            move = (final_distance - sweet_spot)
            move = move / 1000.0 # convert to m
            # print("Follow:", move, angle)
            mem.storeSensorReading("follow", move, angle)


class Person_Detector():
    '''
    This part of the code will identify the nearest
    person in front of K9 (up to about 5m away).  As they
    move, they should be tracked
    '''

    def __init__(self):
        # Initially there is no identified target, so dictionary is empty
        self.target =   {
            "id"    :   None,
            "status":   None,
            "x"     :   None,
            "z"     :   None
            }

    def record_person_vector (self, trackletsData):
        '''
        If a target has been identified than look through the trackletData
        and retrieve the latest information tracklet for that id
        and store it in the target object
        if there is no active matching id, then drop them as a target
        if there is NO target identified yet, then scan the trackletData and
        find the closest NEW or TRACKED tracklet instance and make them the
        target.  Record the tracklet vector in robot dog's memory
        '''

        heel_range = heel_upper # reset range to max
        if self.target["id"] is not None:
            # extract the tracklet id that matches the existing id
            candidate = [tracklet for tracklet in trackletsData
                            if tracklet.id == self.target["id"]
                            if tracklet.status.name == "TRACKED"
                            ]
            # print("Existing target " + str(target["id"]) + " seen again")
            if candidate:
                # refresh the data if identified
                self.target["id"]  = candidate[0].id
                self.target["status"] = candidate[0].status.name
                self.target["x"] = candidate[0].spatialCoordinates.x
                self.target["z"] = candidate[0].spatialCoordinates.z
                # print("Target data " + str(target["id"]) + " refreshed")
            else:
                # drop the target otherwise
                self.target["id"] =  None
                # print("Target lost and forgotten")
        else:
            # look for any new or tracked tracklets
            candidates = [tracklet for tracklet in trackletsData
                        if (tracklet.status.name == "NEW"
                            or tracklet.status.name == "TRACKED")]
            for candidate in candidates:
                # identify the closest tracklet
                # print("New or tracked candidate: " + str(candidate.id))
                if candidate.spatialCoordinates.z < heel_range:
                    # print("Closer candidate spotted")
                    heel_range = candidate.spatialCoordinates.z
                    self.target["id"]  = candidate.id
                    self.target["status"] = candidate.status.name
                    self.target["x"] = candidate.spatialCoordinates.x
                    self.target["z"] = candidate.spatialCoordinates.z
                    # print("Closest target id:",str(target["id"]))
        # store the nearest tracket (if there is one) in
        # the short term memory
        if self.target["id"] is not None:
            z = float(self.target["z"])
            x = float(self.target["x"])
            angle = ( math.pi / 2 ) - math.atan2(z, x)
            distance = max((math.sqrt(z ** 2 + x ** 2 )) - sweet_spot, 0)
            mem.storeSensorReading("person",distance/1000.0,angle)


# Declare the device
# device = dai.Device(pipeline)
with dai.Device(pipeline) as device:
    # declare buffer queues for the streams
    qDep = device.getOutputQueue(name="depth", maxSize=1, blocking=False)
    # qRgb = device.getOutputQueue(name="rgb", maxSize=1, blocking=False)
    qTrack = device.getOutputQueue("tracklets", maxSize=1, blocking=False)
    print("Oak pipeline running...")
    # f_pc = Point_Cloud()
    f_ld = Legs_Detector()
    f_pd = Person_Detector()
    f_cd = Fwd_Collision_Detect()
    # Main loop  starts  here
    # counter =  0
    last_reading = time.time()
    while True:
        start_time = time.time() # start time of the loop
        inDepth = qDep.get()
        depth_image = inDepth.getFrame() # get latest information from queue
        # Retrieve latest tracklets
        track = qTrack.get()
        trackletsData = track.tracklets
        #if counter == 10:
        #    f_pc.record_point_cloud(depth_image)
        #    counter = 0
        f_cd.record_min_dist(depth_image=depth_image)
        f_ld.record_legs_vector(depth_image=depth_image)
        f_pd.record_person_vector(trackletsData=trackletsData)
        # print out the FPS achieved
        # counter += 1
        now_time = time.time()
        # Every 10 seconds print out the short term memory
        if (now_time - last_reading) > 10:
            print("FPS: ","{:.1f}".format(1.0 / (now_time - start_time)))
            last_reading = now_time
            person = mem.retrieveLastSensorReading("person")
            try: 
                print("Person at:","{:.2f}".format(person['distance']),"m and at","{:.2f}".format(person['angle']),"radians.")
            except KeyError:
                print("No Person currently detected")
            follow = mem.retrieveLastSensorReading("follow")
            try: 
                print("Move towards:","{:.2f}".format(follow['distance']),"m and at","{:.2f}".format(follow['angle']),"radians.")
            except KeyError:
                print("Nothing to follow")
            min_dist = mem.retrieveState("forward")
            print("Can't move more than","{:.1f}".format(min_dist),"m forward.")
            point_cloud = mem.retrieveSensorReadings("oak")
            for point in point_cloud:
                print(str(point))
            print("*** OAK PIPE OUTPUT ENDS ***")