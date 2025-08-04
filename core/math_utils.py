# math_utils.py
# Basic reusable math operations used across gaze, entropy, and distance calculations.

import math

def delta(a, b):
    return a - b

def distance(x1, y1, x2, y2):
    return math.hypot(delta(x1, x2), delta(y1, y2))
