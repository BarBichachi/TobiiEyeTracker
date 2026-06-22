import numpy as np

from core.one_euro_filter import OneEuroFilter

HZ = 90.0
DT = 1.0 / HZ


def _run(values, mc=1.0, beta=0.02):
    f = OneEuroFilter(mc, beta)
    return [f.filter(i * DT, v) for i, v in enumerate(values)]


class TestBasics:
    def test_first_sample_returns_input(self):
        f = OneEuroFilter()
        assert f.filter(0.0, 123.4) == 123.4

    def test_non_increasing_time_holds_value(self):
        f = OneEuroFilter()
        f.filter(1.0, 100.0)
        assert f.filter(1.0, 999.0) == 100.0  # same timestamp -> no update
        assert f.filter(0.5, 999.0) == 100.0  # past timestamp -> no update

    def test_converges_to_constant(self):
        out = _run([500.0] * 60)
        assert abs(out[-1] - 500.0) < 1e-6

    def test_reset(self):
        f = OneEuroFilter()
        f.filter(0.0, 10.0)
        f.filter(DT, 20.0)
        f.reset()
        assert f.filter(0.0, 777.0) == 777.0  # behaves as first sample again


class TestNoOvershoot:
    def test_step_does_not_overshoot(self):
        # Hold 100, then step to 200 and hold. A constant-velocity Kalman would coast past
        # 200; the One Euro filter (no velocity state) must never exceed the target.
        values = [100.0] * 45 + [200.0] * 45
        out = _run(values)
        assert max(out) <= 200.0 + 1e-6

    def test_step_down_does_not_undershoot(self):
        values = [800.0] * 45 + [300.0] * 45
        out = _run(values)
        assert min(out) >= 300.0 - 1e-6


class TestJitterAndResponse:
    def test_reduces_jitter(self):
        rng = np.random.default_rng(0)
        noise = rng.normal(0, 8.0, 200)
        values = list(500.0 + noise)
        out = _run(values)
        settled = np.array(out[50:])
        assert settled.std() < noise[50:].std()

    def test_responds_to_large_change(self):
        out = _run([0.0] * 10 + [1000.0] * 60)
        assert out[-1] > 900.0  # tracks the new level (bounded lag)
