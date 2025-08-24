# render.py
# Contains reusable drawing utilities for gaze overlay, tracking indicators,
# attention prompts, and on-screen UI elements like buttons.

import cv2
from core import state, config, math_utils

# ---------------------- Gaze Point ----------------------
def draw_gaze_point(frame):
    """Draws a green circle where the user's gaze is located."""
    cv2.circle(frame, (state.gaze_x, state.gaze_y), 25, (0, 255, 0), 2)


# ---------------------- Tracking Overlay ----------------------
def draw_tracking_overlay(frame, bbox, color, line_target=None):
    """Draws a bounding box and (optionally) a tether line from gaze to target."""
    x, y, w, h = bbox

    # --- always draw the rectangle, with integer coordinates ---
    x1, y1 = int(x), int(y)
    x2, y2 = int(x + w), int(y + h)
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)

    # --- draw the tether only if both endpoints are finite ---
    tx, ty = (state.target_x, state.target_y) if line_target is None else line_target
    gx, gy = state.gaze_x, state.gaze_y
    if (math_utils.isfinite(tx) and math_utils.isfinite(ty)
            and math_utils.isfinite(gx) and math_utils.isfinite(gy)):
        cv2.line(frame, (int(tx), int(ty)), (int(gx), int(gy)), (255, 255, 255), 2)


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
        (255, 0, 0), 2
    )

    # Progress fill (0..1)
    p = state.current_button_progress
    if p > 0.0:
        fill_w = int(btn["w"] * max(0.0, min(1.0, p)))
        cv2.rectangle(
            frame,
            (btn["x"], btn["y"]),
            (btn["x"] + fill_w, btn["y"] + btn["h"]),
            config.BUTTON_PROGRESS_COLOR,
            thickness=-1
        )

    cv2.putText(frame, **config.BUTTON_LABEL)