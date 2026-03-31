import face_recognition
import cv2
import os

def load_known_faces(known_faces_dir):
    known_encodings = []
    known_names = []

    for filename in os.listdir(known_faces_dir):
        if filename.lower().endswith((".jpg", ".png", ".jpeg")):
            path = os.path.join(known_faces_dir, filename)
            img = face_recognition.load_image_file(path)
            encodings = face_recognition.face_encodings(img)
            if encodings:  # Avoid crash if no face found
                encoding = encodings[0]
                known_encodings.append(encoding)
                known_names.append(os.path.splitext(filename)[0])
            else:
                print(f"[WARN] No face found in {filename}, skipping...")
    return known_encodings, known_names

def recognize_faces(frame, known_encodings, known_names):
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    face_names = []
    for encoding in face_encodings:
        matches = face_recognition.compare_faces(known_encodings, encoding)
        name = "Unknown"

        if True in matches:
            first_match_index = matches.index(True)
            name = known_names[first_match_index]

        face_names.append(name)
    return face_locations, face_names
