# eye_overlay.py
# Contains visualization logic for rendering real-time eye openness indicators.
# Displays left/right eye as circles or lines in the video frame based on
# openness values and validity, with numerical values rendered below each eye.

import cv2

def draw_pupil(frame, diameter, position):
    """Draw a pupil overlay on the given frame."""
    radius = max(1, int(diameter * 11))
    center = (int(position[0]), int(position[1]))

    cv2.circle(frame, center, 70, (255, 255, 255), -1)
    cv2.circle(frame, center, radius, (0, 0, 0), -1)
    cv2.line(frame, (center[0], center[1] - radius), (center[0], center[1] + radius), (0, 150, 0), 1)
    cv2.line(frame, (center[0] - radius, center[1]), (center[0] + radius, center[1]), (0, 150, 0), 1)

    label = f"diameter: {diameter:.4f}"
    origin = (center[0] - 50, center[1] - 100)
    cv2.putText(frame, label, origin, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1, cv2.LINE_AA)