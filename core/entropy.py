# entropy.py
# Computes windowed entropy metrics from gaze samples (screen space + gaze error vs target)

import math
import time
from collections import deque


class EntropyTracker:
    # Creates a tracker for windowed entropy calculations
    def __init__(self, window_s=0.8, min_samples=20):
        self.window_s = float(window_s)
        self.min_samples = int(min_samples)

        self._screen_samples = deque()  # (t, x, y, valid)
        self._error_samples = deque()   # (t, dx, dy, valid)

    # Clears all stored samples
    def reset(self):
        self._screen_samples.clear()
        self._error_samples.clear()

    # Adds a sample; if target is provided, stores error sample too
    def add_sample(self, gaze_x, gaze_y, gaze_valid, target_x=None, target_y=None, t=None):
        if t is None:
            t = time.perf_counter()

        gaze_valid = bool(gaze_valid)
        self._screen_samples.append((float(t), float(gaze_x), float(gaze_y), gaze_valid))

        if gaze_valid and target_x is not None and target_y is not None:
            dx = float(gaze_x) - float(target_x)
            dy = float(gaze_y) - float(target_y)
            self._error_samples.append((float(t), dx, dy, True))
        else:
            self._error_samples.append((float(t), 0.0, 0.0, False))

        self._trim(float(t))

    # Returns normalized entropy [0..1] of gaze distribution on the screen grid
    def get_screen_entropy(self, screen_w, screen_h, grid_w=20, grid_h=12, t=None):
        if t is None:
            t = time.perf_counter()

        self._trim(float(t))

        pts = [(x, y) for (_, x, y, v) in self._screen_samples if v and 0.0 <= x < float(screen_w) and 0.0 <= y < float(screen_h)]
        if len(pts) < self.min_samples:
            return None

        counts = {}
        for x, y in pts:
            cx = int((x / float(screen_w)) * int(grid_w))
            cy = int((y / float(screen_h)) * int(grid_h))
            cx = max(0, min(int(grid_w) - 1, cx))
            cy = max(0, min(int(grid_h) - 1, cy))
            counts[(cx, cy)] = counts.get((cx, cy), 0) + 1

        h = self._shannon_entropy_from_counts(counts)
        return self._normalize_entropy(h, int(grid_w) * int(grid_h))

    # Returns normalized inconsistency [0..1] of gaze error vs target (lower is better)
    def get_error_entropy(self, grid=16, t=None):
        if t is None:
            t = time.perf_counter()

        self._trim(float(t))

        pts = [(dx, dy) for (_, dx, dy, v) in self._error_samples if v]
        if len(pts) < self.min_samples:
            return None

        # Robust scale from data (90th percentile)
        abs_dx = sorted(abs(dx) for dx, _ in pts)
        abs_dy = sorted(abs(dy) for _, dy in pts)

        idx = int(0.9 * (len(abs_dx) - 1))
        rx = abs_dx[idx]
        ry = abs_dy[idx]

        r = max(rx, ry, 50.0)  # minimum range to avoid collapse
        span = r * 2.0
        g = int(grid)

        counts = {}
        for dx, dy in pts:
            dx = max(-r, min(r, dx))
            dy = max(-r, min(r, dy))

            nx = (dx + r) / span
            ny = (dy + r) / span

            cx = int(nx * g)
            cy = int(ny * g)

            cx = max(0, min(g - 1, cx))
            cy = max(0, min(g - 1, cy))

            counts[(cx, cy)] = counts.get((cx, cy), 0) + 1

        h = self._shannon_entropy_from_counts(counts)
        return self._normalize_entropy(h, g * g)

    # Trims sample deques to the configured time window
    def _trim(self, t):
        cutoff = float(t) - self.window_s
        while self._screen_samples and self._screen_samples[0][0] < cutoff:
            self._screen_samples.popleft()
        while self._error_samples and self._error_samples[0][0] < cutoff:
            self._error_samples.popleft()

    # Computes Shannon entropy from a histogram dict
    def _shannon_entropy_from_counts(self, counts):
        total = sum(counts.values())
        if total <= 0:
            return None

        h = 0.0
        for c in counts.values():
            p = c / total
            h -= p * math.log2(p)
        return h

    # Normalizes entropy to [0..1] given number of bins
    def _normalize_entropy(self, h, bins):
        if h is None:
            return None
        if bins <= 1:
            return 0.0

        max_h = math.log2(float(bins))
        if max_h <= 0.0:
            return 0.0

        return max(0.0, min(1.0, float(h) / max_h))
