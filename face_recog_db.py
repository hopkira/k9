import face_recognition
import os

# The folder containing the images
images_folder = "images"

# The database file
database_file = "database.txt"

# Load the images and their names
images = []
names = []
for file_name in os.listdir(images_folder):
    image = face_recognition.load_image_file(os.path.join(images_folder, file_name))
    encoding = face_recognition.face_encodings(image)[0]
    images.append(encoding)
    names.append(file_name[:-4]) # Remove the file extension from the name

# Write the database to file
with open(database_file, "w") as f:
    for i in range(len(images)):
        f.write(names[i] + " " + str(list(images[i])) + "\n")