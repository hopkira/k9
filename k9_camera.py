
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
# gender models can be downloaded from:
# model structure: https://data.vision.ee.ethz.ch/cvl/rrothe/imdb-wiki/static/gender.prototxt
# pre-trained weights: https://data.vision.ee.ethz.ch/cvl/rrothe/imdb-wiki/static/gender.caffemodel

# Load the gender detection model
#gender_model = cv2.dnn.readNetFromCaffe("gender.prototxt", "gender_net.caffemodel")
#print("Gender model loaded")

import cv2
import numpy as np
import picamera
import face_recognition
import math
from memory import Memory
import time
import sys

# 6mm 3MP Pi HQ Camera
cam_h_fov = 63.0

mem = Memory()

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

i = 0

try:
    while True:

        time.sleep(0.2)
        face_locations = []
        camera.capture(rgb_frame, format="rgb")

        face_locations = face_recognition.face_locations(rgb_frame)

        # If no faces are found, skip to the next frame
        if len(face_locations) == 0:
            cv2.imshow("Face recognition", rgb_frame)
            cv2.waitKey(1)
            continue

        print("Face detected")
        # Find a reasonably big face closest to the center of the image
        center_x = rgb_frame.shape[1] // 2
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
            cv2.imshow("Face recognition", rgb_frame)
            cv2.waitKey(1)
            continue
        
        # Draw bounding box around the face
        top, right, bottom, left = closest_face_location
        cv2.rectangle(rgb_frame, (left, top), (right, bottom), (0, 255, 0), 2)

        # Perform face recognition on the closest face
        face_encodings = face_recognition.face_encodings(rgb_frame, [closest_face_location])
        if len(face_encodings) == 0:
            print("Face recognition failed")
            cv2.imshow("Face recognition", rgb_frame)
            cv2.waitKey(1)
            continue
        face_encoding = face_encodings[0]

        # Compare face encoding with known faces
        distances = face_recognition.face_distance(known_faces, face_encoding)
        min_distance_index = np.argmin(distances)
        if distances[min_distance_index] <= 0.6:
            name = face_data[min_distance_index]['name']
            gender = face_data[min_distance_index]['gender']
        else:
            name = 'Unknown'
            gender = 'Unknown'

        # Draw text label for the detected name and gender
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(rgb_frame, f'{name}, {gender}', (left, top-10), font, 0.8, (0, 255, 0), 2)
        cv2.imshow("Face recognition", rgb_frame)
        cv2.waitKey(1)

        '''

        unknown_face_encoding = face_recognition.face_encodings(rgb_frame, face_locations)

        if len(unknown_face_encoding) > 0:
            print("Face encoded")
            unknown_face_encoding = unknown_face_encoding[0]
            matches = face_recognition.compare_faces(known_faces, unknown_face_encoding)
            # Find the name and gender of the closest match, or use "Unknown" and the predicted gender
            name = "Unknown"
            if True in matches:
                print("Face recognized")
                index = matches.index(True)
                name = face_data[index]['name']
                gender = face_data[index]['gender']
                if gender == "male": 
                    gender_prediction = 0.0
                else:
                    gender_prediction = 1.0
            else:
                print("Face not recognized, assuming male")
                gender_prediction = 0.0
                # Resize the face image to match the input size of the gender detection model
                #resized_face_image = cv2.resize(face_image, (227, 227))
                # Convert the face image to the input format of the gender detection model
                #blob = cv2.dnn.blobFromImage(resized_face_image, scalefactor=1.0, size=(227, 227),
                #                            mean=(78.4263377603, 87.7689143744, 114.895847746), swapRB=False, crop=False)
                # Pass the face image through the gender detection model to predict the gender
                #gender_model.setInput(blob)
                #gender_predictions = gender_model.forward()
                # Male if < 0.5 otherwise female
                #gender_prediction = round(gender_predictions[0])

            # Calculate the bearing to the face
            face_center_x = (right + left) // 2
            bearing = -(face_center_x - center_x) / center_x
            angle = float(bearing * math.radians(cam_h_fov))
            gender="male" if gender_prediction==1.0 else "female"
            mem.storePerson(str(name), str(gender), float(bearing))
            print(name,gender,bearing)
        '''
except KeyboardInterrupt:
    # Release the video stream and close the window
    camera.close()
    cv2.destroyAllWindows()