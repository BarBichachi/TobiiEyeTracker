import time
import math
import threading
from datetime import datetime
from pathlib import Path

import numpy as np
import cv2
from PySide6.QtWidgets import QApplication
import tobii_research as tr

import live_graphs

# ---------------------- Global Variables ----------------------
gaze_x, gaze_y = 0, 0
timestamp = 0
target_x, target_y = 0, 0

# HSV threshold defaults
hue_min, hue_max = 0, 255
sat_min, sat_max = 0, 255
val_min, val_max = 0, 255
is_grayscale = False

# Thresholds for entropy sensitivity
x_thresh = 25
y_thresh = 25
r_thresh = math.sqrt(x_thresh**2 + y_thresh**2)

# Text overlay (future use)
attention_text = {
    "text": "Are You still here?",
    "font": cv2.FONT_HERSHEY_SIMPLEX,
    "position": (120, 120),
    "scale": 1,
    "color": (0, 0, 255),
    "thickness": 4,
    "line_type": cv2.LINE_AA
}

# ---------------------- Gaze Callback ----------------------
def on_gaze_data(data):
    global gaze_x, gaze_y, timestamp

    now = datetime.now()
    timestamp = (
            now.hour * 3600_000 +
            now.minute * 60_000 +
            now.second * 1_000 +
            now.microsecond // 1_000
                ) / 1000

    lx, ly = data['left_gaze_point_on_display_area']
    rx, ry = data['right_gaze_point_on_display_area']
    gaze_x = int((lx + rx) / 2 * screen_width)
    gaze_y = int((ly + ry) / 2 * screen_height)

# ---------------------- Trackbar Handlers ----------------------
def on_trackbar_hue_min(val):   global hue_min; hue_min = val
def on_trackbar_hue_max(val):   global hue_max; hue_max = val
def on_trackbar_sat_min(val):   global sat_min; sat_min = val
def on_trackbar_sat_max(val):   global sat_max; sat_max = val
def on_trackbar_val_min(val):   global val_min; val_min = val
def on_trackbar_val_max(val):   global val_max; val_max = val
def on_trackbar_grayscale(val): global is_grayscale; is_grayscale = bool(val)

# ---------------------- Math Utilities ----------------------
def delta(a, b):
    return a - b

def distance(x1, y1, x2, y2):
    return math.hypot(delta(x1, x2), delta(y1, y2))

# ---------------------- Video Display Loop ----------------------
def show_video():
    global target_x, target_y
    paused = False

    cv2.namedWindow('Main Window', cv2.WINDOW_NORMAL)
    #cv2.setWindowProperty('Main Window', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    while True:
        if not paused:
            success, frame = cap.read()
            if not success:
                print("Warning: Frame read failed.")
                continue

        # HSV filter to isolate object
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower = np.array([hue_min, sat_min, val_min])
        upper = np.array([hue_max, sat_max, val_max])
        mask = cv2.inRange(hsv, lower, upper)

        # Draw gaze point
        cv2.circle(frame, (gaze_x, gaze_y), 25, (0, 255, 0), 2)

        # Find the largest contour and draw target
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest)
            target_x, target_y = x + w // 2, y + h // 2
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 3)
            cv2.line(frame, (target_x, target_y), (gaze_x, gaze_y), (255, 255, 255), 2)

        # Optional future: overlay text prompt
        # cv2.putText(frame, **attention_text)

        cv2.imshow('Main Window', frame)

        # Quit on 'Q', Pause/Resume on 'Space-bar'
        key = cv2.waitKey(wait_time) & 0xFF
        if key == ord(' '):
            paused = not paused
        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# ---------------------- Real-Time Graph Update ----------------------
def update_graph_data():
    delta_x = delta(gaze_x, target_x)
    delta_y = delta(gaze_y, target_y)
    delta_r = distance(gaze_x, gaze_y, target_x, target_y)

    entropy_x = math.log(abs(delta_x / x_thresh)) * np.sign(delta_x) if abs(delta_x) > x_thresh else 0
    entropy_y = math.log(abs(delta_y / y_thresh)) * np.sign(delta_y) if abs(delta_y) > y_thresh else 0
    entropy_r = math.log(delta_r / r_thresh) if delta_r > r_thresh else 0

    try:
        window.update_graphs([delta_x, delta_y, delta_r, entropy_x, entropy_y, entropy_r], timestamp)
    except Exception as e:
        print(f"Graph update error: {e}")

# ---------------------- Utility ----------------------
def run_periodically(interval, func):
    def runner():
        while True:
            func()
            time.sleep(interval)
    threading.Thread(target=runner, daemon=True).start()

# ---------------------- Main Execution ----------------------
if __name__ == '__main__':
    try:
        # Find and connect to the eye tracker
        eyetrackers = tr.find_all_eyetrackers()
        if not eyetrackers:
            raise RuntimeError("No eye tracker found")

        tracker = eyetrackers[0]
        tracker.subscribe_to(tr.EYETRACKER_GAZE_DATA, on_gaze_data, as_dictionary=True)

        print("Address:", tracker.address)
        print("Model:", tracker.model)
        print("Name:", tracker.device_name or "(Unnamed)")
        print("Serial number:", tracker.serial_number)

        # Load video
        cap = cv2.VideoCapture(str(Path('assets/videos/RocketWC.mp4')))
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        wait_time = int(1000 / video_fps) if video_fps > 0 else 33
        screen_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        screen_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

        # Create trackbars for HSV filtering
        cv2.namedWindow('Trackbar', cv2.WINDOW_NORMAL)
        cv2.createTrackbar('Hue Min',  'Trackbar', 0, hue_min, on_trackbar_hue_min)
        cv2.createTrackbar('Hue Max',  'Trackbar', 15, hue_max, on_trackbar_hue_max)
        cv2.createTrackbar('Sat Min',  'Trackbar', 0, sat_min, on_trackbar_sat_min)
        cv2.createTrackbar('Sat Max',  'Trackbar', 255, sat_max, on_trackbar_sat_max)
        cv2.createTrackbar('Val Min',  'Trackbar', 0, val_min, on_trackbar_val_min)
        cv2.createTrackbar('Val Max',  'Trackbar', 40, val_max, on_trackbar_val_max)
        cv2.createTrackbar('Grayscale', 'Trackbar', 0, 1, on_trackbar_grayscale)

        # Start video display thread
        threading.Thread(target=show_video, daemon=True).start()

        # Start graph GUI window
        app = QApplication([])
        window = live_graphs.LiveGraphs()
        window.show()

        # Periodically update graphs
        run_periodically(0.01, update_graph_data)
        app.exec()

    except Exception as e:
        print(f"Startup error: {e}")