# kalman_filter.py
# Lightweight 1D constant-velocity Kalman filter used for smoothing gaze coordinates.

import numpy as np


class KalmanFilter:
    # Initializes a 1D Kalman filter with [position, velocity] state
    def __init__(self, initial_position, process_noise, measurement_noise, dt=1.0):
        self._dt = float(dt)

        self._x = np.array([[float(initial_position)], [0.0]])
        self._A = np.array([[1.0, self._dt], [0.0, 1.0]])
        self._H = np.array([[1.0, 0.0]])

        q = float(process_noise)
        r = float(measurement_noise)
        self._Q = np.array([[q, 0.0], [0.0, q]])
        self._R = np.array([[r]])

        self._P = np.array([[1000.0, 0.0], [0.0, 1000.0]])

    # Predicts the next state based on the motion model
    def predict(self):
        self._x = self._A @ self._x
        self._P = self._A @ self._P @ self._A.T + self._Q

    # Updates the state estimate using a new measurement
    def update(self, measurement):
        z = float(measurement)

        s = self._H @ self._P @ self._H.T + self._R
        k = self._P @ self._H.T @ np.linalg.inv(s)

        y = z - (self._H @ self._x)
        self._x = self._x + k @ y
        self._P = (np.eye(self._x.shape[0]) - k @ self._H) @ self._P

    # Returns the smoothed position estimate
    def get_smoothed_position(self):
        return float(self._x[0, 0])