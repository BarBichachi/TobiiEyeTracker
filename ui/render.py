# render.py
# Contains reusable drawing utilities for gaze overlay, tracking indicators,
# attention prompts, and on-screen UI elements like buttons.

import cv2
from core import state, config

# ---------------------- Gaze Point ----------------------
def draw_gaze_point(frame):
    """Draws a green circle where the user's gaze is located."""
    cv2.circle(frame, (state.gaze_x, state.gaze_y), 25, (0, 255, 0), 2)


# ---------------------- Tracking Overlay ----------------------
def draw_tracking_overlay(frame, bbox, color):
    """Draws a bounding box around the tracked object and a line from gaze to target."""
    x, y, w, h = bbox
    cv2.rectangle(frame, (x, y), (x + w, y + h), color, 3)
    cv2.line(frame, (state.target_x, state.target_y), (state.gaze_x, state.gaze_y), (255, 255, 255), 2)


# ---------------------- Tracking Label ----------------------
def draw_tracking_label(frame, label):
    """Draws the current tracking mode label on the frame (e.g., User/Computer)."""
    cv2.putText(frame, **label)


# ---------------------- Attention Prompt ----------------------
def draw_attention_prompt(frame):
    """Displays a prompt asking if the user is still there after gaze timeout."""
    cv2.putText(frame, **config.ATTENTION_LABEL)


# ---------------------- Button Overlay ----------------------
def draw_button_overlay(frame):
    """Draws an interactive button and its label on the frame."""
    btn = config.BUTTON_RECT
    cv2.rectangle(
        frame,
        (btn["x"], btn["y"]),
        (btn["x"] + btn["w"], btn["y"] + btn["h"]),
        (100, 100, 255), 2
    )
    cv2.putText(frame, **config.BUTTON_LABEL)