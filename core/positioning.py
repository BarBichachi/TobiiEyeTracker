# positioning.py
# Handles the Tobii User Position Guide stream and derives head/eye alignment feedback,
# used by the on-screen positioning guide (track box) overlay.

import time

from core import state


# Distance from track-box center (0.5) still considered "well positioned"
CENTER_TOLERANCE = 0.12
# Ideal normalized depth (z); 0.0 = closest to tracker, 1.0 = farthest
IDEAL_DEPTH = 0.5


# Callback for EYETRACKER_USER_POSITION_GUIDE: stores normalized eye positions in state
def on_user_position_guide(data):
    state.user_left_pos = data.get("left_user_position")
    state.user_left_valid = data.get("left_user_position_validity") == 1
    state.user_right_pos = data.get("right_user_position")
    state.user_right_valid = data.get("right_user_position_validity") == 1
    state.last_user_position_time = time.time()


# Returns the averaged normalized (x, y, z) of valid eyes, or None if none are valid
def average_position(left_pos=None, left_valid=None, right_pos=None, right_valid=None):
    if left_pos is None and left_valid is None and right_pos is None and right_valid is None:
        left_pos, left_valid = state.user_left_pos, state.user_left_valid
        right_pos, right_valid = state.user_right_pos, state.user_right_valid

    points = []
    if left_valid and left_pos is not None:
        points.append(left_pos)
    if right_valid and right_pos is not None:
        points.append(right_pos)

    if not points:
        return None

    n = len(points)
    return tuple(sum(p[i] for p in points) / n for i in range(3))


# Returns True if the averaged position is within tolerance on all three axes
def is_centered(avg, tol=CENTER_TOLERANCE):
    if avg is None:
        return False
    return all(abs(avg[i] - 0.5) <= tol for i in range(3))


# Returns (status_text, color_bgr, centered_bool) for the averaged position
def position_feedback(avg, tol=CENTER_TOLERANCE):
    if avg is None:
        return "No eyes detected", (60, 60, 255), False

    if is_centered(avg, tol):
        return "Good position", (0, 220, 0), True

    return "Adjust your position", (0, 200, 255), False
