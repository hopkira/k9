import math
import numpy as np
print("Numpy ready to crunch numbers...")
import pandas as pd
print("Pandas purring...")
import skimage.measure as skim
print("Skikit ready to decimate...")
import depthai as dai
print("3D vision seeing the light...")
from memory import Memory
print("All imports done!")

mem = Memory()

detections = []
angle = 0.0

disparity_confidence_threshold = 130

# Create pipeline
pipeline = dai.Pipeline()

# Define sources and outputs
camRgb = pipeline.create(dai.node.ColorCamera)
spatialDetectionNetwork = pipeline.create(dai.node.MobileNetSpatialDetectionNetwork)
monoLeft = pipeline.create(dai.node.MonoCamera)
monoRight = pipeline.create(dai.node.MonoCamera)
stereo = pipeline.create(dai.node.StereoDepth)

xoutRgb = pipeline.create(dai.node.XLinkOut)
xoutNN = pipeline.create(dai.node.XLinkOut)
xoutBoundingBoxDepthMapping = pipeline.create(dai.node.XLinkOut)
xoutDepth = pipeline.create(dai.node.XLinkOut)

xoutRgb.setStreamName("rgb")
xoutNN.setStreamName("detections")
xoutBoundingBoxDepthMapping.setStreamName("boundingBoxDepthMapping")
xoutDepth.setStreamName("depth")

# Properties
camRgb.setPreviewSize(300, 300)
camRgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
camRgb.setInterleaved(False)
camRgb.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)

monoLeft.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
monoLeft.setBoardSocket(dai.CameraBoardSocket.LEFT)
monoRight.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
monoRight.setBoardSocket(dai.CameraBoardSocket.RIGHT)

# Setting node configs
stereo.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_DENSITY)

spatialDetectionNetwork.setBlobPath("./mobilenet-ssd_openvino_2021.2_6shave.blob")
spatialDetectionNetwork.setConfidenceThreshold(0.5)
spatialDetectionNetwork.input.setBlocking(False)
spatialDetectionNetwork.setBoundingBoxScaleFactor(0.5)
spatialDetectionNetwork.setDepthLowerThreshold(100)
spatialDetectionNetwork.setDepthUpperThreshold(5000)

# Linking
monoLeft.out.link(stereo.left)
monoRight.out.link(stereo.right)

camRgb.preview.link(spatialDetectionNetwork.input)

spatialDetectionNetwork.passthrough.link(xoutRgb.input)
spatialDetectionNetwork.out.link(xoutNN.input)
spatialDetectionNetwork.boundingBoxMapping.link(xoutBoundingBoxDepthMapping.input)
stereo.depth.link(spatialDetectionNetwork.inputDepth)
spatialDetectionNetwork.passthroughDepth.link(xoutDepth.input)

decimate = 20
MAX_RANGE = 4000.0
height = 400.0
width = 640.0
cx = width/decimate/2
cy = height/decimate/2
fx = 1.4 # values found by measuring known sized objects at known distances
fy = 2.05

prev_frame = 0
now_frame = 0

cam_h_fov = 73.0

x_bins = pd.interval_range(start = -2000, end = 2000, periods = 40)
y_bins = pd.interval_range(start = 0, end = 1600, periods = 16)

# calculate the horizontal angle per bucket
h_bucket_fov = math.radians( cam_h_fov / 40.0)

print("Init of pipeline complete")

MAX_DIST = 1.5
MIN_DIST = 0.3
CONF = 0.2 # Normally 0.7
SWEET_SPOT = MIN_DIST + (MAX_DIST - MIN_DIST) / 2.0

def person_scan():
    '''
    Returns detectd person nearest centre of field

    detection.label == 15

    '''
    detections = inDet.detections
    if detections is not None :
        people = [detection for detection in detections
                    if detection.label == 15
                    if detection.confidence > CONF]
        if len(people) >= 1 :
            min_angle = math.pi
            for person in people:
                z = float(person.spatialCoordinates.z)
                x = float(person.spatialCoordinates.x)
                angle = abs(( math.pi / 2 ) - math.atan2(z, x))
                if angle < min_angle:
                    min_angle = angle
                    target = person
            # record
            target_angle = min_angle
            target_distance = math.sqrt(target.spatialCoordinates.z ** 2 + target.spatialCoordinates.x ** 2 )
            mem.storeSensorReading("person",target_distance,target_angle)
    else:
        print("No person found")
        return

def follow_scan(min_range = 200.0, max_range = 1500.0, decimate_level = 20, mean = True):
    '''
    Record the direction for somone to follow.  This is determined by generating 
    a simplified image of the depth image stream from the camera and determing the
    average direction and distance of the valid columns.
    
    The image can be reduced in size by using the decimate_level parameter.  
    It also will remove invalid data from the image (too close or too near pixels)
    The mechanism to determine the returned value of each new pixel can be the mean or 
    minimum values across the area can also be specified.
    
    The image is returned as a 2D numpy array.
    '''

    func = np.mean if mean else np.min
    frame = depth.getFrame()
    valid_frame = (frame >= min_range) & (frame <= max_range)
    valid_image = np.where(valid_frame, frame, max_range)
    depth_image = skim.block_reduce(valid_image,(decimate_level,decimate_level),func)
    direction, distance = follow_vector(depth_image, certainty = CONF)
    if distance is not None and direction is not None:
        distance = distance / 1000.0
        angle = direction * math.radians(cam_h_fov)
        move = (distance - SWEET_SPOT)
        mem.storeSensorReading("follow", move, angle)
    else:
        print("Nothing to follow")
    return

 
def point_cloud(min_range = 200.0, max_range = 4000.0):
    '''
    Generates a point cloud based on the provided numpy 2D depth array.
    
    Returns a 16 x 40 numpy matrix describing the forward distance to
    the points within the field of view of the camera.
    
    Initial measures closer than the min_range are discarded.  Those outside of the
    max_range are set to the max_range.
    '''
    frame = depth.getFrame()
    frame = skim.block_reduce(frame,(decimate,decimate),np.min)
    height, width = frame.shape
    print("Decimated dimensions:",height,width)
    # Convert depth map to point cloud with valid depths
    column, row = np.meshgrid(np.arange(width), np.arange(height), sparse=True)
    valid = (frame >= min_range) & (frame <= max_range)
    z = np.where(valid, frame, 0.0)
    x = np.where(valid, (z * (column - cx) /cx / fx) + 120.0 , max_range)
    y = np.where(valid, 325.0 - (z * (row - cy) / cy / fy) , max_range)
    # Flatten point cloud axes
    z2 = z.flatten()
    x2 = x.flatten()
    y2 = y.flatten()
    # Stack the x, y and z co-ordinates into a single 2D array
    cloud = np.column_stack((x2,y2,z2))
    # Filter the array by x and y co-ordinates
    in_scope = (cloud[:,1] < 1600) & (cloud[:,1] > 0) & (cloud[:,0] < 2000) & (cloud[:,0] > -2000)
    in_scope = np.repeat(in_scope, 3)
    in_scope = in_scope.reshape(-1, 3)
    scope = np.where(in_scope, cloud, np.nan)
    # Remove invalid rows from array
    scope = scope[~np.isnan(scope).any(axis=1)]
    # Index each point into 10cm x and y bins (40 x 16)
    x_index = pd.cut(scope[:,0], x_bins)
    y_index = pd.cut(scope[:,1], y_bins)
    # Place the depth values into the corresponding bin
    binned_depths = pd.Series(scope[:,2])
    # Average the depth measures in each bin
    totals = binned_depths.groupby([y_index, x_index]).mean()
    # Reshape the bins into a 16 x 40 matrix
    totals = totals.values.reshape(16,40)
    closest = np.amin(totals, axis = 0)
    closest = np.around(closest, -2)
    closest = closest.reshape(1,-1)
    count = np.nditer(closest, flags=['f_index'])
    for point in count:
        angle = h_bucket_fov * (count.index - 20)
        distance = point
        mem.storeSensorReading("point_cloud", distance, angle)
            
def follow_vector(image, max_range = 1200.0, certainty = 0.75):
    """
    Determine direction and distance to person to approach
    """
    final_distance = None
    direction = None
    # determine size of supplied image
    height, width = image.shape
    # just use the top half for analysis
    # as this will ignore low obstacles
    half_height = int(height/2)
    image = image[0:half_height,:]
    # find all the columns within the image where there are a
    # consistently significant number of valid depth measurements
    # this suggests a target in range that is reasonably tall
    # and vertical (hopefully a person's legs
    columns = np.sum(image < max_range, axis = 0) >= (certainty*half_height)
    # average the depth values of each column
    distance = np.average(image, axis = 0)
    # create an array with just the useful distances (by zeroing
    # out any columns with inconsistent data)
    useful_distances = distance * columns
    # average out all the useful distances
    # ignoring the zeros and the max_ranges
    subset = useful_distances[np.where((useful_distances < max_range) & (useful_distances > 0.0))]
    if len(subset) > 0:
        final_distance = np.average(subset)
    # determine the indices of the valid columns and average them
    # us the size of the image to determine a relative strength of
    # direction that can be converted into an angle once fov of
    # camera is known (range is theoretically -1 to +1 that
    # corresponds to the h_fov of the camera)
    mid_point = (width - 1.0) / 2.0
    indices = columns.nonzero()
    if len(indices[0]) > 0 :
        direction = (np.average(indices) - mid_point) / width
    return (direction, final_distance)

with dai.Device(pipeline) as device:
    depthQueue = device.getOutputQueue(name="depth", maxSize=1, blocking=False)
    depth = depthQueue.get()
    detectionNNQueue = device.getOutputQueue(name="detections", maxSize=4, blocking=False)
    inDet = detectionNNQueue.get()
    while True:
        person_scan()
        follow_scan()
        # point_cloud()
