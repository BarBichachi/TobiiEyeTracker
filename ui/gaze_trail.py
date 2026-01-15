# gaze_trail.py
# Renders a smooth fading gaze trail using a persistent decay buffer

import numpy as np
import cv2


class GazeTrail:
    # Creates a trail renderer with decay and blur settings
    def __init__(self, decay=0.90, sigma=10.0):
        self.decay = float(decay)
        self.sigma = float(sigma)
        self._buf = None  # uint8 HxW

    # Clears the internal buffer
    def reset(self):
        self._buf = None

    # Ensures the internal buffer matches the frame size
    def ensure_size(self, frame):
        h, w = frame.shape[:2]
        if self._buf is not None and self._buf.shape == (h, w):
            return
        self._buf = np.zeros((h, w), dtype=np.uint8)

    # Updates the trail buffer with decay and an optional gaze stamp
    def update(self, frame, gaze_x, gaze_y, valid):
        self.ensure_size(frame)

        if self.decay < 1.0:
            cv2.multiply(self._buf, self.decay, dst=self._buf)

        # Shrinks old trail slightly (morphological erosion)
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        self._buf = cv2.erode(self._buf, k, iterations=1)

        if not valid:
            return

        h, w = self._buf.shape
        x, y = int(gaze_x), int(gaze_y)
        if x < 0 or y < 0 or x >= w or y >= h:
            return

        r = max(2, int(self.sigma))  # sigma now acts as "radius"
        cv2.circle(self._buf, (x, y), r, 255, thickness=-1)

    # Draws the trail onto the frame efficiently
    def draw(self, frame):
        if self._buf is None:
            return
        if int(self._buf.max()) == 0:
            return

        g = frame[:, :, 1]
        frame[:, :, 1] = cv2.max(g, self._buf)