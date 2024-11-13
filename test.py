import pygame
import streamlit as st
import face_recognition
import cv2
import numpy as np
import os
from datetime import datetime
import pandas as pd
import time

AUTHORIZED_DIR = r"C:\Users\othma\Documents\presence\authorized"
UNAUTHORIZED_DIR = r"C:\Users\othma\Documents\presence\unauthorized"
ALERT_SOUND_PATH = r"C:\Users\othma\Downloads\siren-alert-96052.mp3"
EXCEL_LOG_FILE = r"C:\Users\othma\Documents\presence\presence_log.xlsx"

# Load known faces and their encodings
def load_known_faces(directory=AUTHORIZED_DIR):
    known_face_encodings = []
    known_face_names = []
    for filename in os.listdir(directory):
        if filename.endswith((".jpg", ".png", ".jfif")):
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
def verify_face(known_face_encodings, known_face_names, unauthorized_attempts):
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

    # If no match found, increase unauthorized attempts
    unauthorized_attempts += 1
    save_unauthorized_access(captured_image, unauthorized_attempts)
    return False, None

# Save authorized access to an Excel file
def save_authorized_access(name):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = pd.DataFrame({
        "Name": [name],
        "Status": ["Authorized"],
        "Timestamp": [timestamp],
        "Attempts": [1]
    })
    save_to_excel(log_entry)

# Save unauthorized access to an Excel file
def save_unauthorized_access(image, attempt_count):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    os.makedirs(UNAUTHORIZED_DIR, exist_ok=True)
    image_filename = os.path.join(UNAUTHORIZED_DIR, f"unauthorized_{timestamp}.png")
    cv2.imwrite(image_filename, cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
    
    log_entry = pd.DataFrame({
        "Name": ["Unknown"],
        "Status": ["Unauthorized"],
        "Timestamp": [timestamp],
        "Attempts": [attempt_count],
        "Image File": [image_filename]
    })
    save_to_excel(log_entry)

# Helper function to save entries to an Excel file with retry on PermissionError
def save_to_excel(data, retry_attempts=3):
    for attempt in range(retry_attempts):
        try:
            if os.path.exists(EXCEL_LOG_FILE):
                with pd.ExcelWriter(EXCEL_LOG_FILE, mode='a', engine='openpyxl', if_sheet_exists="overlay") as writer:
                    data.to_excel(writer, index=False, header=False, startrow=writer.sheets["Sheet1"].max_row)
            else:
                data.to_excel(EXCEL_LOG_FILE, index=False)
            break  # Exit the loop if successful
        except PermissionError as e:
            st.warning(f"Permission denied for {EXCEL_LOG_FILE}. Retrying...")
            time.sleep(1)  # Wait for 1 second before retrying
            if attempt == retry_attempts - 1:
                st.error("Could not access the log file after multiple attempts.")
                raise e

# Main Streamlit application
def main():
    st.title("Presence Marker with Face Recognition")

    # Load known face encodings and names
    known_face_encodings, known_face_names = load_known_faces()

    # Counter for unauthorized attempts
    unauthorized_attempts = 0

    if st.button("Attempt Access"):
        authorized, name = verify_face(known_face_encodings, known_face_names, unauthorized_attempts)
        
        if authorized:
            st.success(f"Welcome, {name}! Access granted.")
            save_authorized_access(name)  # Record authorized access
        else:
            st.error("Unauthorized access detected!")
            unauthorized_attempts += 1  # Increment attempt count
            
            # Play alert sound for unauthorized access
            pygame.mixer.init()
            pygame.mixer.music.load(ALERT_SOUND_PATH)
            pygame.mixer.music.play()

if __name__ == "__main__":
    main()
