# one_euro_filter.py
# One Euro Filter (Casiez, Roussel & Vogel, CHI 2012): an adaptive low-pass filter for noisy
# interactive signals such as gaze. It smooths heavily when the signal is slow (kills jitter)
# and lightly when it moves fast (low lag), and has no velocity state so it does not "coast"
# or overshoot after a movement the way a constant-velocity Kalman filter does.

import math


# Exponential smoothing factor for a given time step and cutoff frequency (Hz)
def _smoothing_factor(t_e, cutoff):
    r = 2.0 * math.pi * cutoff * t_e
    return r / (r + 1.0)


def _exponential_smoothing(a, x, x_prev):
    return a * x + (1.0 - a) * x_prev


class OneEuroFilter:
    # min_cutoff: lower = more smoothing at low speed; beta: higher = less lag at high speed
    def __init__(self, min_cutoff=1.0, beta=0.0, d_cutoff=1.0):
        self.min_cutoff = float(min_cutoff)
        self.beta = float(beta)
        self.d_cutoff = float(d_cutoff)
        self._t_prev = None
        self._x_prev = None
        self._dx_prev = 0.0

    # Clears internal state so the next sample re-initializes the filter
    def reset(self):
        self._t_prev = None
        self._x_prev = None
        self._dx_prev = 0.0

    # Filters one sample. t is a monotonic timestamp in seconds; x is the raw value.
    def filter(self, t, x):
        t = float(t)
        x = float(x)

        if self._t_prev is None:
            self._t_prev = t
            self._x_prev = x
            self._dx_prev = 0.0
            return x

        t_e = t - self._t_prev
        if t_e <= 0.0:
            return self._x_prev

        # Filtered derivative of the signal (drives the adaptive cutoff)
        a_d = _smoothing_factor(t_e, self.d_cutoff)
        dx = (x - self._x_prev) / t_e
        dx_hat = _exponential_smoothing(a_d, dx, self._dx_prev)

        # Adapt the cutoff to speed, then low-pass the signal
        cutoff = self.min_cutoff + self.beta * abs(dx_hat)
        a = _smoothing_factor(t_e, cutoff)
        x_hat = _exponential_smoothing(a, x, self._x_prev)

        self._x_prev = x_hat
        self._dx_prev = dx_hat
        self._t_prev = t
        return x_hat
