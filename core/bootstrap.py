# bootstrap.py
# Initializes the eye tracker, video capture, UI application, and background threads.
# This is the central starting point of the system.

import threading
import time
import math
import cv2
from PySide6.QtWidgets import QApplication
import tobii_research as tr
import numpy as np
import atexit

from core import state, config, gaze
from ui import video_loop, trackbars, live_graphs
from core.mock_eye_tracker import MockEyeTracker


# ---------------------- Periodic Graph Updater ----------------------
def _run_periodically(interval, func):
    """Runs a given function on a fixed interval in a daemon thread."""
    def runner():
        while True:
            func()
            time.sleep(interval)
    threading.Thread(target=runner, daemon=True).start()


# ---------------------- Graph Data Update ----------------------
def _update_graph_data():
    """Updates live entropy/delta graphs based on gaze vs target position."""
    from core.math_utils import delta, distance

    dx = delta(state.gaze_x, state.target_x)
    dy = delta(state.gaze_y, state.target_y)
    dr = distance(state.gaze_x, state.gaze_y, state.target_x, state.target_y)

    ex = math.log(abs(dx / config.X_THRESH)) * np.sign(dx) if abs(dx) > config.X_THRESH else 0
    ey = math.log(abs(dy / config.Y_THRESH)) * np.sign(dy) if abs(dy) > config.Y_THRESH else 0
    er = math.log(dr / config.R_THRESH) if dr > config.R_THRESH else 0

    try:
        state.graph_window.update_graphs([dx, dy, dr, ex, ey, er], state.timestamp)
    except Exception as e:
        print(f"[Graph Update Error] {e}")


# ---------------------- Application Entry ----------------------
def start():
    try:
        # Find and connect to eye tracker
        eyetrackers = tr.find_all_eyetrackers()
        if not eyetrackers:
            print("[Startup] No eye tracker found. Using MockEyeTracker.")
            tracker = MockEyeTracker(i_Hz=120)
        else:
            tracker = eyetrackers[0]

        tracker.subscribe_to(tr.EYETRACKER_GAZE_DATA, gaze.on_gaze_data, as_dictionary=True)

        # Ensure we always unsubscribe before process exit
        tobii_shutdown = _make_tobii_shutdown(tracker)
        atexit.register(tobii_shutdown)

        print("Eye Tracker Connected:")
        print("  Address:", tracker.address)
        print("  Model:", tracker.model)
        print("  Name:", tracker.device_name or "(Unnamed)")
        print("  Serial:", tracker.serial_number)

        # Load video
        cap = cv2.VideoCapture(str(config.DEFAULT_VIDEO))
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        wait_time = int(1000 / video_fps) if video_fps > 0 else 33

        # Store screen dimensions
        state.screen_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        state.screen_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

        # Center tracking mode label
        config.TRACKING_MODE_LABEL["org"] = (int(state.screen_width // 2) - 200, 50)
        config.TRACKING_LOCK_LABEL["org"] = (int(state.screen_width // 2) - 150, 110)

        # Center button under it
        button_width = config.BUTTON_RECT["w"]
        button_height = config.BUTTON_RECT["h"]
        config.BUTTON_RECT["x"] = int(state.screen_width // 2 - button_width // 2)
        config.BUTTON_RECT["y"] = config.TRACKING_MODE_LABEL["org"][1] + 100

        # Adjust label position inside the button
        config.BUTTON_LABEL["org"] = (
            config.BUTTON_RECT["x"] + 20,
            config.BUTTON_RECT["y"] + button_height // 2 + 10
        )

        # Create trackbars
        trackbars.create_trackbars()

        # Launch Qt app
        app = QApplication([])
        state.graph_window = live_graphs.LiveGraphs()
        state.graph_window.show()

        # Launch video display in background
        threading.Thread(target=video_loop.show_video, args=(cap, wait_time, app), daemon=True).start()

        # Launch graph update loop
        _run_periodically(0.01, _update_graph_data)

        # Start Qt event loop
        app.exec()

    except Exception as e:
        print(f"[Startup Error] {e}")

# --- Tobii cleanup helper ---
def _make_tobii_shutdown(tracker):
    """Explicitly unsubscribe from Tobii streams to avoid __del__ errors on exit."""
    def _safe_shutdown():
        try:
            tracker.unsubscribe_from(tr.EYETRACKER_GAZE_DATA, gaze.on_gaze_data)
        except Exception:
            pass
    return _safe_shutdown