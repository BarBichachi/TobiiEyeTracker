from core.kalman_filter import KalmanFilter


def _make():
    return KalmanFilter(initial_position=100.0, process_noise=0.1, measurement_noise=50.0)


class TestKalmanFilter:
    def test_initial_position(self):
        kf = _make()
        assert kf.get_smoothed_position() == 100.0

    def test_returns_float(self):
        kf = _make()
        kf.predict()
        kf.update(120.0)
        assert isinstance(kf.get_smoothed_position(), float)

    def test_smooths_a_spike(self):
        # A single large jump must not be followed fully on the next sample.
        kf = _make()
        kf.predict()
        kf.update(900.0)
        out = kf.get_smoothed_position()
        assert 100.0 < out < 900.0

    def test_converges_to_constant(self):
        # Feeding a steady measurement should pull the estimate close to it.
        kf = _make()
        for _ in range(60):
            kf.predict()
            kf.update(300.0)
        assert abs(kf.get_smoothed_position() - 300.0) < 1.0

    def test_lags_noisy_oscillation(self):
        # Output should stay inside the measured envelope (acts as a low-pass).
        kf = _make()
        out = None
        for m in [100, 200, 100, 200, 100, 200]:
            kf.predict()
            kf.update(m)
            out = kf.get_smoothed_position()
        assert 100.0 <= out <= 200.0
