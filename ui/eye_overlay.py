# eye_overlay.py
# Renders pupil / eye openness indicators on top of a video frame.

import math

import cv2


_SCLERA_RADIUS_PX = 70
_PUPIL_SCALE_PX_PER_MM = 11
_PUPIL_MIN_RADIUS_PX = 1
_PUPIL_MAX_RADIUS_PX = 35


# Draws a pupil indicator at a fixed position based on the measured diameter
def draw_pupil(frame, diameter, position):
    x, y = int(position[0]), int(position[1])

    cv2.circle(frame, (x, y), _SCLERA_RADIUS_PX, (255, 255, 255), -1)
    cv2.circle(frame, (x, y), _SCLERA_RADIUS_PX, (0, 0, 0), 2)

    d = _valid_diameter_or_none(diameter)
    if d is None:
        _draw_eye_label(frame, x, y, "eye not detected", (0, 0, 255))
        return

    radius = int(d * _PUPIL_SCALE_PX_PER_MM)
    radius = max(_PUPIL_MIN_RADIUS_PX, min(_PUPIL_MAX_RADIUS_PX, radius))

    cv2.circle(frame, (x, y), radius, (0, 0, 0), -1)
    cv2.line(frame, (x, y - radius), (x, y + radius), (0, 150, 0), 1)
    cv2.line(frame, (x - radius, y), (x + radius, y), (0, 150, 0), 1)

    _draw_eye_label(frame, x, y, f"diameter: {d:.4f}", (255, 0, 0))


# Returns a diameter float when valid, else None
def _valid_diameter_or_none(diameter):
    if not isinstance(diameter, (int, float)):
        return None
    if not math.isfinite(diameter):
        return None
    if diameter <= 0.0:
        return None
    return float(diameter)


# Draws a small label above the pupil indicator
def _draw_eye_label(frame, x, y, text, color):
    origin = (x - _SCLERA_RADIUS_PX, y - _SCLERA_RADIUS_PX - 30)
    cv2.putText(frame, str(text), origin, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)
