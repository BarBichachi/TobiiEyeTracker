# eye_overlay.py
# Contains visualization logic for rendering real-time eye openness indicators.
# Displays left/right eye as circles or lines in the video frame based on
# openness values and validity, with numerical values rendered below each eye.

import cv2

def draw_pupil(frame, diameter, position):
    """Draws a pupil visualization:
    - Full drawing if diameter > 0.0
    - Just white circle + 'eye not detected' label otherwise"""
    x, y = int(position[0]), int(position[1])
    radius = max(1, int(diameter * 11))  # Ensure radius is at least 1 px

    # Always draw white sclera
    cv2.circle(frame, (x, y), 70, (255, 255, 255), -1)
    # Border around the circle (black)
    cv2.circle(frame, (x, y), 70, (0, 0, 0), 2)

    if diameter > 0.0:
        # Valid pupil: draw black circle and green cross
        cv2.circle(frame, (x, y), radius, (0, 0, 0), -1)
        cv2.line(frame, (x, y - radius), (x, y + radius), (0, 150, 0), 1)
        cv2.line(frame, (x - radius, y), (x + radius, y), (0, 150, 0), 1)
        label = f"diameter: {diameter:.4f}"
        color = (255, 0, 0)
    else:
        # Eye not detected
        label = "eye not detected"
        color = (0, 0, 255)

    # Label position
    origin = (x - 70, y - 100)
    cv2.putText(frame, label, origin, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)