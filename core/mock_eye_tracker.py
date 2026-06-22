# mock_eye_tracker.py
# Simulates a Tobii-like eye tracker by periodically emitting gaze and user-position-guide
# samples to whichever streams are subscribed. Lets the app run without hardware.

import logging
import math
import random
import threading
import time
from typing import Callable, Optional

import tobii_research as tr


logger = logging.getLogger(__name__)


class MockEyeTracker:
    # Initializes a mock tracker that emits gaze samples at a fixed rate
    def __init__(self, hz: int = 120):
        self._hz = int(hz)
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._callbacks = {}

        self.address = "mock://localhost"
        self.model = "MockEyeTracker"
        self.device_name = "Mock"
        self.serial_number = "MOCK-0000"

    # Mimics tobii_research subscribe_to (supports multiple streams)
    def subscribe_to(self, event, callback: Callable, as_dictionary: bool = True):
        self._callbacks[event] = callback
        if self._thread is None or not self._thread.is_alive():
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()

    # Mimics tobii_research unsubscribe_from
    def unsubscribe_from(self, event, callback: Callable = None):
        self._callbacks.pop(event, None)
        if self._callbacks:
            return
        self._stop_event.set()
        if self._thread and self._thread.is_alive() and threading.current_thread() is not self._thread:
            self._thread.join(timeout=1.0)
        self._thread = None

    # Emits periodic samples to every subscribed stream
    def _run_loop(self):
        dt = 1.0 / float(self._hz)
        t0 = time.perf_counter()

        while not self._stop_event.is_set():
            t = time.perf_counter() - t0
            self._emit(tr.EYETRACKER_GAZE_DATA, self._build_gaze_data, t)
            self._emit(tr.EYETRACKER_USER_POSITION_GUIDE, self._build_position_data, t)
            self._stop_event.wait(dt)

    # Calls the callback for one stream (if subscribed) with freshly built data
    def _emit(self, event, builder, t):
        cb = self._callbacks.get(event)
        if cb is None:
            return
        try:
            cb(builder(t))
        except Exception as e:
            logger.error("Callback error (%s): %s", event, e)

    # Builds a Tobii-like gaze dictionary with smooth motion and pupil data
    def _build_gaze_data(self, t):
        x = 0.5 + 0.35 * math.sin(t * 0.8) + random.uniform(-0.01, 0.01)
        y = 0.5 + 0.25 * math.cos(t * 1.1) + random.uniform(-0.01, 0.01)
        x = max(0.0, min(1.0, x))
        y = max(0.0, min(1.0, y))

        return {
            "device_time_stamp": int(t * 1_000_000),
            "system_time_stamp": int(time.time() * 1000),

            "left_gaze_point_on_display_area": (x, y),
            "right_gaze_point_on_display_area": (x, y),
            "left_gaze_point_validity": 1,
            "right_gaze_point_validity": 1,

            "left_pupil_diameter": 3.2,
            "left_pupil_validity": 1,
            "right_pupil_diameter": 3.1,
            "right_pupil_validity": 1,
        }

    # Builds a Tobii-like user-position-guide dict drifting gently around the center
    def _build_position_data(self, t):
        x = 0.5 + 0.08 * math.sin(t * 0.5)
        y = 0.5 + 0.06 * math.cos(t * 0.4)
        z = 0.5 + 0.06 * math.sin(t * 0.3)

        return {
            "left_user_position": (max(0.0, min(1.0, x - 0.04)), y, z),
            "left_user_position_validity": 1,
            "right_user_position": (max(0.0, min(1.0, x + 0.04)), y, z),
            "right_user_position_validity": 1,
        }
