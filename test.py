import pygame
import streamlit as st
import face_recognition
import cv2
import numpy as np
import os

# Load known faces and their encodings
def load_known_faces(directory=r"C:\Users\othma\Documents\authorized"):
    known_face_encodings = []
    known_face_names = []
    for filename in os.listdir(directory):
        if filename.endswith(".jpg") or filename.endswith(".png") or filename.endswith(".jfif"):
            image = face_recognition.load_image_file(os.path.join(directory, filename))
            encoding = face_recognition.face_encodings(image)[0]
            known_face_encodings.append(encoding)
            known_face_names.append(os.path.splitext(filename)[0])
    return known_face_encodings, known_face_names

# Function to capture webcam frame
def capture_webcam():
    video_capture = cv2.VideoCapture(0)
    ret, frame = video_capture.read()
    video_capture.release()
    if not ret:
        st.error("Failed to capture image from webcam.")
        return None
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return frame_rgb

# Verify the captured image against known faces
def verify_face(known_face_encodings, known_face_names):
    captured_image = capture_webcam()
    if captured_image is None:
        return False, None
    face_locations = face_recognition.face_locations(captured_image)
    face_encodings = face_recognition.face_encodings(captured_image, face_locations)
    for face_encoding in face_encodings:
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
        best_match_index = np.argmin(face_distances)
        if matches[best_match_index]:
            return True, known_face_names[best_match_index]
    return False, None

# Main Streamlit application
def main():
    st.title("Face ID Authentication App")
    known_face_encodings, known_face_names = load_known_faces()
    if st.button("Login with Face ID"):
        authorized, name = verify_face(known_face_encodings, known_face_names)
        if authorized:
            st.success(f"Welcome, {name}!")
        else:
            st.error("Unauthorized access detected!")
            # Initialize pygame mixer and play alert sound
            pygame.mixer.init()
            pygame.mixer.music.load(r"C:\Users\othma\Downloads\siren-alert-96052.mp3")
            pygame.mixer.music.play()

if __name__ == "__main__":
    main()
