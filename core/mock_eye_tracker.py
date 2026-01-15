# core/mock_eye_tracker.py
# Simulates a Tobii-like eye tracker by calling gaze callbacks periodically.

import math
import random
import threading
import time
from typing import Callable, Optional

class MockEyeTracker:
    def __init__(self, i_Hz: int = 120):
        self.m_Hz = i_Hz
        self.m_Thread: Optional[threading.Thread] = None
        self.m_StopEvent = threading.Event()
        self.m_Callback: Optional[Callable] = None

        # Optional metadata to match your prints
        self.address = "mock://localhost"
        self.model = "MockEyeTracker"
        self.device_name = "Mock"
        self.serial_number = "MOCK-0000"

    # Mimics tobii_research subscribe_to
    def subscribe_to(self, i_Event, i_Callback: Callable, as_dictionary: bool = True):
        self.m_Callback = i_Callback
        self.m_StopEvent.clear()
        self.m_Thread = threading.Thread(target=self._run_loop, daemon=True)
        self.m_Thread.start()

    # Mimics tobii_research unsubscribe_from
    def unsubscribe_from(self, i_Event, i_Callback: Callable):
        self.m_StopEvent.set()
        if self.m_Thread and self.m_Thread.is_alive():
            self.m_Thread.join(timeout=1.0)
        self.m_Thread = None
        self.m_Callback = None

    def _run_loop(self):
        dt = 1.0 / float(self.m_Hz)
        t0 = time.perf_counter()

        # Smooth gaze moving in a Lissajous-like pattern
        while not self.m_StopEvent.is_set():
            t = time.perf_counter() - t0

            x = 0.5 + 0.35 * math.sin(t * 0.8)
            y = 0.5 + 0.25 * math.cos(t * 1.1)

            # small noise
            x += random.uniform(-0.01, 0.01)
            y += random.uniform(-0.01, 0.01)

            x = max(0.0, min(1.0, x))
            y = max(0.0, min(1.0, y))

            gaze_data = {
                "device_time_stamp": int(t * 1_000_000),
                "system_time_stamp": int(time.time() * 1000),

                "left_gaze_point_on_display_area": (x, y),
                "right_gaze_point_on_display_area": (x, y),
                "left_gaze_point_validity": 1,
                "right_gaze_point_validity": 1,

                # pupil data (your code expects these)
                "left_pupil_diameter": 3.2,
                "left_pupil_validity": 1,
                "right_pupil_diameter": 3.1,
                "right_pupil_validity": 1,
            }

            cb = self.m_Callback
            if cb:
                try:
                    cb(gaze_data)
                except Exception as e:
                    print(f"[MockEyeTracker] Callback error: {e}")

            time.sleep(dt)
