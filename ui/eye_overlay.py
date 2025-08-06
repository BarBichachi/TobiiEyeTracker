# eye_overlay.py
# Contains visualization logic for rendering real-time eye openness indicators.
# Displays left/right eye as circles or lines in the video frame based on
# openness values and validity, with numerical values rendered below each eye.

import cv2

def draw_eye_openness_overlay(frame, eye_data, scale=1.0):
    """Draws eye openness visualization in the bottom-right corner of the frame.
    Circles = open, line = closed, X = not detected."""
    h, w, _ = frame.shape
    radius = int(20 * scale)
    spacing = int(80 * scale)
    base_x = w - int(2.5 * spacing)
    base_y = h - int(1.5 * spacing)
    font = cv2.FONT_HERSHEY_SIMPLEX

    def draw_eye(x, y, valid, openness, label):
        if not valid:
            # Draw an "X"
            cv2.line(frame, (x - radius, y - radius), (x + radius, y + radius), (0, 0, 255), 2)
            cv2.line(frame, (x - radius, y + radius), (x + radius, y - radius), (0, 0, 255), 2)
            text = f"{label}: N/A"
        elif openness < 0.2:
            # Closed eye - straight line
            cv2.line(frame, (x - radius, y), (x + radius, y), (0, 255, 255), 2)
            text = f"{label}: {openness:.2f}"
        else:
            # Open eye - circle
            cv2.circle(frame, (x, y), radius, (0, 255, 0), 2)
            text = f"{label}: {openness:.2f}"

        # Draw label below
        cv2.putText(frame, text, (x - radius, y + radius + 20),
                    font, 0.5 * scale, (255, 255, 255), 1, cv2.LINE_AA)

    # Draw left and right eyes
    draw_eye(base_x, base_y,
             eye_data.get("left_eye_validity", False),
             eye_data.get("left_eye_openness_value", 0.0),
             "Left")

    draw_eye(base_x + spacing, base_y,
             eye_data.get("right_eye_validity", False),
             eye_data.get("right_eye_openness_value", 0.0),
             "Right")
