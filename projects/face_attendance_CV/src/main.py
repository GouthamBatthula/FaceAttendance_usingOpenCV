# Updated main.py - Improved Attendance System Logic

import cv2
import csv
import os
import time
from datetime import datetime
from face_utils import load_known_faces, recognize_faces

# --- Configuration ---
# Base project directory (one level above src)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
KNOWN_FACES_DIR = os.path.join(BASE_DIR, "data", "known_faces")
CSV_FILE = os.path.join(BASE_DIR, "data", "attendance.csv")

# A grace period in seconds to handle temporary absences (e.g., blinking, turning head)
PRESENCE_GRACE_PERIOD = 5.0

# Define how long the program should run in seconds. Set to None to run indefinitely.
RUN_DURATION = 60.0  # e.g., 60.0 for one minute

# --- Data Loading and CSV Setup ---
# Load known faces from the 'known_faces' directory
known_encodings, known_names = load_known_faces(KNOWN_FACES_DIR)

# Write date header & column headers if the file does not exist or it's a new day
today_str = datetime.now().strftime("Date: %d-%b-%Y, %A")
if not os.path.exists(CSV_FILE) or (
    os.path.exists(CSV_FILE) and open(CSV_FILE, "r").readline().strip() != today_str
):
    with open(CSV_FILE, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([today_str])  # Date header
        writer.writerow(["Name", "Start Time (s)", "End Time (s)", "Duration (s)"])  # Column headers

# Track states for each person with more detailed information
person_states = {}  # {name: {"start_time": float, "last_seen_time": float}}

# Open webcam
video = cv2.VideoCapture(0)
program_start_time = time.time()

print(f"Attendance system started. Running for {RUN_DURATION} seconds. Press 'q' to quit early.")

# --- Main Video Processing Loop ---
# Check if a specific run duration is set
run_until_time = program_start_time + RUN_DURATION if RUN_DURATION is not None else None

while True:
    ret, frame = video.read()
    if not ret:
        print("Error: Could not read frame from webcam.")
        break

    # Check if the run duration has been exceeded
    if run_until_time is not None and time.time() > run_until_time:
        print("Run duration exceeded. Shutting down automatically.")
        break

    # Get face locations and names for the current frame
    face_locations, names = recognize_faces(frame, known_encodings, known_names)

    current_time = time.time()
    detected_set = set(names)

    # Update states for people currently detected
    for name in detected_set:
        if name not in person_states:
            # First time seeing this person, log their start time
            person_states[name] = {
                "start_time": current_time - program_start_time,
                "last_seen_time": current_time
            }
        else:
            # Person is still present, just update their last seen time
            person_states[name]["last_seen_time"] = current_time

    # Check for people who are no longer detected and log them
    names_to_remove = []
    for name, state in person_states.items():
        if name not in detected_set:
            # Check if they have been absent for longer than the grace period
            if (current_time - state["last_seen_time"]) > PRESENCE_GRACE_PERIOD:
                end_time = state["last_seen_time"] - program_start_time
                duration = round(end_time - state["start_time"], 2)

                # Log the single "Present" entry to the CSV
                with open(CSV_FILE, mode="a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        name,
                        round(state["start_time"], 2),
                        round(end_time, 2),
                        duration
                    ])

                # Mark for removal from state tracking
                names_to_remove.append(name)

    # Clean up the state dictionary
    for name in names_to_remove:
        del person_states[name]

    # Draw boxes and names on the video frame
    for (top, right, bottom, left), name in zip(face_locations, names):
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)

    # Display the resulting frame
    cv2.imshow("Attendance System", frame)

    # Break the loop on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("User pressed 'q'. Shutting down.")
        break

# --- Final Logging on Program Exit ---
program_end_time = time.time()
with open(CSV_FILE, mode="a", newline="") as f:
    writer = csv.writer(f)
    # Log any remaining people who were still present when the program was closed
    for name, state in person_states.items():
        # Their end time is when the program was closed
        end_time = program_end_time - program_start_time
        duration = round(end_time - state["start_time"], 2)
        writer.writerow([
            name,
            round(state["start_time"], 2),
            round(end_time, 2),
            duration
        ])

# Release resources
video.release()
cv2.destroyAllWindows()
print("Attendance system shut down.")
