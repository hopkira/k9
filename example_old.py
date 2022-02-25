device = depthai.Device('', False)

config={
    "streams": ["depth","metaout"],
    "ai": {
        "blob_file": "/home/pi/3dvision/mobilenet-ssd/mobilenet-ssd.blob",
        "blob_file_config": "/home/pi/3dvision/mobilenet-ssd/mobilenet-ssd.json",
        "calc_dist_to_bb": True,
        "camera_input": "right"
    },
    "camera": {
        "mono": {
            # 1280x720, 1280x800, 640x400 (binning enabled)
            # reducing resolution decreases min depth as
            # relative disparity is decreased
            'resolution_h': 400,
            'fps': 10   
        }
    }
}

body_cam = device.create_pipeline(config=config)

# Retrieve model class labels from model config file.
model_config_file = config["ai"]["blob_file_config"]
mcf = open(model_config_file)
model_config_dict = json.load(mcf)
labels = model_config_dict["mappings"]["labels"]

if body_cam is None:
    raise RuntimeError("Error initializing body camera")

nn2depth = device.get_nn_to_depth_bbox_mapping()

def nn_to_depth_coord(x, y, nn2depth):
    x_depth = int(nn2depth['off_x'] + x * nn2depth['max_w'])
    y_depth = int(nn2depth['off_y'] + y * nn2depth['max_h'])
    return x_depth, y_depth

nnet_packets, data_packets = body_cam.get_available_nnet_and_data_packets()
for nnet_packet in nnet_packets:
    detections = list(nnet_packet.getDetectedObjects())
    if detections is not None :
        people = [detection for detection in detections
                    if detection.label == 15
                    if detection.confidence > CONF]
        if len(people) >= 1 :
            min_angle = math.pi
            for person in people:
                z = float(person.depth_z)
                x = float(person.depth_x)
                angle = abs(( math.pi / 2 ) - math.atan2(z, x))
                if angle < min_angle:
                    min_angle = angle
                    target = person
            return target