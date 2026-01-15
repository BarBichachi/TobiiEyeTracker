# config.py
# Central configuration: algorithm thresholds, UI overlay styles, and asset paths used across the project.

from pathlib import Path
import cv2


# region Paths
# Project root inferred from this file location
PROJECT_ROOT = Path(__file__).resolve().parent.parent

ASSETS_DIR = PROJECT_ROOT / "assets"
SOUNDS_DIR = ASSETS_DIR / "sounds"
VIDEOS_DIR = ASSETS_DIR / "videos"
# endregion


# region HSV Threshold Defaults
# OpenCV HSV hue range is [0..179] for 8-bit images
HUE_MIN, HUE_MAX = 0, 179
SAT_MIN, SAT_MAX = 0, 255
VAL_MIN, VAL_MAX = 0, 255
IS_GRAYSCALE = False
# endregion


# region Gaze Thresholds
GAZE_TARGET_TOLERANCE = 250
GAZE_BUTTON_TOLERANCE = 50

X_THRESH = 25
Y_THRESH = 25
R_THRESH = (X_THRESH ** 2 + Y_THRESH ** 2) ** 0.5

GAZE_TIMEOUT_SECONDS = 3.0
BEEP_TIMEOUT_SECONDS = 5.0
BUTTON_DWELL_SECONDS = 1.0
BUTTON_PRESSED_COOLDOWN = 2.0

RIGHT_EYE_CLOSURE_SECONDS = 1.0
LEFT_EYE_CLOSURE_SECONDS = 1.0

FOCUS_STICKY_SECONDS = 0.25
MODE_SWITCH_COOLDOWN_S = 2.0

MIN_CONTOUR_AREA = 150
MAX_TARGETS_CONSIDERED = 5

MAX_REID_DIST_PX = 120
LATCH_STICKY_SECONDS = 0.2
# endregion


# region Kalman Filter Tuning
GAZE_PROCESS_NOISE_COV = 0.1
GAZE_MEASUREMENT_NOISE_COV = 50.0
# endregion


# region UI Overlay Styles
ATTENTION_LABEL = {
    "text": "Are you still here?",
    "org": (40, 80),
    "fontFace": cv2.FONT_HERSHEY_DUPLEX,
    "fontScale": 1,
    "color": (0, 0, 255),
    "thickness": 2,
    "lineType": cv2.LINE_AA,
}

TRACKING_MODE_LABEL = {
    "text": "Tracking mode: Computer",
    "org": (0, 0),
    "fontFace": cv2.FONT_HERSHEY_DUPLEX,
    "fontScale": 1,
    "color": (0, 0, 255),
    "thickness": 2,
    "lineType": cv2.LINE_AA,
}

TRACKING_LOCK_LABEL = {
    "text": "Tracking Lock: OFF",
    "org": (0, 0),
    "fontFace": cv2.FONT_HERSHEY_SIMPLEX,
    "fontScale": 1,
    "color": (255, 255, 0),
    "thickness": 2,
    "lineType": cv2.LINE_AA,
}

BUTTON_RECT = {"x": 270, "y": 20, "w": 250, "h": 50}

BUTTON_LABEL = {
    "text": "Cognitive Aid",
    "org": (300, 55),
    "fontFace": cv2.FONT_HERSHEY_SIMPLEX,
    "fontScale": 1,
    "color": (255, 0, 0),
    "thickness": 2,
    "lineType": cv2.LINE_AA,
}

BUTTON_PROGRESS_COLOR = (100, 200, 100)
# endregion


# region Asset Paths
USER_MODE_SOUND = SOUNDS_DIR / "user_mode.wav"
COMPUTER_MODE_SOUND = SOUNDS_DIR / "computer_mode.wav"
USER_NOT_HERE_SOUND = SOUNDS_DIR / "user_not_here.wav"
BUTTON_PRESSED_SOUND = SOUNDS_DIR / "button_pressed.wav"
TRACKING_LOCK_ENABLED_SOUND = SOUNDS_DIR / "tracking_lock_enabled.wav"
TRACKING_LOCK_DISABLED_SOUND = SOUNDS_DIR / "tracking_lock_disabled.wav"
COGNITIVE_AID_ENABLED_SOUND = SOUNDS_DIR / "cognitive_aid_enabled.wav"
COGNITIVE_AID_DISABLED_SOUND = SOUNDS_DIR / "cognitive_aid_disabled.wav"
SWITCHED_TARGET_SOUND = SOUNDS_DIR / "switched_target.wav"

DEFAULT_VIDEO = VIDEOS_DIR / "cloud_balls_black_60s.mp4"
# endregion