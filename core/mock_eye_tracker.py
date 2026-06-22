# mock_eye_tracker.py
# Simulates a Tobii-like eye tracker by calling gaze callbacks periodically.

import math
import random
import threading
import time
import logging
from typing import Callable, Optional


logger = logging.getLogger(__name__)


class MockEyeTracker:
    # Initializes a mock tracker that emits gaze samples at a fixed rate
    def __init__(self, hz: int = 120):
        self._hz = int(hz)
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._callback: Optional[Callable] = None

        self.address = "mock://localhost"
        self.model = "MockEyeTracker"
        self.device_name = "Mock"
        self.serial_number = "MOCK-0000"

    # Mimics tobii_research subscribe_to
    def subscribe_to(self, event, callback: Callable, as_dictionary: bool = True):
        self._callback = callback
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    # Mimics tobii_research unsubscribe_from
    def unsubscribe_from(self, event, callback: Callable):
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._thread = None
        self._callback = None

    # Emits periodic gaze samples and calls the subscribed callback
    def _run_loop(self):
        dt = 1.0 / float(self._hz)
        t0 = time.perf_counter()

        while not self._stop_event.is_set():
            t = time.perf_counter() - t0
            gaze_data = self._build_gaze_data(t)

            cb = self._callback
            if cb:
                try:
                    cb(gaze_data)
                except Exception as e:
                    logger.error("Callback error: %s", e)

            self._stop_event.wait(dt)

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
