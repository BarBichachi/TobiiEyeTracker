# math_utils.py
# Small, defensive math helpers used across gaze processing, distance checks, and entropy calculations.

import math


# Returns a - b, or None if inputs are not finite numbers
def delta(a, b):
    if not isfinite(a) or not isfinite(b):
        return None
    return a - b


# Returns Euclidean distance between two points, or None if any input is invalid
def distance(x1, y1, x2, y2):
    if not all(isfinite(v) for v in (x1, y1, x2, y2)):
        return None
    return math.hypot(x1 - x2, y1 - y2)


# Returns the average of two values, ignoring invalid inputs
def safe_average(a, b):
    a_valid = isfinite(a)
    b_valid = isfinite(b)

    if not a_valid and not b_valid:
        return None
    if not a_valid:
        return b
    if not b_valid:
        return a
    return (a + b) / 2.0


# Returns True if x is a finite int or float
def isfinite(x):
    return isinstance(x, (int, float)) and math.isfinite(x)
