# render.py
# Drawing utilities for gaze overlays, tracking indicators, attention prompts, and on-screen UI widgets.

import cv2

from core import config, math_utils, state


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
