#!/usr/bin/env python3

import cv2
import warnings
import numpy as np
import depthai as dai
import pandas as pd

from memory import Memory

mem = Memory()

class Fwd_Collision_Detect():
    '''
    Creates a focussed point cloud that determines any obstacles
    directly in front of the robot and returns the minimum distance
    to the closest
    '''

    def __init__(self):
        # Point cloud loop constants
        self.x_bins = pd.interval_range(start = -350, end = 350, periods = 7)
        self.y_bins = pd.interval_range(start = 0, end = 1600, periods = 16)
        self.fx = 1.4 # values found by measuring known sized objects at known distances
        self.fy = 3.3
        self.pc_width = 640
        self.cx = self.pc_width / 2
        self.pc_height = 480
        self.cy = self.pc_height / 2
        self.pc_max_range  = 10000.0
        self.pc_min_range  = 300.0
        self.column, self.row = np.meshgrid(np.arange(self.pc_width), np.arange(self.pc_height), sparse=True)

    def record_min_dist(self,depth_image) -> float:
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
        print(np.shape(scope))
        # place the points into a set of 10cm square bins
        x_index = pd.cut(scope[:,0], self.x_bins)
        y_index = pd.cut(scope[:,1], self.y_bins)
        binned_depths = pd.Series(scope[:,2])
        # simplify each bin to a single median value
        totals = binned_depths.groupby([y_index, x_index]).median()
        # shape the simplified bins into a 2D array
        totals = totals.values.reshape(16,7)
        min = np.amin(totals)
        im_totals = totals - min
        mean = np.mean(im_totals)
        disp = (im_totals / mean * 128.0).astype(np.uint8)
        disp = cv2.applyColorMap(disp, cv2.COLORMAP_HOT)
        dim = (640, 280)
        resized = cv2.resize(disp, dim, interpolation = cv2.INTER_AREA)
        cv2.imshow("Resized point cloud image", resized)
        # for each column in the array, find out the closest
        # bin; as the robot cannot duck or jump, the
        # y values are irrelevant
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            min_dist_cols = np.nanmin(totals, axis = 0)
            min_dist = float(np.nanmin(min_dist_cols))
        # inject the resulting 40 sensor points into thew
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

def getDepthFrame(frame):
    min = np.amin(frame)
    frame = frame - min
    mean = np.mean(frame)
    disp = (frame / mean * 128.0).astype(np.uint8)
    disp = cv2.applyColorMap(disp, cv2.COLORMAP_HOT)
    return disp

print("Creating stereo depth pipeline")
pipeline = dai.Pipeline()
camLeft = pipeline.create(dai.node.MonoCamera)
camRight = pipeline.create(dai.node.MonoCamera)
stereo = pipeline.create(dai.node.StereoDepth)
xoutDepth = pipeline.create(dai.node.XLinkOut)
camLeft.setBoardSocket(dai.CameraBoardSocket.LEFT)
camRight.setBoardSocket(dai.CameraBoardSocket.RIGHT)
camLeft.setResolution(dai.MonoCameraProperties.SensorResolution.THE_480_P)
camRight.setResolution(dai.MonoCameraProperties.SensorResolution.THE_480_P)
stereo.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_ACCURACY)
stereo.initialConfig.setMedianFilter(dai.StereoDepthProperties.MedianFilter.KERNEL_7x7)
stereo.setRectifyEdgeFillColor(0)
stereo.setLeftRightCheck(True)
stereo.setExtendedDisparity(False)
stereo.setSubpixel(True)
xoutDepth.setStreamName("depth")
camLeft.out.link(stereo.left)
camRight.out.link(stereo.right)
stereo.depth.link(xoutDepth.input)

print("Creating device")
device = dai.Device()

fc = Fwd_Collision_Detect()

with device:
    print("Starting pipeline")
    device.startPipeline(pipeline)
    print("Pipeline started")
    qDepth = device.getOutputQueue(name = "depth", maxSize = 3, blocking = False)
    print("Ready to process images")
    while True:
        frame = qDepth.get().getCvFrame()
        print("Min dist:",fc.record_min_dist(frame))
        # print(np.shape(frame)) # 480, 640
        im_frame = getDepthFrame(frame)
        cv2.imshow("False Depth Image", im_frame)
        if cv2.waitKey(1) == ord("q"):
            break