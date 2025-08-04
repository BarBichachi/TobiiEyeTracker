# gaze.py
# Handles gaze data callback from the Tobii SDK and related gaze computations.
# This includes real-time screen coordinate updates based on eye tracker input,
# as well as utility functions to determine gaze interaction with on-screen elements.

from datetime import datetime, time
from core import state, math_utils, config

def on_gaze_data(data):
    """Callback function triggered by the Tobii SDK on new gaze data.
    Updates gaze position (in screen pixels), timestamp, and resets gaze_lost state."""
    now = datetime.now()
    state.timestamp = (
        now.hour * 3600_000 +
        now.minute * 60_000 +
        now.second * 1_000 +
        now.microsecond // 1_000
    ) / 1000

    lx, ly = data['left_gaze_point_on_display_area']
    rx, ry = data['right_gaze_point_on_display_area']

    # Convert to pixel coordinates using video frame dimensions
    state.gaze_x = int((lx + rx) / 2 * state.screen_width)
    state.gaze_y = int((ly + ry) / 2 * state.screen_height)
    state.last_gaze_time = time.time()
    state.gaze_lost = False

def is_gaze_on_rect(rect):
    """Returns True if the gaze point is within the given rectangle."""
    return (rect["x"] <= state.gaze_x <= rect["x"] + rect["w"] and
            rect["y"] <= state.gaze_y <= rect["y"] + rect["h"])

def is_user_tracking_object(tolerance=config.GAZE_TOLERANCE):
    """Returns True if the gaze is close enough to the tracked object center."""
    dist = math_utils.distance(state.gaze_x, state.gaze_y, state.target_x, state.target_y)
    return dist < tolerance