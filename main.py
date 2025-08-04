import time
import math
import threading
from datetime import datetime
from pathlib import Path

import numpy as np
import cv2
from PyQt5.QtWidgets import QApplication
import tobii_research as tr
from playsound import playsound

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

# Gaze lost control
attention_label = {
    "text": "Are you still here?",
    "org": (40, 80),
    "fontFace": cv2.FONT_HERSHEY_DUPLEX,
    "fontScale": 2,
    "color": (0, 0, 255),
    "thickness": 2,
    "lineType": cv2.LINE_AA
}
last_gaze_time = time.time()
gaze_lost = False
gaze_timeout_seconds = 2

# User tracking state
user_is_tracking = False
gaze_tolerance = 50  # pixels
current_gaze_mode = None
last_user_not_here_beep_time = 0

# Tracking label
tracking_label = {
    "text": "Tracking mode: Computer",
    "org": (0, 0),
    "fontFace": cv2.FONT_HERSHEY_DUPLEX,
    "fontScale": 1,
    "color": (0, 0, 255),
    "thickness": 2,
    "lineType": cv2.LINE_AA
}

# Button for example
button_rect = {
    "x": 270,
    "y": 20,
    "w": 200,
    "h": 50
}
button_label = {
    "text": "Press Me",
    "font": cv2.FONT_HERSHEY_SIMPLEX,
    "position": (button_rect["x"] + 30, button_rect["y"] + 35),
    "scale": 1,
    "color": (255, 255, 255),
    "thickness": 2
}
button_pressed_cooldown = 2.0
last_button_press_time = 0

# Sound paths
USER_MODE_SOUND = "assets/sounds/user_mode.wav"
COMPUTER_MODE_SOUND = "assets/sounds/computer_mode.wav"
USER_NOT_HERE_SOUND = "assets/sounds/user_not_here.wav"
BUTTON_PRESSED_SOUND = "assets/button_pressed.wav"

# ---------------------- Play sound ----------------------
def play_user_mode_sound():
    playsound(USER_MODE_SOUND, block=False)

def play_computer_mode_sound():
    playsound(COMPUTER_MODE_SOUND, block=False)

def play_user_not_here_sound():
    playsound(USER_NOT_HERE_SOUND, block=False)

def play_button_pressed_sound():
    playsound("beeps/button_pressed.wav", block=False)


# ---------------------- Gaze Callback ----------------------
def on_gaze_data(data):
    global gaze_x, gaze_y, timestamp, last_gaze_time, gaze_lost

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
    last_gaze_time = time.time()
    gaze_lost = False


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
    global target_x, target_y, last_gaze_time, gaze_lost, user_is_tracking, current_gaze_mode, last_user_not_here_beep_time, last_button_press_time
    paused = False

    cv2.namedWindow('Main Window', cv2.WINDOW_NORMAL)
    #cv2.setWindowProperty('Main Window', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    while True:
        if not paused:
            success, frame = cap.read()
            if not success:
                print("Warning: Frame read failed.")
                continue

        current_time = time.time()

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

            # Check if user is tracking the object
            if distance(gaze_x, gaze_y, target_x, target_y) < gaze_tolerance:
                user_is_tracking = True
                last_gaze_time = time.time()
                gaze_lost = False
            else:
                user_is_tracking = False

            # Draw tracking rectangle based on gaze status
            if user_is_tracking:
                if current_gaze_mode != "user":
                    play_user_mode_sound()
                    current_gaze_mode = "user"

                tracking_label["text"] = "Tracking mode: User"
                tracking_label["color"] = (0, 255, 0)

                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)  # green
                cv2.line(frame, (target_x, target_y), (gaze_x, gaze_y), (255, 255, 255), 2)

            else:
                if current_gaze_mode != "computer":
                    play_computer_mode_sound()
                    current_gaze_mode = "computer"

                tracking_label["text"] = "Tracking mode: Computer"
                tracking_label["color"] = (0, 0, 255)

                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 3)  # red

            # Check if user is gazing at the button
            if (button_rect["x"] <= gaze_x <= button_rect["x"] + button_rect["w"] and
                    button_rect["y"] <= gaze_y <= button_rect["y"] + button_rect["h"]):

                if current_time - last_button_press_time > button_pressed_cooldown:
                    play_button_pressed_sound()
                    last_button_press_time = time.time()

        cv2.putText(frame, **tracking_label)

        # Show attention text if gaze lost for >3s
        if current_time - last_gaze_time > gaze_timeout_seconds:
            cv2.putText(frame, **attention_label)

            # Beep every 2 seconds when user is not here
            if current_time - last_user_not_here_beep_time > 2:
                play_user_not_here_sound()
                last_user_not_here_beep_time = current_time

        cv2.rectangle(frame,
            (button_rect["x"], button_rect["y"]),
            (button_rect["x"] + button_rect["w"], button_rect["y"] + button_rect["h"]),
            (100, 100, 255), 2)
        cv2.putText(frame, **button_label)

        cv2.imshow('Main Window', frame)

        # Quit on 'Q', Pause/Resume on 'Space-bar'
        key = cv2.waitKey(wait_time) & 0xFF
        if key == ord(' '):
            paused = not paused
        elif key == ord('q'):
            app.quit()
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
        tracking_label["org"] = (int(screen_width // 2) - 180, 50)

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