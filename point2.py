#!/usr/bin/env python3

import cv2
import numpy as np
import depthai as dai

def getDisparityFrame(frame):
    maxDisp = stereo.initialConfig.getMaxDisparity()
    disp = (frame * (255.0 / maxDisp)).astype(np.uint8)
    disp = cv2.applyColorMap(disp, cv2.COLORMAP_JET)
    return disp

def getDepthFrame(frame):
    min = np.amin(frame)
    frame = frame - min
    max = np.amax(frame)
    print(min,max)
    # disp = (frame * (65535.0 / max)).astype(np.uint16)
    disp = (frame / 255.0).astype(np.uint8)
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

stereo.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_DENSITY)
stereo.initialConfig.setMedianFilter(dai.StereoDepthProperties.MedianFilter.KERNEL_7x7)  # KERNEL_7x7 default
stereo.setRectifyEdgeFillColor(0)  # Black, to better see the cutout
stereo.setLeftRightCheck(False)
stereo.setExtendedDisparity(False)
stereo.setSubpixel(False)

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

streams = ["disparity", "depth"]

device = dai.Device()

'''
calibData = device.readCalibration()
leftMesh, rightMesh = getMesh(calibData)
if generateMesh:
    meshLeft = list(leftMesh.tobytes())
    meshRight = list(rightMesh.tobytes())
    stereo.loadMeshData(meshLeft, meshRight)

if meshDirectory is not None:
    saveMeshFiles(leftMesh, rightMesh, meshDirectory)
'''

print("Creating DepthAI device")
with device:
    device.startPipeline(pipeline)

    # Create a receive queue for each stream
    qList = [device.getOutputQueue(stream, 8, blocking=False) for stream in streams]

    while True:
        for q in qList:
            name = q.getName()
            frame = q.get().getCvFrame()
            if name == "depth":
                frame = getDepthFrame(frame)
            elif name == "disparity":
                frame = getDisparityFrame(frame)

            cv2.imshow(name, frame)
        if cv2.waitKey(1) == ord("q"):
            break