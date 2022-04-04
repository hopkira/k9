#!/usr/bin/env python
# coding: utf-8
# Author: Richard Hopkins
# Date: 28 March 2022
#
# This program uses the Oak-Lite camera from Luxonis
# to support two key functions:
#   * to identify the vector to the person in front of K9
#   * to identify the vector to the nearest vertical obstacle
#     that is near K9 (that may not be recognisable as a person)

import skimage.measure as skim
print("Skikit ready to decimate...")
import depthai as dai
print("Depthai looking forward...")
import numpy as np
print("Numpy is running...")
import math
print("Counting on fingers... yep")
from memory import Memory
print("All imports done!")

mem = Memory()

# Follow loop constants 
min_range = 300.0 # default for device is mm
max_range = 1500.0 # default for device is mm
decimate_level = 7 # reduces size of depth image
func = np.mean # averages cells during decimation
keep_top = 0.85 # bottom 15% of image tends to include floor
certainty = 0.7 # likelihood that a person in in the column

# Heel loop  constants
heel_confidence = 0.7 # NN certainty that its a person
heel_lower = 200 # minimum depth for person detection
heel_upper = 5000 # maximu depth for person detection

# Heeling distance
sweet_spot = min_range + (max_range - min_range) / 2.0

# Oak-Lite Horizontal FoV
cam_h_fov = 73.0

# Path to NN model
nnBlob = "/home/pi/depthai-python/examples/models/mobilenet-ssd_openvino_2021.4_5shave.blob"

# Initially there is no identified target
target = None

# Create pipeline
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
xOutRgb = pipeline.create(dai.node.XLinkOut)
xOutRgb.setStreamName("rgb")
camRgb.video.link(xOutRgb.input)

# Create tracker output stream
trackerOut = pipeline.create(dai.node.XLinkOut)
trackerOut.setStreamName("tracklets")
objectTracker.passthroughTrackerFrame.link(xOutRgb.input)
objectTracker.out.link(trackerOut.input)

# Declare the device
# device = dai.Device(pipeline)
with dai.Device(pipeline) as device:
    # declare buffer queues for the streams
    qDep = device.getOutputQueue(name="depth", maxSize=1, blocking=False)
    qRgb = device.getOutputQueue(name="rgb", maxSize=1, blocking=False)
    qTrack = device.getOutputQueue("tracklets", maxSize=4, blocking=False)
    print("Oak pipeline running...")
    # Main loop  starts  here
    while True:
        #
        # Follow section of code
        #
        # The follow capability ueses the depth stream to determine
        # where the nearest pair of legs  are
        inDepth = qDep.get()
        frame = inDepth.getFrame() # get latest information from queue

        # reduce the size of the depth image by decimating it by
        # a factor (numbers between 3 and 20 seem to work best)
        # remove the bottom of the image as the figures that
        # are valid are mostly floor
        height, width = frame.shape
        pix_width = int(width / decimate_level)
        pix_height = int(keep_top * height / decimate_level)
        depth_image = skim.block_reduce(frame,(decimate_level,decimate_level),func)
        # just use the depth data within valid ranges
        valid_frame = (depth_image >= min_range) & (depth_image <= max_range)
        valid_image = np.where(valid_frame, depth_image, max_range)
        valid_image = valid_image[0:pix_height,:]
        # work out which columns are likely to contain a vertical object
        columns = np.sum(valid_image < max_range, axis = 0) >= (certainty*pix_height)
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
        mid_point = int(((width / decimate_level) - 1.0 ) / 2.0)
        # collate a list of all the column numbers that have the
        # 'vertical' data in them
        indices = columns.nonzero()[1]
        # determine the average angle that these columns as a multiplier for the h_fov
        if len(indices) > 0 :
            direction = (np.average(indices) - mid_point) / (width / decimate_level)
            distance = distance / 1000.0 # convert to m
            angle = direction * math.radians(cam_h_fov)
            move = (distance - sweet_spot)
            mem.storeSensorReading("follow", move, angle)
            print("Follow: ", move, angle)
        #
        # Heeling/tracking section of code
        #
        # This part of the code will identify the nearest
        # person in front of K9 (up to about 5m away).  As they
        # move, they should be tracked
        #
        heel_range = heel_upper # reset range to max
        #
        #for t in trackletsData:
        #    print(t.id,t.status.name,t.spatialCoordinates.x, t.spatialCoordinates.z)
        # Tracklets can have the status NEW, TRACKED or LOST
        #
        # Retrieve latest tracklets
        track = qTrack.get()
        trackletsData = track.tracklets
        # if a target has been identified than look through the trackletData
        # and retrieve the latest information tracklet for that id
        # and store it in the target object
        # if there is no active matching id, then drop them as a target
        # if there is NO target identified yet, then scan the trackletData and
        # find the closest NEW or TRACKED tracklet instance and make them the
        # target
        if target is not None:
            candidate = [tracklet for tracklet in trackletsData
                            if tracklet.id == target.id]
            if candidate is not None:
                target  = candidate
            else:
                target =  None
        else:
            candidates = [tracklet for tracklet in trackletsData
                        if tracklet.status.name == "NEW"
                        if tracklet.status.name == "TRACKED"]
            for candidate in candidates:
                if candidate.spatialCoordinates.z < heel_range:
                    heel_range = candidate.spatialCoordinates.z
                    target = candidate
        
        if target is not None:
            z = float(target.spatialCoordinates.z)
            x = float(target.spatialCoordinates.x)
            angle = abs(( math.pi / 2 ) - math.atan2(z, x))
            distance = math.sqrt(target.spatialCoordinates.z ** 2 + target.spatialCoordinates.x ** 2 )
            mem.storeSensorReading("person",distance,angle)
            print("Person:", distance, angle)