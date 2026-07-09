import cv2
import os
import time
import pandas as pd
from datetime import datetime
import subprocess
import threading

from detection.detection import AnimalDetector
from distance.distance import measure_distance, cleanup_gpio
from alert.alert import speak_alert
from behavior.tracker import CentroidTrack, match_single_object
from behavior.behavior import predict_behavior
from lowlight.lowlight import pir_triggered
from lowlight.lowlight import is_night
from location_tracker.location_tracker import get_current_location, app as location_app

# ---------------- PATH SETUP ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(BASE_DIR, "events", "images")
LOG_DIR = os.path.join(BASE_DIR, "events", "logs")
LOG_FILE = os.path.join(LOG_DIR, "events.csv")

os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# ---------------- CREATE CSV ----------------
if not os.path.exists(LOG_FILE):
    df = pd.DataFrame(columns=[
        "timestamp",
        "animal",
        "snapshot",
        "distance",
        "proximity",
        "behavior", 
        "alert_message",
        "location"
    ])
    df.to_csv(LOG_FILE, index=False)

# ---------------- INIT DETECTOR ----------------
detector = AnimalDetector("best.pt")

# ---------------- TRACKER INIT ----------------
trackers = {}  # one tracker per animal
frame_idx = 0

# ---------------- CAMERA ----------------
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

if not cap.isOpened():
    print("Camera not working")
    exit()

# -------- START LOCATION SERVER --------
threading.Thread(
    target=lambda: location_app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False),
    daemon=True
).start()

# ---------------- SYNC SETTINGS ----------------
PYTHON_PATH = "/home/ideators/smart_surveillance/venv/bin/python3"
SYNC_SCRIPT = "/home/ideators/smart_surveillance/sync.py"
SYNC_INTERVAL = 300  # every 5 minutes
last_sync_time = 0

print("Detection system running...")

try:
    while True:
        cap.grab()
        ret, frame = cap.read()
        if not ret:
            continue

        # -------- preprocessing --------
        frame = cv2.resize(frame, (640, 480))
        frame_idx += 1

        night = is_night(frame)
        motion = pir_triggered()


        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        brightness = hsv[:, :, 2].mean()

        # Apply equalization ONLY in low light
        if brightness < 60:
            hsv[:, :, 2] = cv2.equalizeHist(hsv[:, :, 2])

        frame = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)


        # -------- detection --------
        if night and motion:
            conf_threshold = 0.5
            print("🌙 PIR motion at night → High priority detection")

            # 🔁 Confirm detection over next 5 frames
            for _ in range(5):
                ret, frame = cap.read()
                if not ret:
                    continue

                frame = cv2.resize(frame, (640, 480))
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                brightness = hsv[:, :, 2].mean()
                if brightness < 50:
                    hsv[:, :, 2] = cv2.equalizeHist(hsv[:, :, 2])
                frame = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

                detected, animal, box = detector.detect(frame, conf_threshold)

                if detected:
                    time_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    behavior_label = "UNKNOWN"

                    if box is not None:
                        x1, y1, x2, y2 = box
                        cx = int((x1 + x2) / 2)
                        cy = int((y1 + y2) / 2)

                        if animal not in trackers:
                            trackers[animal] = CentroidTrack(maxlen=15)
                        track = trackers[animal]

                        if match_single_object(track, cx, cy, max_dist=120):
                            track.update(cx, cy, box, frame_idx)

                        direction = track.get_direction_label()
                        speed = track.get_speed_px_per_frame()
                        behavior_label = predict_behavior(animal, direction, speed)

                    image_name = f"{animal}_{time_str}.jpg"
                    image_path = os.path.join(IMAGE_DIR, image_name)
                    cv2.imwrite(image_path, frame)

                    print(f"✅ Confirmed night detection: {animal}")
                    print(f"Behavior: {behavior_label}")

                    distance_value, proximity_level = measure_distance()
                    print(f"Distance: {distance_value}")
                    print(f"Proximity: {proximity_level}")

                    alert = speak_alert(animal, proximity_level, behavior_label)
                    print("Voice alert generated.")

                    log_row = pd.DataFrame([{
                        "timestamp": time_str,
                        "animal": animal,
                        "snapshot": image_path,
                        "distance": round(distance_value, 2) if distance_value else "No Echo",
                        "proximity": proximity_level,
                        "behavior": behavior_label,
                        "alert_message": alert,
                        "location": get_current_location()
                    }])
                    log_row.to_csv(LOG_FILE, mode="a", header=False, index=False)
                    print("Event logged")

                    time.sleep(25)  # prevent rapid night re-detection
                    break  # stop the 5-frame loop

        else:  # daytime or normal detection
            conf_threshold = 0.6
            
            detected, animal, box = detector.detect(frame, conf_threshold)
            if detected:
                time_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                behavior_label = "UNKNOWN"

                if box is not None:
                    x1, y1, x2, y2 = box
                    cx = int((x1 + x2) / 2)
                    cy = int((y1 + y2) / 2)

                    if animal not in trackers:
                        trackers[animal] = CentroidTrack(maxlen=15)
                    track = trackers[animal]

                    if match_single_object(track, cx, cy, max_dist=120):
                        track.update(cx, cy, box, frame_idx)

                    direction = track.get_direction_label()
                    speed = track.get_speed_px_per_frame()
                    behavior_label = predict_behavior(animal, direction, speed)

                image_name = f"{animal}_{time_str}.jpg"
                image_path = os.path.join(IMAGE_DIR, image_name)
                cv2.imwrite(image_path, frame)

                print(f"Day detection: {animal}")
                print(f"Behavior: {behavior_label}")

                distance_value, proximity_level = measure_distance()
                print(f"Distance: {distance_value}")
                print(f"Proximity: {proximity_level}")

                alert = speak_alert(animal, proximity_level, behavior_label)
                print("Voice alert generated.")

                log_row = pd.DataFrame([{
                    "timestamp": time_str,
                    "animal": animal,
                    "snapshot": image_path,
                    "distance": round(distance_value, 2) if distance_value else "No Echo",
                    "proximity": proximity_level,
                    "behavior": behavior_label,
                    "alert_message": alert,
                    "location": get_current_location()
                }])
                log_row.to_csv(LOG_FILE, mode="a", header=False, index=False)
                print("Event logged")

                time.sleep(25)  # prevent rapid day re-detection

        time.sleep(0.03)

        # -------- PERIODIC SYNC --------
        current_time = time.time()
        if current_time - last_sync_time > SYNC_INTERVAL:
            subprocess.Popen([PYTHON_PATH, SYNC_SCRIPT])
            print("🔄 Sync script launched in background")
            last_sync_time = current_time

except KeyboardInterrupt:
    print("Stopped by user")

finally:
    cap.release()
    cleanup_gpio()
    print("Camera and GPIO released")