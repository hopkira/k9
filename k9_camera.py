
#!/usr/bin/env python
# coding: utf-8
# Author: Richard Hopkins and Chat-GPT
# Date: 3 April 2023
#
# Written in part by Chat-GPT using the following prompt:
#
# Write a Python program that will:
#   1. Run on the Raspberry Pi and use the Pi Camera to perform the detection
#      of a face closest to the centre of the camera image. 
#   2. Perform face recognition of the detected face against a list of known faces.
#      Each known face has an assigned name and gender.
#   3. If the face is not recognized from the list call it "Unknown" and use a 
#      specialist model to determine the likely gender of the face.
#   4. Record the name, gender and horizontal bearing of the face (in degrees) in Redis
#
# Gender recognition code written by Chat-GPT but clearly from the following:
# @article{Rothe-IJCV-2018,
#  author = {Rasmus Rothe and Radu Timofte and Luc Van Gool},
#  title = {Deep expectation of real and apparent age from a single image without facial landmarks},
#  journal = {International Journal of Computer Vision},
#  volume={126},
#  number={2-4},
#  pages={144--157},
#  year={2018},
#  publisher={Springer}
# }

import cv2
import numpy as np
import face_recognition
import math
from memory import Memory
import time
import sys

# 6mm 3MP Pi HQ Camera
cam_h_fov = 63.0

mem = Memory()

# Load the known faces and their names
with open('../face_db/face_embeddings.txt', 'r') as file:
    lines = file.readlines()

data = []
for line in lines:
    parts = line.strip().split('|')
    name = parts[0]
    gender = parts[1]
    embeddings = eval(parts[2])
    data.append({'name': name, 'gender': gender, 'embeddings': embeddings})
print(data)

sys.exit()
# gender models can be downloaded from:
# model structure: https://data.vision.ee.ethz.ch/cvl/rrothe/imdb-wiki/static/gender.prototxt
# pre-trained weights: https://data.vision.ee.ethz.ch/cvl/rrothe/imdb-wiki/static/gender.caffemodel

# Load the gender detection model
gender_model = cv2.dnn.readNetFromCaffe("gender.prototxt", "gender.caffemodel")

# Open the video stream from the Pi Camera
camera = cv2.VideoCapture(0)

try:
    while True:
        time.sleep(0.2)
        # Grab a single frame of video
        ret, frame = camera.read()

        # Convert the frame to RGB color
        rgb_frame = frame[:, :, ::-1]

        # Find all the faces and their locations in the current frame
        face_locations = face_recognition.face_locations(rgb_frame)

        # If no faces are found, skip to the next frame
        if len(face_locations) == 0:
            continue

        # Find the face closest to the center of the image
        center_x = frame.shape[1] // 2
        min_distance = math.inf
        closest_face_location = None
        for location in face_locations:
            y, x, _ = location
            distance = abs(x - center_x)
            if distance < min_distance:
                min_distance = distance
                closest_face_location = location

        # Crop the image to the closest face
        top, right, bottom, left = closest_face_location
        face_image = rgb_frame[top:bottom, left:right]

        # Encode the face image and compare it to the known faces
        unknown_face_encoding = face_recognition.face_encodings(face_image)
        if len(unknown_face_encoding) > 0:
            unknown_face_encoding = unknown_face_encoding[0]
            matches = face_recognition.compare_faces(known_faces, unknown_face_encoding)
            # Find the name and gender of the closest match, or use "Unknown" and the predicted gender
            name = "Unknown"
            if True in matches:
                index = matches.index(True)
                name = known_names[index]
                gender = known_genders[index]
                if gender == "male": 
                    gender_prediction = 0.0
                else:
                    gender_prediction = 1.0
            else:
                # Resize the face image to match the input size of the gender detection model
                resized_face_image = cv2.resize(face_image, (227, 227))
                # Convert the face image to the input format of the gender detection model
                blob = cv2.dnn.blobFromImage(resized_face_image, scalefactor=1.0, size=(227, 227),
                                            mean=(78.4263377603, 87.7689143744, 114.895847746), swapRB=False, crop=False)
                # Pass the face image through the gender detection model to predict the gender
                gender_model.setInput(blob)
                gender_predictions = gender_model.forward()
                # Male if < 0.5 otherwise female
                gender_prediction = round(gender_predictions[0])

        # Calculate the bearing to the face
        face_center_x = (right + left) // 2
        bearing = -(face_center_x - center_x) / center_x
        angle = float(bearing * math.radians(cam_h_fov))
        gender="male" if gender_prediction==1.0 else "female"
        mem.storePerson(str(name), str(gender), float(bearing))


except KeyboardInterrupt:
    # Release handle to the webcam
    camera.release()