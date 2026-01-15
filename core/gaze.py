# gaze.py
# Processes gaze samples from the eye tracker and updates shared runtime state.
# Provides helper functions for gaze interaction checks (rect hit-test, target tracking).

import math
import time
from datetime import datetime

from core import config, kalman_filter, math_utils, state


# Handles gaze callback: smooth gaze with Kalman, update state, and track pupil diameters
def on_gaze_data(data):
    now = datetime.now()
    state.timestamp = (now.hour * 3600_000 + now.minute * 60_000 + now.second * 1_000 + now.microsecond // 1_000) / 1000.0

    avg_x, avg_y = _extract_avg_gaze(data)
    if avg_x is None or avg_y is None:
        state.gaze_lost = True
        _update_pupils(data)
        return

    raw_x, raw_y = _to_pixel_coords(avg_x, avg_y)
    _update_kalman_and_state(raw_x, raw_y)

    state.last_gaze_time = time.time()
    state.gaze_lost = False

    _update_pupils(data)


# Returns True if gaze point is inside rect (±offset)
def is_gaze_on_rect(rect, offset=0):
    x, y, w, h = _normalize_rect(rect)

    if not (math_utils.isfinite(state.gaze_x) and math_utils.isfinite(state.gaze_y)):
        return False

    x_min = x - offset
    y_min = y - offset
    x_max = x + w + offset
    y_max = y + h + offset

    return x_min <= state.gaze_x <= x_max and y_min <= state.gaze_y <= y_max


# Returns True if the gaze is close enough to the tracked object center
def is_user_tracking_object():
    dist = math_utils.distance(state.gaze_x, state.gaze_y, state.target_x, state.target_y)
    if dist is None:
        return False
    return dist < config.GAZE_TARGET_TOLERANCE


# Initializes the Kalman filters for gaze smoothing
def setup_kalman_filters(initial_x, initial_y):
    state.kalman_x = kalman_filter.KalmanFilter(initial_position=initial_x, process_noise=config.GAZE_PROCESS_NOISE_COV, measurement_noise=config.GAZE_MEASUREMENT_NOISE_COV)
    state.kalman_y = kalman_filter.KalmanFilter(initial_position=initial_y, process_noise=config.GAZE_PROCESS_NOISE_COV, measurement_noise=config.GAZE_MEASUREMENT_NOISE_COV)


# Extracts averaged gaze in display-area coords (0..1) using validity when available
def _extract_avg_gaze(data):
    lx, ly = data.get("left_gaze_point_on_display_area", (float("nan"), float("nan")))
    rx, ry = data.get("right_gaze_point_on_display_area", (float("nan"), float("nan")))

    lv = data.get("left_gaze_point_validity", 1)
    rv = data.get("right_gaze_point_validity", 1)

    if lv != 1:
        lx, ly = float("nan"), float("nan")
    if rv != 1:
        rx, ry = float("nan"), float("nan")

    avg_x = math_utils.safe_average(lx, rx)
    avg_y = math_utils.safe_average(ly, ry)
    return avg_x, avg_y


# Converts normalized display-area coords (0..1) into pixel coords using video dimensions
def _to_pixel_coords(x, y):
    x = max(0.0, min(1.0, x))
    y = max(0.0, min(1.0, y))
    return int(x * state.screen_width), int(y * state.screen_height)


# Updates Kalman filters and writes smoothed gaze to state
def _update_kalman_and_state(raw_x, raw_y):
    if state.kalman_x is None or state.kalman_y is None:
        setup_kalman_filters(raw_x, raw_y)
        state.gaze_x = raw_x
        state.gaze_y = raw_y
        return

    state.kalman_x.predict()
    state.kalman_y.predict()
    state.kalman_x.update(raw_x)
    state.kalman_y.update(raw_y)

    state.gaze_x = int(state.kalman_x.get_smoothed_position())
    state.gaze_y = int(state.kalman_y.get_smoothed_position())


# Updates pupil diameters in state based on validity flags
def _update_pupils(data):
    left_diameter = data.get("left_pupil_diameter", 0.0)
    if data.get("left_pupil_validity") == 1 and isinstance(left_diameter, (int, float)) and not math.isnan(left_diameter):
        state.left_pupil_diameter = float(left_diameter)
    else:
        state.left_pupil_diameter = 0.0

    right_diameter = data.get("right_pupil_diameter", 0.0)
    if data.get("right_pupil_validity") == 1 and isinstance(right_diameter, (int, float)) and not math.isnan(right_diameter):
        state.right_pupil_diameter = float(right_diameter)
    else:
        state.right_pupil_diameter = 0.0


# Normalizes rect input (dict or tuple) into (x, y, w, h)
def _normalize_rect(rect):
    if isinstance(rect, dict):
        return rect["x"], rect["y"], rect["w"], rect["h"]
    return rect
