
#!/usr/bin/env python
# coding: utf-8
# Author: Richard Hopkins and Chat-GPT-4
# Date: 3 April 2023
#
# Written in part by GPT-4 using the following prompt:
#
# Write a Python program that will:
#   1. Run on the Raspberry Pi and use the Pi Camera to perform the detection
#      of a face closest to the centre of the camera image. 
#   2. Perform face recognition of the detected face against a list of known faces.
#      Each known face has an assigned name and gender.
#   3. If the face is not recognized from the list call it "Unknown" and use a 
#      specialist model to determine the likely gender of the face.
#   4. Record the name, gender and horizontal bearing of the face (in degrees) in Redis

import cv2
import numpy as np
import face_recognition
import math
from memory import Memory
import time

# 6mm 3MP Pi HQ Camera
cam_h_fov = 63.0

mem = Memory()

# Load the known faces and their names
known_faces = []
known_names = []
known_genders = []
with open("known_faces.txt", "r") as f:
    lines = f.readlines()
    for line in lines:
        face_encoding = np.fromstring(line, dtype=float, sep=' ')
        known_faces.append(face_encoding)
        name, gender = line.split(":")
        known_names.append(name)
        known_genders.append(gender.strip())

#gender model
#model structure: https://data.vision.ee.ethz.ch/cvl/rrothe/imdb-wiki/static/gender.prototxt
#pre-trained weights: https://data.vision.ee.ethz.ch/cvl/rrothe/imdb-wiki/static/gender.caffemodel

# Load the gender detection model
gender_model = cv2.dnn.readNetFromCaffe("gender.prototxt", "gender.caffemodel")

# Open the video stream from the Pi Camera
camera = cv2.VideoCapture(0)

try:
    while True:
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

        mem.storeState("face_bearing",float(bearing))
        mem.storeState("face_name",float(index))
        mem.storeState("face_gender",float(gender_prediction))

except KeyboardInterrupt:
    # Release handle to the webcam
    camera.release()