#!/usr/bin/env python
# coding: utf-8
# Author: Richard Hopkins
# Date: 29 October 2022
#
import cv2
import numpy as np
import depthai as dai

# Depth configuration
resolution = (1280, 720)
lrcheck = True
extended = True
subpixel = True
median = dai.StereoDepthProperties.MedianFilter.KERNEL_7x7

print("Creating Stereo Depth pipeline")
pipeline = dai.Pipeline()
camLeft = pipeline.create(dai.node.MonoCamera)
camRight = pipeline.create(dai.node.MonoCamera)
stereo = pipeline.create(dai.node.StereoDepth)
xoutLeft = pipeline.create(dai.node.XLinkOut)
xoutRight = pipeline.create(dai.node.XLinkOut)
xoutDepth = pipeline.create(dai.node.XLinkOut)
camLeft.setBoardSocket(dai.CameraBoardSocket.LEFT)
camRight.setBoardSocket(dai.CameraBoardSocket.RIGHT)
camLeft.setResolution(dai.MonoCameraProperties.SensorResolution.THE_720_P)
camRight.setResolution(dai.MonoCameraProperties.SensorResolution.THE_720_P)
stereo.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_ACCURACY)
stereo.initialConfig.setMedianFilter(median)
stereo.setRectifyEdgeFillColor(0)
stereo.setLeftRightCheck(lrcheck)
stereo.setExtendedDisparity(extended)
stereo.setSubpixel(subpixel)
xoutDepth.setStreamName("depth")
camLeft.out.link(stereo.left)
camRight.out.link(stereo.right)
stereo.syncedLeft.link(xoutLeft.input)
stereo.syncedRight.link(xoutRight.input)
stereo.depth.link(xoutDepth.input)

device = dai.Device()

with device:
    device.startPipeline(pipeline)
    qDepth = [device.getOutputQueue(name = "depth", max_size = 3, blocking = False)]
    while True:

        inDepth = qDepth.get().getCvFrame()
        frame = frame.astype(np.uint16)
        cv2.imshow("Depth", frame)
        if cv2.waitKey(1) == ord("q"):
            break