# bootstrap.py
# Boots the runtime: eye tracker connection, gaze subscription, video source init, UI startup, and periodic update loops.

import atexit
import logging
import threading

import cv2
import tobii_research as tr
from PySide6.QtWidgets import QApplication

from core import config, gaze, sound, state
from core.mock_eye_tracker import MockEyeTracker
from ui import live_graphs, trackbars, video_loop


logger = logging.getLogger(__name__)

DEFAULT_FRAME_WAIT_MS = 33
MOCK_TRACKER_HZ = 120


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

    w, h = state.screen_width, state.screen_height

    # Center the cognitive-aid button near the top; HUD labels are centered at draw time.
    button_width = config.BUTTON_RECT["w"]
    config.BUTTON_RECT["x"] = w // 2 - button_width // 2
    config.BUTTON_RECT["y"] = 150

    # Place pupil overlays relative to the bottom-right so they scale with resolution.
    state.right_pupil_position = (w - 120, h - 130)
    state.left_pupil_position = (w - 270, h - 130)


# Finds a Tobii tracker or returns a mock tracker when none is available
def _create_tracker():
    eyetrackers = tr.find_all_eyetrackers()
    if not eyetrackers:
        logger.warning("No eye tracker found. Using MockEyeTracker")
        return MockEyeTracker(hz=MOCK_TRACKER_HZ)
    return eyetrackers[0]


# Subscribes to gaze stream and registers shutdown cleanup
def _subscribe_gaze(tracker):
    tracker.subscribe_to(tr.EYETRACKER_GAZE_DATA, gaze.on_gaze_data, as_dictionary=True)
    atexit.register(_make_tobii_shutdown(tracker))


# Logs tracker details in a consistent format
def _print_tracker_info(tracker):
    logger.info("EyeTracker connected")
    logger.info("  Address: %s", getattr(tracker, "address", "(N/A)"))
    logger.info("  Model:   %s", getattr(tracker, "model", "(N/A)"))
    logger.info("  Name:    %s", getattr(tracker, "device_name", None) or "(Unnamed)")
    logger.info("  Serial:  %s", getattr(tracker, "serial_number", "(N/A)"))


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
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
    try:
        sound.set_sound_enabled(config.SOUND_ENABLED)
        if config.SOUND_ENABLED:
            sound.preload_sounds()

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

        app.exec()

    except Exception as e:
        logger.exception("Startup error: %s", e)