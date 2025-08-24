# gaze.py
# Handles gaze data callback from the Tobii SDK and related gaze computations.
# This includes real-time screen coordinate updates based on eye tracker input,
# as well as utility functions to determine gaze interaction with on-screen elements.
import math
from datetime import datetime
import time
from core import state, math_utils, config, kalman_filter

def on_gaze_data(data):
    """Callback from Tobii: smooth gaze with Kalman, update state, handle pupils."""
    # --- Timestamp (seconds within day) ---
    now = datetime.now()
    state.timestamp = (
        now.hour * 3600_000 +
        now.minute * 60_000 +
        now.second * 1_000 +
        now.microsecond // 1_000
    ) / 1000

    # --- Read raw gaze (normalized 0..1) ---
    lx, ly = data['left_gaze_point_on_display_area']
    rx, ry = data['right_gaze_point_on_display_area']
    avg_x = math_utils.safe_average(lx, rx)
    avg_y = math_utils.safe_average(ly, ry)

    # Convert to pixel coordinates using video frame dimensions
    if avg_x is not None and avg_y is not None:
        raw_x = int(avg_x * state.screen_width)
        raw_y = int(avg_y * state.screen_height)

        # Check if the Kalman filters have not been initialized - initialize at first-run
        if state.kalman_x or state.kalman_y is None:
            setup_kalman_filters(raw_x, raw_y)
            state.gaze_x = raw_x
            state.gaze_y = raw_y
        else:
            # Use the Kalman filter to smooth the raw data
            state.kalman_x.predict()
            state.kalman_y.predict()
            state.kalman_x.update(raw_x)
            state.kalman_y.update(raw_y)

            # Get the smoothed gaze position from the filters
            state.gaze_x = int(state.kalman_x.get_smoothed_position())
            state.gaze_y = int(state.kalman_y.get_smoothed_position())

        state.last_gaze_time = time.time()
        state.gaze_lost = False

    # Check if pupil diameter data is valid and get it
    # LEFT EYE
    left_diameter = data.get('left_pupil_diameter', 0.0)
    if data.get('left_pupil_validity') == 1 and not math.isnan(left_diameter):
        state.left_pupil_diameter = left_diameter
    else:
        state.left_pupil_diameter = 0.0

    # RIGHT EYE
    right_diameter = data.get('right_pupil_diameter', 0.0)
    if data.get('right_pupil_validity') == 1 and not math.isnan(right_diameter):
        state.right_pupil_diameter = right_diameter
    else:
        state.right_pupil_diameter = 0.0


def is_gaze_on_rect(rect, offset=0):
    """ True if gaze point is inside rect (±offset).
    `rect` can be dict {x,y,w,h} or tuple/list (x,y,w,h)."""

    if isinstance(rect, dict):
        x, y, w, h = rect["x"], rect["y"], rect["w"], rect["h"]
    else:
        x, y, w, h = rect

    if not (math_utils.isfinite(state.gaze_x) and math_utils.isfinite(state.gaze_y)):
        return False

    x_min = x - offset
    y_min = y - offset
    x_max = x + w + offset
    y_max = y + h + offset

    return (x_min <= state.gaze_x <= x_max) and (y_min <= state.gaze_y <= y_max)


def is_user_tracking_object():
    """Returns True if the gaze is close enough to the tracked object center."""
    dist = math_utils.distance(state.gaze_x, state.gaze_y, state.target_x, state.target_y)
    return dist < config.GAZE_TARGET_TOLERANCE


def setup_kalman_filters(initial_x, initial_y):
    """
    Initializes the Kalman filters for gaze smoothing.
    This function should be called once at the start of the application.
    """
    # Create an instance of the KalmanFilter for the X coordinate
    # The noise values should be tuned based on how "jittery" the raw data is.
    state.kalman_x = kalman_filter.KalmanFilter(
        initial_position=initial_x,
        process_noise=config.GAZE_PROCESS_NOISE_COV,
        measurement_noise=config.GAZE_MEASUREMENT_NOISE_COV
    )

    # Create a separate instance for the Y coordinate
    state.kalman_y = kalman_filter.KalmanFilter(
        initial_position=initial_y,
        process_noise=config.GAZE_PROCESS_NOISE_COV,
        measurement_noise=config.GAZE_MEASUREMENT_NOISE_COV
    )