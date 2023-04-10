import numpy as np
import time
import picamera
import face_recognition
from age_and_gender import AgeAndGender
from PIL import Image

data = AgeAndGender()
data.load_shape_predictor('../models/shape_predictor_5_face_landmarks.dat')
data.load_dnn_gender_classifier('../models/dnn_gender_classifier_v1.dat')
data.load_dnn_age_predictor('../models/dnn_age_predictor_v1.dat')

camera = picamera.PiCamera()
camera.resolution = (640, 480)
rgb_frame = np.empty((480, 640, 3), dtype=np.uint8)

time.sleep(2)

while True:
    camera.capture(rgb_frame, format="rgb")
    face_locations = []
    face_locations = face_recognition.face_locations(rgb_frame)
    for location in face_locations:
            top, right, bottom, left = location
            subset_cv2_image = rgb_frame[top:bottom, left:right, :]
            subset_pil_image = Image.fromarray(subset_cv2_image)
            info = data.predict(subset_pil_image)
            print(info)