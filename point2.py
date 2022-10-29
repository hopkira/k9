#!/usr/bin/env python3

import cv2
import numpy as np
import depthai as dai

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

device = dai.Device()

with device:
    print("Starting pipeline")
    device.startPipeline(pipeline)
    print("Pipeline started")
    qDepth = device.getOutputQueue(name = "depth", maxSize = 8, blocking = False)
    print("Ready to process images")
    while True:
        frame = qDepth.get().getCvFrame()
        im_frame = getDepthFrame(frame)
        cv2.imshow("False Depth Image", im_frame)
        if cv2.waitKey(1) == ord("q"):
            break