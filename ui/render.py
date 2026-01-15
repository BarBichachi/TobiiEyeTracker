# render.py
# Drawing utilities for gaze overlays, tracking indicators, attention prompts, and on-screen UI widgets.
import time
import cv2

from core import config, entropy, math_utils, state
from ui.gaze_trail import GazeTrail

_entropy_tracker = entropy.EntropyTracker(window_s=1.5, min_samples=5)
_gaze_trail = GazeTrail(decay=0.98, sigma=25.0)


# Draws a gaze marker at the current gaze position (if valid)
def draw_gaze_point(frame, radius=25, color=(0, 255, 0), thickness=2):
    gx, gy = state.gaze_x, state.gaze_y
    if not (math_utils.isfinite(gx) and math_utils.isfinite(gy)):
        return

    cv2.circle(frame, (int(gx), int(gy)), int(radius), color, int(thickness))


# Draws a bounding box and optional tether line from gaze to target
def draw_tracking_overlay(frame, bbox, color, line_target=None, thickness=3, tether_color=(255, 255, 255), tether_thickness=2):
    x, y, w, h = bbox
    x1, y1 = int(x), int(y)
    x2, y2 = int(x + w), int(y + h)

    cv2.rectangle(frame, (x1, y1), (x2, y2), color, int(thickness))

    tx, ty = (state.target_x, state.target_y) if line_target is None else line_target
    gx, gy = state.gaze_x, state.gaze_y

    if not (math_utils.isfinite(tx) and math_utils.isfinite(ty) and math_utils.isfinite(gx) and math_utils.isfinite(gy)):
        return

    cv2.line(frame, (int(tx), int(ty)), (int(gx), int(gy)), tether_color, int(tether_thickness))


# Draws a configured OpenCV text label dict onto the frame
def draw_label(frame, label):
    text = label.get("text", "")
    org = label.get("org", (0, 0))
    font_face = label.get("fontFace", cv2.FONT_HERSHEY_SIMPLEX)
    font_scale = label.get("fontScale", 1.0)
    color = label.get("color", (255, 255, 255))
    thickness = label.get("thickness", 2)
    line_type = label.get("lineType", cv2.LINE_AA)

    cv2.putText(frame, str(text), tuple(org), font_face, float(font_scale), tuple(color), int(thickness), line_type)


# Draws the attention prompt label
def draw_attention_prompt(frame):
    draw_label(frame, config.ATTENTION_LABEL)


# Draws the interactive button widget and its fill progress
def draw_button_overlay(frame):
    btn = config.BUTTON_RECT
    x, y, w, h = int(btn["x"]), int(btn["y"]), int(btn["w"]), int(btn["h"])

    cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

    p = float(state.current_button_progress or 0.0)
    if p > 0.0:
        fill_w = int(w * max(0.0, min(1.0, p)))
        cv2.rectangle(frame, (x, y), (x + fill_w, y + h), config.BUTTON_PROGRESS_COLOR, thickness=-1)

    draw_label(frame, config.BUTTON_LABEL)


# Draws a smooth gaze trail and a live entropy label based on gaze error vs target
def draw_gaze_trail_and_entropy(frame):
    now_t = time.perf_counter()

    gx, gy = state.gaze_x, state.gaze_y
    tx, ty = state.target_x, state.target_y

    valid_gaze = math_utils.isfinite(gx) and math_utils.isfinite(gy)
    valid_target = math_utils.isfinite(tx) and math_utils.isfinite(ty)

    _entropy_tracker.add_sample(gx if valid_gaze else 0.0, gy if valid_gaze else 0.0, valid_gaze, tx if valid_target else None, ty if valid_target else None, t=now_t)

    _gaze_trail.update(frame, gx, gy, valid_gaze)
    _gaze_trail.draw(frame)

    c = _entropy_tracker.get_error_entropy(grid=16, t=now_t)
    text = f"Consistency: {1.0 - c:.2f}" if c is not None else "Consistency: --"

    cv2.putText(frame, text, (14, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)