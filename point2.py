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

print("Creating Stereo Depth pipeline")
pipeline = dai.Pipeline()

camLeft = pipeline.create(dai.node.MonoCamera)
camRight = pipeline.create(dai.node.MonoCamera)
stereo = pipeline.create(dai.node.StereoDepth)
xoutLeft = pipeline.create(dai.node.XLinkOut)
xoutRight = pipeline.create(dai.node.XLinkOut)
xoutDisparity = pipeline.create(dai.node.XLinkOut)
xoutDepth = pipeline.create(dai.node.XLinkOut)
xoutRectifLeft = pipeline.create(dai.node.XLinkOut)
xoutRectifRight = pipeline.create(dai.node.XLinkOut)

camLeft.setBoardSocket(dai.CameraBoardSocket.LEFT)
camRight.setBoardSocket(dai.CameraBoardSocket.RIGHT)

for monoCam in (camLeft, camRight):  # Common config
    monoCam.setResolution(dai.MonoCameraProperties.SensorResolution.THE_480_P)

stereo.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_ACCURACY)
stereo.initialConfig.setMedianFilter(dai.StereoDepthProperties.MedianFilter.KERNEL_7x7)  # KERNEL_7x7 default
stereo.setRectifyEdgeFillColor(0)  # Black, to better see the cutout
stereo.setLeftRightCheck(True)
stereo.setExtendedDisparity(False)
stereo.setSubpixel(True)

xoutLeft.setStreamName("left")
xoutRight.setStreamName("right")
xoutDisparity.setStreamName("disparity")
xoutDepth.setStreamName("depth")
xoutRectifLeft.setStreamName("rectifiedLeft")
xoutRectifRight.setStreamName("rectifiedRight")

camLeft.out.link(stereo.left)
camRight.out.link(stereo.right)
#stereo.syncedLeft.link(xoutLeft.input)
#stereo.syncedRight.link(xoutRight.input)
stereo.disparity.link(xoutDisparity.input)
stereo.depth.link(xoutDepth.input)

device = dai.Device()

with device:
    print("Starting pipeline")
    device.startPipeline(pipeline)
    print("Pipeline started")
    qDepth = [device.getOutputQueue(name = "depth", maxSize = 1, blocking = False)]
    print("Ready to process images")
    while True:
        inDepth = qDepth.get().getCvFrame()
        frame = getDepthFrame(frame)
        cv2.imshow("False Depth Image", frame)
        if cv2.waitKey(1) == ord("q"):
            break