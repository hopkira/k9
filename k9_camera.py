
#!/usr/bin/env python
# coding: utf-8
# Author: Richard Hopkins
# Date: 10 April 2023
#

import cv2
import numpy as np
import picamera
import face_recognition
from memory import Memory
from age_and_gender import AgeAndGender
from PIL import Image
import time

# 6mm 3MP Pi HQ Camera
cam_h_fov = 63.0

mem = Memory()

data = AgeAndGender()
data.load_shape_predictor('../models/shape_predictor_5_face_landmarks.dat')
data.load_dnn_gender_classifier('../models/dnn_gender_classifier_v1.dat')
data.load_dnn_age_predictor('../models/dnn_age_predictor_v1.dat')

def detect_face(rgb_frame) -> dict:
        face_locations = []
        face_locations = face_recognition.face_locations(rgb_frame)
        # If no faces are found, skip to the next frame
        if len(face_locations) == 0:
            return None

        print("Face detected")
        # Find a reasonably big face closest to the center of the image
        img_width = rgb_frame.shape[1]
        center_x = img_width // 2
        closest_face_location = None
        min_size = 0
        for location in face_locations:
            top, right, bottom, left = location
            x = (left + right) // 2
            distance = abs(x - center_x)
            size = right - left
            print("Size = ", size, ", center dist = ", distance)
            if size > min_size and size > 70 and distance < (size * 2.0):
                closest_face_location = location

        # If no faces are found, skip to the next frame
        if not closest_face_location:
            print('No qualifying face')
            return None

        bearing = round(float(cam_h_fov * (x - center_x) / img_width), 3)
        # Draw bounding box around the face
        top, right, bottom, left = closest_face_location
        cv2.rectangle(rgb_frame, (left, top), (right, bottom), (0, 255, 0), 2)

        # Perform face recognition on the closest face
        face_encodings = face_recognition.face_encodings(rgb_frame, [closest_face_location])
        if len(face_encodings) == 0:
            print("Face recognition failed")
            return None
        face_encoding = face_encodings[0]

        # Compare face encoding with known faces
        distances = face_recognition.face_distance(known_faces, face_encoding)
        min_distance_index = np.argmin(distances)
        if distances[min_distance_index] <= 0.6:
            name = face_data[min_distance_index]['name']
            gender = face_data[min_distance_index]['gender']
        else:
            subset_cv2_image = rgb_frame[top:bottom, left:right, :]
            subset_pil_image = Image.fromarray(subset_cv2_image)
            info = data.predict(subset_pil_image)
            if len(info) == 0:
                return None
            else:
                name = 'Unknown'
                gender = info[0]['gender']['value']

        # Draw text label for the detected name and gender
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(rgb_frame, f'{name}, {gender}, {bearing}', (left, top-10), font, 0.8, (0, 255, 0), 2)
        dict = {"name": name, "gender":gender, "bearing": bearing}
        return dict

# Load the known faces and their names
with open('../face_db/face_encodings.txt', 'r') as file:
    lines = file.readlines()

face_data = []
known_faces=[]
for line in lines:
    parts = line.strip().split('|')
    name = parts[0]
    gender = parts[1]
    embeddings = eval(parts[2])
    face_data.append({'name': name, 'gender': gender})
    known_faces.append(embeddings)
print("Embeddings loaded")

camera = picamera.PiCamera()
camera.resolution = (640, 480)
rgb_frame = np.empty((480, 640, 3), dtype=np.uint8)
min_head_size = camera.resolution[0] // 8
print("Min head size is ", min_head_size, " pixels")

print("Waiting for camera to warm up")

time.sleep(2.0)

# Create a window to display the video
cv2.namedWindow("Face recognition")

try:
    while True:
        #time.sleep(0.2)
        camera.capture(rgb_frame, format="rgb")
        dict = detect_face(rgb_frame)
        if dict:
            mem.storePerson(str(dict['name']), str(dict['gender']), float(dict['bearing']))
        rgb_image = cv2.cvtColor(rgb_frame, cv2.COLOR_BGR2RGB)
        cv2.imshow("Face recognition", rgb_image)
        cv2.waitKey(1)

except KeyboardInterrupt:
    # Release the video stream and close the window
    camera.close()
    cv2.destroyAllWindows()