# trackbars.py
# OpenCV trackbar handlers for HSV and grayscale filtering thresholds.
# These update shared config values in real-time for object segmentation.

import core.config as config
import cv2

# ---------------------- Trackbar Handlers ----------------------
def on_trackbar_hue_min(val):   config.HUE_MIN = val
def on_trackbar_hue_max(val):   config.HUE_MAX = val
def on_trackbar_sat_min(val):   config.SAT_MIN = val
def on_trackbar_sat_max(val):   config.SAT_MAX = val
def on_trackbar_val_min(val):   config.VAL_MIN = val
def on_trackbar_val_max(val):   config.VAL_MAX = val
def on_trackbar_grayscale(val): config.IS_GRAYSCALE = bool(val)

# ---------------------- Trackbar Setup ----------------------
def create_trackbars():
    cv2.namedWindow('Trackbar', cv2.WINDOW_NORMAL)

    cv2.createTrackbar('Hue Min',   'Trackbar',  0, config.HUE_MAX,  on_trackbar_hue_min)
    cv2.createTrackbar('Hue Max',   'Trackbar', 15, config.HUE_MAX,  on_trackbar_hue_max)
    cv2.createTrackbar('Sat Min',   'Trackbar',  0, config.SAT_MAX,  on_trackbar_sat_min)
    cv2.createTrackbar('Sat Max',   'Trackbar', 255, config.SAT_MAX, on_trackbar_sat_max)
    cv2.createTrackbar('Val Min',   'Trackbar',  0, config.VAL_MAX,  on_trackbar_val_min)
    cv2.createTrackbar('Val Max',   'Trackbar', 40, config.VAL_MAX,  on_trackbar_val_max)
    cv2.createTrackbar('Grayscale', 'Trackbar',  0, 1,         on_trackbar_grayscale)