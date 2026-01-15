# bootstrap.py
# Boots the runtime: eye tracker connection, gaze subscription, video source init, UI startup, and periodic update loops.

import atexit
import math
import threading
import time

import cv2
import numpy as np
import tobii_research as tr
from PySide6.QtWidgets import QApplication

from core import config, gaze, state
from core.mock_eye_tracker import MockEyeTracker
from core.math_utils import delta, distance
from ui import live_graphs, trackbars, video_loop


GRAPH_UPDATE_INTERVAL_SEC = 0.01
DEFAULT_FRAME_WAIT_MS = 33
MOCK_TRACKER_HZ = 120


# Runs a function periodically in a daemon thread
def _run_periodically(interval_sec, func):
    def runner():
        while True:
            try:
                func()
            except Exception as e:
                print(f"[Periodic Task Error] {e}")
            time.sleep(interval_sec)

    threading.Thread(target=runner, daemon=True).start()


# Calculates entropy-style values and pushes them to the live graphs
def _update_graph_data():
    if state.graph_window is None:
        return

    if state.gaze_x is None or state.gaze_y is None or state.target_x is None or state.target_y is None:
        return

    dx = delta(state.gaze_x, state.target_x)
    dy = delta(state.gaze_y, state.target_y)
    dr = distance(state.gaze_x, state.gaze_y, state.target_x, state.target_y)

    if dx is None or dy is None or dr is None:
        return

    ex = math.log(abs(dx / config.X_THRESH)) * np.sign(dx) if abs(dx) > config.X_THRESH else 0
    ey = math.log(abs(dy / config.Y_THRESH)) * np.sign(dy) if abs(dy) > config.Y_THRESH else 0
    er = math.log(dr / config.R_THRESH) if dr > config.R_THRESH else 0

    try:
        state.graph_window.update_graphs([dx, dy, dr, ex, ey, er], state.timestamp)
    except Exception as e:
        print(f"[Graph Update Error] {e}")


# Opens the configured video source and returns (cap, wait_time_ms)
def _open_video():
    cap = cv2.VideoCapture(str(config.DEFAULT_VIDEO))
    if not cap.isOpened():
        raise RuntimeError(f"Failed opening video source: {config.DEFAULT_VIDEO}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    wait_time = int(1000 / fps) if fps and fps > 0 else DEFAULT_FRAME_WAIT_MS
    return cap, wait_time


# Reads video dimensions into state and centers overlay/UI elements
def _configure_layout_from_video(cap):
    state.screen_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    state.screen_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)

    if state.screen_width <= 0 or state.screen_height <= 0:
        raise RuntimeError("Invalid video dimensions (width/height <= 0)")

    config.TRACKING_MODE_LABEL["org"] = (state.screen_width // 2 - 200, 50)
    config.TRACKING_LOCK_LABEL["org"] = (state.screen_width // 2 - 150, 110)

    button_width = config.BUTTON_RECT["w"]
    button_height = config.BUTTON_RECT["h"]
    config.BUTTON_RECT["x"] = state.screen_width // 2 - button_width // 2
    config.BUTTON_RECT["y"] = config.TRACKING_MODE_LABEL["org"][1] + 100

    config.BUTTON_LABEL["org"] = (config.BUTTON_RECT["x"] + 20, config.BUTTON_RECT["y"] + button_height // 2 + 10)


# Finds a Tobii tracker or returns a mock tracker when none is available
def _create_tracker():
    eyetrackers = tr.find_all_eyetrackers()
    if not eyetrackers:
        print("[Startup] No eye tracker found. Using MockEyeTracker")
        return MockEyeTracker(hz=MOCK_TRACKER_HZ)
    return eyetrackers[0]


# Subscribes to gaze stream and registers shutdown cleanup
def _subscribe_gaze(tracker):
    tracker.subscribe_to(tr.EYETRACKER_GAZE_DATA, gaze.on_gaze_data, as_dictionary=True)
    atexit.register(_make_tobii_shutdown(tracker))


# Prints tracker details in a consistent format
def _print_tracker_info(tracker):
    print("[EyeTracker] Connected")
    print(f"  Address: {getattr(tracker, 'address', '(N/A)')}")
    print(f"  Model:   {getattr(tracker, 'model', '(N/A)')}")
    print(f"  Name:    {getattr(tracker, 'device_name', None) or '(Unnamed)'}")
    print(f"  Serial:  {getattr(tracker, 'serial_number', '(N/A)')}")


# Unsubscribes from Tobii streams to avoid exit-time SDK errors
def _make_tobii_shutdown(tracker):
    def safe_shutdown():
        try:
            tracker.unsubscribe_from(tr.EYETRACKER_GAZE_DATA, gaze.on_gaze_data)
        except Exception:
            pass

    return safe_shutdown


# Starts the runtime: tracker, video, UI, background loops
def start():
    try:
        tracker = _create_tracker()
        _subscribe_gaze(tracker)
        _print_tracker_info(tracker)

        cap, wait_time = _open_video()
        _configure_layout_from_video(cap)

        trackbars.create_trackbars()

        app = QApplication([])
        state.graph_window = live_graphs.LiveGraphs()
        state.graph_window.show()

        threading.Thread(target=video_loop.show_video, args=(cap, wait_time, app), daemon=True).start()
        _run_periodically(GRAPH_UPDATE_INTERVAL_SEC, _update_graph_data)

        app.exec()

    except Exception as e:
        print(f"[Startup Error] {e}")