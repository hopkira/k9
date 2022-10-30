#!/usr/bin/env python
# coding: utf-8
# Author: Richard Hopkins
# Date: 30 October 2022
#
# This program uses the OAK-D lite camera from Luxonis
# to support three key functions:
#   1. to identify the vector to the person in front of K9
#   2. to identify the vector to the nearest vertical obstacle
#      that is near K9 (that may not be recognisable as a person)
#   3. generate a point cloud to help avoid forward collisions
#   4. generate a focussed point cloud to avoid straight line collisions
#
import time
#from turtle import distance
print("Time started...")
import argparse
print("Ready for arguments...")
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
#from matplotlib import pyplot as plt
#print("Picture drawing loaded...")

testing = False

mem = Memory()

# Oak-Lite Horizontal FoV
cam_h_fov = 73.0

# Point cloud variabless
cam_height = 268.0 # mm distance from floor
fx = 1.3514 # values derived mathematically due to new resolution and fov
fy = 1.7985 # values derived mathematically due to new resolution and fov
pc_width = 160
cx = pc_width / 2
pc_height = 120
cy = pc_height / 2

# Shared contraints 
min_range = 750.0 # default for device is mm
max_range = 1750.0 # default for device is mm
sweet_spot = min_range + ((max_range - min_range) / 2.0)

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
stereo.setLeftRightCheck(True)
stereo.setExtendedDisparity(False)
stereo.setSubpixel(True)
stereo.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_ACCURACY)
stereo.initialConfig.setMedianFilter(dai.StereoDepthProperties.MedianFilter.KERNEL_7x7)
stereo.setRectifyEdgeFillColor(0)

# Configure mono camera nodes
right.setBoardSocket(dai.CameraBoardSocket.RIGHT)
left.setBoardSocket(dai.CameraBoardSocket.LEFT)
right.setResolution(dai.MonoCameraProperties.SensorResolution.THE_480_P)
left.setResolution(dai.MonoCameraProperties.SensorResolution.THE_480_P)

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

# Create tracker output stream
trackerOut = pipeline.create(dai.node.XLinkOut)
trackerOut.setStreamName("tracklets")
objectTracker.out.link(trackerOut.input)

# Decimate the depth image by a factor of 4
config = stereo.initialConfig.get()
config.postProcessing.decimationFilter.decimationMode.NON_ZERO_MEDIAN
config.postProcessing.decimationFilter.decimationFactor = 4
stereo.initialConfig.set(config)

def main():
    global testing
    parser = argparse.ArgumentParser(description='Runs OAK pipe to find people in view.')
    '''parser.add_argument('command',
                        choices=['arc','fd','bk','lt','rt','stop'],
                        help='movement command')
    parser.add_argument('parameter',
                        type=float,
                        default=0.0,
                        nargs='?',
                        help='distance in metres or angle in radians')
    '''
    parser.add_argument('-t', '--test',
                        action='store_true',
                        help='execute in visual testing mode')
    args = parser.parse_args()
    testing = args.test
    if testing:
        print("Visual test mode active")

def getDepthFrame(frame):
    frame_min = np.amin(frame)
    frame = frame - frame_min
    mean = np.mean(frame)
    disp = (frame / mean * 128.0).astype(np.uint8)
    dim = (640, 480) 
    resized = cv2.resize(disp, dim, interpolation = cv2.INTER_AREA)
    resized_disp = cv2.applyColorMap(resized, cv2.COLORMAP_HOT)
    return resized_disp

class Point_Cloud():
    '''
    Calculates a point cloud of an asked for size in mm
    expressed as a 2D numpy array of 100x100mm blocks.
    Each block contains the median depth reading of all the pixels
    that have been projected into each block by the point cloud.
    '''

    def __init__(self, width:int=4000, height:int=1560, min_depth:float = 200.0, max_depth:float = 10000.0):
        self.width = width
        self.height = height
        self.width_elem = int(self.width/pc_width)
        self.height_elem = int(self.height/pc_height)
        self.pc_min_range = min_depth
        self.pc_max_range = max_depth
        self.x_bins = pd.interval_range(start = -int(self.width/2), end = int(self.width/2), periods = int(self.width/pc_width))
        self.y_bins = pd.interval_range(start = 0, end = self.height, periods = int(self.height/pc_height))
        self.column, self.row = np.meshgrid(np.arange(pc_width), np.arange(pc_height), sparse=True)

    def populate_bins(self, depth_image):
        '''
        Work out which points are valid, project them into a point cloud and then
        group them into bins.  The median value of each bin is then reported back
        as a two dimensional numpy array (height x width)
        '''
        # Ignore points too close or too far away
        valid = (depth_image >= self.pc_min_range) & (depth_image <= self.pc_max_range)
        #print("Depth image",np.shape(depth_image))
        #print("Valid image",np.shape(valid))

        # Calculate the point cloud using simple extrapolation from depth
        z = np.where(valid, depth_image, 0.0)
        x = np.where(valid, (z * (self.column - cx) / cx / fx) + 120.0, self.pc_max_range)
        y = np.where(valid, cam_height - (z * (self.row - cy) / cy / fy), self.pc_max_range)
        z2 = z.flatten()
        x2 = x.flatten()
        y2 = y.flatten()
        cloud = np.column_stack((x2,y2,z2))
        # Remove points that are projected to fall outside the field of view
        # points below floor level, above 1.6m or those more than 2m to the
        # sides of the robot are ignored
        in_scope = (cloud[:,1] < self.height) & (cloud[:,1] > 0) & (cloud[:,0] < self.width/2) & (cloud[:,0] > -self.width/2)
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
        totals = totals.values.reshape(self.height_elem,self.width_elem)
        return totals

class Big_Point_Cloud():
    '''
    Creates a point cloud that determines any obstacles in front of the robot
    '''

    def __init__(self):
        self.bpc = Point_Cloud(4000,1560)
        # Pre-calculate the angles in the point cloud
        self.angles_array = np.arange(-36.5, 39.42, 3.04)

    def record_point_cloud(self,depth_image):
        '''
        Distills the point cloud down to a single value that is the distance to the
        nearest obstacle that is directly in front of the robot
        '''
        totals = self.bpc.populate_bins(depth_image)
        # for each column in the array, find out the closest
        # bin; as the robot cannot duck or jump, the
        # y values are irrelevant
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            point_cloud = np.nanmin(totals, axis = 0)
            # print("PC shape:",np.shape(point_cloud))
        # inject the resulting 40 sensor points into the
        # short term memory of the robot
        if testing:
            points = np.zeros((27,2))
            for index, point in enumerate(point_cloud):
                angle = self.angles_array[index]
                depth = point/10.0
                x,y = calcCartesian(angle, depth)
                if not (np.isnan(x) or np.isnan(y)):
                    points[index+1,0] = x
                    points[index+1,1] = y
            x_min = np.nanmin(points[:,0])
            x_max = np.nanmax(points[:,0])
            y_min = np.nanmin(points[:,1])
            y_max = np.nanmax(points[:,1])
            win_width = int(abs(x_max - x_min))
            win_height = int(abs(y_max - y_min))       
            pc_image = np.zeros((win_height, win_width, 3), np.uint8)
            for index in range(26):
                from_p = (int(points[index,0] - x_min), int(points[index,1] - y_min))
                to_p = (int(points[index+1,0] - x_min), int(points[index+1,1] - y_min))
                cv2.line(pc_image, from_p, to_p, color=(0,255,0), thickness = 3)
            x_text = "X: {:.1f}m, {:.1f}m".format(x_min/100, x_max/100)
            y_text = "Y: {:.1f}m, {:.1f}m".format(y_min/100, y_max/100)
            pc_image = cv2.putText(pc_image, x_text, (10, 20), cv2.FONT_HERSHEY_PLAIN, 1, colour_green)
            pc_image = cv2.putText(pc_image, y_text, (10, 40), cv2.FONT_HERSHEY_PLAIN, 1, colour_green)
            cv2.imshow("Point cloud render", pc_image)
        for index, point in enumerate(point_cloud):
            # print(str(index),str(point))
            mem.storeSensorReading("oak",float(point/1000.0), math.radians(float(self.angles_array[index])))

def calcCartesian(angle, depth):
    x = depth * math.sin(math.radians(angle))
    y = depth * math.cos(math.radians(angle))
    return x,y

class Fwd_Collision_Detect():
    '''
    Creates a focussed point cloud that determines any obstacles
    directly in front of the robot and returns the minimum distance
    to the closest; this determines how far it can move in a straight line
    '''

    def __init__(self):
        self.fcd = Point_Cloud(800, 960) # 5 x 8

    def record_min_dist(self,depth_image) -> float:
        '''
        Distills the point cloud down to a single value that is the distance to the
        nearest obstacle that is directly in front of the robot
        '''

        totals = self.fcd.populate_bins(depth_image)
        if testing:
            img_min = float(np.nanmin(totals))
            im_totals = totals - img_min
            img_max = float(np.nanmax(im_totals))
            # print("PC:",min, max)
            disp = (im_totals / img_max * 255.0).astype(np.uint8)
            disp = cv2.applyColorMap(disp, cv2.COLORMAP_HOT)
            flipv = cv2.flip(disp, 0)
            dim = (250, 400) 
            resized = cv2.resize(flipv, dim, interpolation = cv2.INTER_AREA)
            cv2.imshow("Point cloud image", resized)
        # for each column in the array, find out the closest
        # bin; as the robot cannot duck or jump, the
        # y values are irrelevant
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            min_dist = float(np.nanmin(totals))
        # inject the resulting 40 sensor points into the
        # short term memory of the robot
        # point_cloud = point_cloud[16:24]
        # min_dist = np.amin(point_cloud)
        # mem.storeState("forward", min_dist)
        #plt.scatter(x2,-y2,c=z2,cmap='afmhot',s=10)
        #plt.xlim(-350,350)
        #plt.ylim(-200,1600)
        #plt.show()
        if min_dist:
            min_dist = float(min_dist/1000.0)
            mem.storeState("forward", min_dist)
            return min_dist
        else:
            return None
        

class Legs_Detector():
    ''''
    Detects legs and records the vector to them.  This is done by 
    detecting vertical slices of the image that include an object
    and then averaging the distance for each slice. One or two contiguous
    rectangle of a minimum width are used to determine the target.
    '''

    def __init__ (self):
        # decimate_level = 7 # reduces size of depth image
        # func = np.mean # averages cells during decimation
        self.keep_top = 0.7 # bottom 15% of image tends to include floor
        self.certainty = 0.5 # likelihood that a person in in the column
         # max_depth_diff is the largest allowable differrence between the column
         # depth readings in mm to allow both columns to be taken into account in the 
         # direction and depth.
        self.max_depth_diff = 200
        # Min_col_size is the minimum width of a consecutive column 
        # to allow it to be taken into account.
        self.min_col_size = 5
        # max_gap_dist_prod is a measure of how close two rectangles
        # are in reality by multiplying  the gaps between their centres
        # by the sensed depth.  Too large a number means the two rectangles
        # can't be legs from the same person
        self.max_gap_dist_prod = 100000.0

    def record_legs_vector(self,depth_image) -> dict:
        '''
        Analyse image and record vector to legs, returns a dict of
        columns that contain legs and target data
        '''
        # reduce the size of the depth image by decimating it by
        # a factor (numbers between 3 and 20 seem to work best)
        # remove the bottom of the image as the figures that
        # are valid are mostly floor
        pix_height, pix_width = depth_image.shape
        # pix_width = int(width / decimate_level)
        pix_height = int(self.keep_top * pix_height)
        # depth_image = skim.block_reduce(frame,(decimate_level,decimate_level),func)
        # just use the depth data within valid ranges
        valid_frame = (depth_image >= min_range) & (depth_image <= max_range)
        # invalid cells will be set to max_range
        valid_image = np.where(valid_frame, depth_image, max_range)
        # remove the bottom 15% of the image
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
        # determine the middle of the depth image
        mid_point = int((pix_width - 1.0 ) / 2.0)
        # collate a list of all the column numbers that have the
        # 'vertical' data in them
        indices = columns.nonzero()[1]
        # if there are sufficient non zero columns left, then
        # determine the average angle that these columns as a multiplier for the h_fov
        num_cols = int(len(indices))
        # Create a column_set list of each group of indices
        column_set = np.split(indices, np.where(np.diff(indices) != 1)[0]+1)
        # Strip out all the consecutive columns that are not wide enough
        # and place the remaining colums in big_cols
        big_cols = []
        for col in column_set:
            if col.size >= self.min_col_size:
                big_cols.append(col)
        # Calculate the mean distances (big_dists) for the big columns and
        # store their column ranges (big_col_ind).
        big_dists =  []
        big_col_ind = []
        indices =  {}
        if len(big_cols) > 0:
            for big_col in big_cols:
                bc_min = np.amin(big_col)
                bc_max = np.amax(big_col)
                big_col_ind.append([bc_min, bc_max])
                dists = []
                for col in big_col:
                    dists.append(np.mean(valid_image[:,col-1]))
                dist_mean = float(np.mean(dists))
                big_dists.append(dist_mean)
        else:
            mem.storeSensorReading("follow",0,0)
            return None
        # record the result for the nearest column
        result = {}
        index_min = np.argmin(big_dists)
        result = {
                    "index" : int(index_min),
                    "dist" : float(dist_mean),
                    "min_col" : int(big_col_ind[index_min][0]),
                    "max_col" : int(big_col_ind[index_min][1])
        }
        '''
        Refine the result by deciding whether to combine in the second 
        nearest contiguous rectangle in terms of depth. This will only happen
        if the depth distances are within a fixed tolerance and the rectangle
        themselves are within a range determined by their distance. 
        If the depth is small then the rectangles can be further apart, 
        if the depth is further, then the rectangles must be closer. 
        This measure is calculated from the product of the distance between 
        the centres of the rectangle and their minimum distance.
        '''
        result["combined"] = 0
        if np.size(big_dists) > 1:
            store = big_dists[index_min]
            big_dists[index_min] = max_range
            index_next_min = np.argmin(big_dists)
            big_dists[index_min] = store
            cen1 = float((big_col_ind[index_min][0] + big_col_ind[index_min][1]) / 2)
            cen2 = float((big_col_ind[index_next_min][0] + big_col_ind[index_next_min][1]) / 2)
            dist_cen = float(abs(cen1 - cen2))
            if ((big_dists[index_next_min] - big_dists[index_min]) < self.max_depth_diff) and \
            ((dist_cen * float(big_dists[index_min])) < self.max_gap_dist_prod):
                result["min_col"] = int(min(big_col_ind[index_min][0], big_col_ind[index_next_min][0]))
                result["max_col"] = int(max(big_col_ind[index_min][1],big_col_ind[index_next_min][1]))
                result["combined"] = 1.0
        # prepare the result object
        direction = float((((float(result["max_col"]) + float(result["min_col"])) / 2) - mid_point) / pix_width)
        angle = float(direction * math.radians(cam_h_fov))
        my_angle = math.degrees(angle)
        move = float(result["dist"] - sweet_spot)
        move = move / 1000.0 # convert to m
        # print("Follow:", move, angle)
        mem.storeSensorReading("follow", move, angle)
        result["top"] = self.keep_top
        result["angle"] = float(my_angle)
        result["dist"] =  float(result["dist"]) / 1000.0
        result["max_cols"] = int(pix_width)
        result["num_cols"] = float(result["max_col"]) - float(result["min_col"])
        return result


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

    def record_person_vector (self, trackletsData) -> dict:
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
                    self.target["tracklet"] = candidate
                    # print("Closest target id:",str(target["id"]))
        # store the nearest tracket (if there is one) in
        # the short term memory
        if self.target["id"] is not None:
            z = float(self.target["z"])
            x = float(self.target["x"])
            angle = ( math.pi / 2 ) - math.atan2(z, x)
            trk_distance = max((math.sqrt(z ** 2 + x ** 2 )) - sweet_spot, 0)
            trk_distance = trk_distance / 1000.0
            mem.storeSensorReading("person",trk_distance,angle)
            my_angle = math.degrees(angle)
            target_dict = {
                "angle" : my_angle,
                "dist" : trk_distance,
                "tracklet" : self.target["tracklet"]
            }
            return target_dict
        else:
            mem.storeSensorReading("person",0,0)
            return {}


# if executed from the command line then execute arguments as functions
if __name__ == '__main__':
    main()

if testing:
    import cv2
    print("Windows are open...")
    xOutRgb = pipeline.create(dai.node.XLinkOut)
    xOutRgb.setStreamName("rgb")
    camRgb.video.link(xOutRgb.input)
    # objectTracker.passthroughTrackerFrame.link(xOutRgb.input)
    

# Declare the device
# device = dai.Device(pipeline)
with dai.Device(pipeline) as device:
    # declare buffer queues for the streams
    FPS =  0.0
    qDep = device.getOutputQueue(name="depth", maxSize=3, blocking=False)
    if testing:
        qRgb = device.getOutputQueue(name="rgb", maxSize=1, blocking=False)
    qTrack = device.getOutputQueue("tracklets", maxSize=1, blocking=False)
    print("Oak pipeline running...")
    f_pc = Big_Point_Cloud()
    f_ld = Legs_Detector()
    f_pd = Person_Detector()
    f_cd = Fwd_Collision_Detect()
    # Main loop  starts  here
    if testing:
        cv2.namedWindow("OAK Perception Preview", cv2.WINDOW_NORMAL)
    counter =  0
    FPS_counter = 0
    last_reading = time.time()
    while True:
        start_time = time.time() # start time of the loop
        depth_image = qDep.get().getCvFrame() # get latest information from queue
        #inDepth = qDep.get()
        #depth_image = inDepth.get().getCvFrame() # get latest information from queue
        # Retrieve latest tracklets
        track = qTrack.get()
        trackletsData = track.tracklets
        if counter == 10:
            f_pc.record_point_cloud(depth_image)
            counter = 0
        min_dist =  f_cd.record_min_dist(depth_image=depth_image)
        legs_dict = f_ld.record_legs_vector(depth_image=depth_image)
        target_dict = f_pd.record_person_vector(trackletsData=trackletsData)
        if testing:
            im_frame = getDepthFrame(depth_image)
            cv2.imshow("False Depth Image", im_frame)
            in_rgb = qRgb.get()
            preview = in_rgb.getCvFrame() # get RGB frame
            # Resize frame to fit Pi VNC viewer
            scale = 0.5
            width = int(preview.shape[1] * scale)
            height = int(preview.shape[0] * scale)
            dsize = (width, height)
            colour_red = (0, 0, 255)
            col_white = (255,255,255)
            colour_green = (0, 255, 0)
            thickness = 3
            output = cv2.resize(preview, dsize)
            # Draw a green bounding box
            # around the nearest person
            if min_dist:
                dist_txt = "safe dist = " +  "{:.2f}".format(min_dist) + "m"
                output = cv2.putText(output, dist_txt, (10, height - 40), cv2.FONT_HERSHEY_PLAIN, 1, col_white)
                FPS_txt = "FPS = " +  "{:.2f}".format(FPS)
                output = cv2.putText(output, FPS_txt, (10, height - 20), cv2.FONT_HERSHEY_PLAIN, 1, col_white)
            if target_dict:
                t = target_dict["tracklet"]             
                bearing_txt = "t0 = " + "{:.0f}".format(target_dict['angle']) + "degrees"
                dist_txt = "td = " +  "{:.2f}".format(target_dict['dist']) + "m"
                roi = t.roi.denormalize(width, height)
                x1 = int(roi.topLeft().x)
                y1 = int(roi.topLeft().y)
                x2 = int(roi.bottomRight().x)
                y2 = int(roi.bottomRight().y)
                output =  cv2.rectangle(output, (x1, y1), (x2, y2), colour_green, thickness)
                output = cv2.putText(output, bearing_txt, (x1 + 10, y2 - 40), cv2.FONT_HERSHEY_PLAIN, 1, colour_green)
                output = cv2.putText(output, dist_txt, (x1 + 10, y2 - 20), cv2.FONT_HERSHEY_PLAIN, 1, colour_green)
            #  If legs have been spotted, draw red
            #  bounding boxes
            if legs_dict:
                box_min = legs_dict["min_col"]
                box_max = legs_dict["max_col"]
                cols = legs_dict['max_cols']
                x_min = int(box_min /cols * width)
                x_max = int(box_max / cols * width)
                y_max = int(height * legs_dict['top'])
                output = cv2.rectangle(output, (x_min, 0), (x_max, y_max), colour_red, thickness)
                mean_col = (box_min + box_max) / 2
                x_dir = int(mean_col/cols * width)
                output = cv2.circle(output, (x_dir, int(y_max/2)), 10, colour_red, thickness)
                bearing_txt = "0 = " + "{:.0f}".format(legs_dict['angle']) + "degrees"
                dist_txt = "d = " +  "{:.2f}".format(legs_dict['dist']) + "m"
                com_txt = "comb: " + str(legs_dict["combined"])
                output = cv2.putText(output, bearing_txt, (x_dir + 15, int(y_max/2)), cv2.FONT_HERSHEY_PLAIN, 1, colour_red)
                output = cv2.putText(output, dist_txt, (x_dir + 15, int(y_max/2) + 20), cv2.FONT_HERSHEY_PLAIN, 1, colour_red)
                output = cv2.putText(output, com_txt, (x_dir + 15, int(y_max/2) + 40), cv2.FONT_HERSHEY_PLAIN, 1, colour_red)
            cv2.imshow("OAK Perception Preview", output)
            if cv2.waitKey(1) == ord("q"):
                break
        # print out the FPS achieved
        counter += 1
        FPS_counter +=1
        now_time = time.time()
        if not testing:
            time.sleep(0.1)
        # Every 10 seconds print out the short term memory
        if (now_time - last_reading) > 10:
            FPS = FPS_counter / 10.0
            print("FPS: " + "{:.1f}".format(FPS))
            last_reading = now_time
            FPS_counter = 0
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
            print("*** OAK PIPE OUTPUT ENDS ***")