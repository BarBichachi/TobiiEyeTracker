# trackbars.py
# OpenCV trackbars for live tuning of HSV segmentation and grayscale mode.

import cv2

from core import config


_TRACKBAR_WINDOW = "Trackbars"


# Updates HSV minimum hue threshold
def _on_hue_min(value):
    config.HUE_MIN = int(value)


# Updates HSV maximum hue threshold
def _on_hue_max(value):
    config.HUE_MAX = int(value)


# Updates HSV minimum saturation threshold
def _on_sat_min(value):
    config.SAT_MIN = int(value)


# Updates HSV maximum saturation threshold
def _on_sat_max(value):
    config.SAT_MAX = int(value)


# Updates HSV minimum value (brightness) threshold
def _on_val_min(value):
    config.VAL_MIN = int(value)


# Updates HSV maximum value (brightness) threshold
def _on_val_max(value):
    config.VAL_MAX = int(value)


# Toggles grayscale processing mode
def _on_grayscale_toggle(value):
    config.IS_GRAYSCALE = bool(value)


# Creates and initializes all OpenCV trackbars
def create_trackbars():
    cv2.namedWindow(_TRACKBAR_WINDOW, cv2.WINDOW_NORMAL)

    # Initial positions are seeded from config (the single source of truth for the tuned
    # mask); slider ranges are the full OpenCV HSV ranges.
    hue_max = config.HSV_HUE_RANGE_MAX
    sv_max = config.HSV_SV_RANGE_MAX
    cv2.createTrackbar("Hue Min", _TRACKBAR_WINDOW, config.HUE_MIN, hue_max, _on_hue_min)
    cv2.createTrackbar("Hue Max", _TRACKBAR_WINDOW, config.HUE_MAX, hue_max, _on_hue_max)

    cv2.createTrackbar("Sat Min", _TRACKBAR_WINDOW, config.SAT_MIN, sv_max, _on_sat_min)
    cv2.createTrackbar("Sat Max", _TRACKBAR_WINDOW, config.SAT_MAX, sv_max, _on_sat_max)

    cv2.createTrackbar("Val Min", _TRACKBAR_WINDOW, config.VAL_MIN, sv_max, _on_val_min)
    cv2.createTrackbar("Val Max", _TRACKBAR_WINDOW, config.VAL_MAX, sv_max, _on_val_max)

    cv2.createTrackbar("Grayscale", _TRACKBAR_WINDOW, int(config.IS_GRAYSCALE), 1, _on_grayscale_toggle)