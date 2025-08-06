# config.py
# Centralized constants, thresholds, and asset paths used throughout the project.
# This includes HSV filters, gaze tolerance, sound paths, and UI text defaults.

from pathlib import Path
import cv2

# ---------------------- HSV Threshold Defaults ----------------------
HUE_MIN, HUE_MAX = 0, 255
SAT_MIN, SAT_MAX = 0, 255
VAL_MIN, VAL_MAX = 0, 255
IS_GRAYSCALE = False

# ---------------------- Gaze Thresholds ----------------------
GAZE_TOLERANCE = 50
X_THRESH = 25
Y_THRESH = 25
R_THRESH = (X_THRESH ** 2 + Y_THRESH ** 2) ** 0.5
GAZE_TIMEOUT_SECONDS = 3
BEEP_TIMEOUT_SECONDS = 5

# ---------------------- Attention Label ----------------------
ATTENTION_LABEL = {
    "text": "Are you still here?",
    "org": (40, 80),
    "fontFace": cv2.FONT_HERSHEY_DUPLEX,
    "fontScale": 2,
    "color": (0, 0, 255),
    "thickness": 2,
    "lineType": cv2.LINE_AA,
}

# ---------------------- Tracking Label ----------------------
TRACKING_MODE_LABEL = {
    "text": "Tracking mode: Computer",
    "org": (0, 0),
    "fontFace": cv2.FONT_HERSHEY_DUPLEX,
    "fontScale": 1,
    "color": (0, 0, 255),
    "thickness": 2,
    "lineType": cv2.LINE_AA,
}

# ---------------------- Virtual Button ----------------------
BUTTON_RECT = {
    "x": 270,
    "y": 20,
    "w": 200,
    "h": 50
}
BUTTON_LABEL = {
    "text": "Press Me",
    "org": (300, 55),
    "fontFace": cv2.FONT_HERSHEY_SIMPLEX,
    "fontScale": 1,
    "color": (255, 0, 0),
    "thickness": 2,
    "lineType": cv2.LINE_AA
}
BUTTON_PRESSED_COOLDOWN = 2.0

# ---------------------- Asset Paths ----------------------
USER_MODE_SOUND = Path("assets/sounds/user_mode.wav")
COMPUTER_MODE_SOUND = Path("assets/sounds/computer_mode.wav")
USER_NOT_HERE_SOUND = Path("assets/sounds/user_not_here.wav")
BUTTON_PRESSED_SOUND = Path("assets/sounds/button_pressed.wav")
DEFAULT_VIDEO = Path("assets/videos/RocketWC.mp4")