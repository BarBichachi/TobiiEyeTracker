# math_utils.py
# Basic reusable math operations used across gaze, entropy, and distance calculations.

import math

def delta(a, b):
    return a - b

def distance(x1, y1, x2, y2):
    return math.hypot(delta(x1, x2), delta(y1, y2))

def safe_average(a, b):
    if math.isnan(a) and math.isnan(b):
        return None
    elif math.isnan(a):
        return b
    elif math.isnan(b):
        return a
    return (a + b) / 2

def isfinite(x): return isinstance(x, (int, float)) and math.isfinite(x)