# kalman_filter.py
# A simple, self-contained implementation of a 1D Kalman filter.
# This filter is designed to smooth noisy, real-time measurements
# by estimating the true state of a system (in this case, gaze position).
import numpy as np

class KalmanFilter:
    """
    A simple 1D Kalman filter for smoothing a single measurement
    such as the X or Y coordinate of a gaze point.

    The state is a 2x1 vector [position, velocity].

    The filter has a "predict" step where it estimates the next state
    based on the previous state and a "update" step where it corrects
    that estimate based on the new measurement.
    """

    def __init__(self, initial_position, process_noise, measurement_noise):
        """
        Initializes the Kalman filter.

        Args:
            initial_position (float): The first known position measurement.
            process_noise (float): A value representing the uncertainty in our
                                   model (how much the system changes between updates).
                                   A higher value makes the filter trust the prediction less.
            measurement_noise (float): A value representing the uncertainty in our
                                       measurements. A higher value makes the filter
                                       trust the raw measurement less.
        """
        # State vector: [position, velocity]
        self.x = np.array([[initial_position], [0.0]])

        # State transition matrix (A).
        # This matrix predicts the next state from the current state.
        # [1 1] -> new position = old position + old velocity
        # [0 1] -> new velocity = old velocity (assuming constant velocity)
        self.A = np.array([[1.0, 1.0], [0.0, 1.0]])

        # Measurement matrix (H).
        # This matrix maps the state vector to the measurement vector.
        # We only measure position, so H = [1 0].
        self.H = np.array([[1.0, 0.0]])

        # Process noise covariance matrix (Q).
        # This represents the uncertainty of our system model.
        # We'll use a simple diagonal matrix where we can tune the
        # process noise independently for position and velocity.
        self.Q = np.array([[process_noise, 0.0], [0.0, process_noise]])

        # Measurement noise covariance matrix (R).
        # This represents the uncertainty of the raw gaze measurement.
        self.R = np.array([[measurement_noise]])

        # Covariance matrix (P).
        # This matrix represents the uncertainty of our state estimate.
        # We start with a high uncertainty and the filter will reduce it.
        self.P = np.array([[1.0, 0.0], [0.0, 1.0]]) * 1000.0

    def predict(self):
        """
        Predicts the next state of the system based on the current state.
        This updates the state vector and the covariance matrix.
        """
        self.x = self.A @ self.x
        self.P = self.A @ self.P @ self.A.T + self.Q

    def update(self, measurement):
        """
        Corrects the state estimate using a new measurement.

        Args:
            measurement (float): The new raw gaze coordinate.
        """
        # Calculate the Kalman Gain (K).
        # This determines how much we trust the new measurement vs. our prediction.
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)

        # Update the state estimate.
        y = measurement - self.H @ self.x  # Innovation (difference between measurement and prediction)
        self.x = self.x + K @ y

        # Update the covariance matrix.
        self.P = (np.eye(self.x.shape[0]) - K @ self.H) @ self.P

    def get_smoothed_position(self):
        """
        Returns the smoothed position estimate from the state vector.
        """
        return self.x[0][0]