import random

from core.entropy import EntropyTracker


class TestErrorEntropy:
    def test_none_below_min_samples(self):
        et = EntropyTracker(window_s=1000, min_samples=5)
        for i in range(4):
            et.add_sample(100, 100, True, 50, 50, t=i * 0.1)
        assert et.get_error_entropy(grid=16, t=1.0) is None

    def test_zero_for_constant_error(self):
        et = EntropyTracker(window_s=1000, min_samples=5)
        for i in range(20):
            et.add_sample(100, 100, True, 50, 50, t=i * 0.1)
        assert et.get_error_entropy(grid=16, t=5.0) == 0.0

    def test_positive_for_spread_error(self):
        et = EntropyTracker(window_s=1000, min_samples=5)
        random.seed(0)
        for i in range(300):
            gx = 500 + random.uniform(-200, 200)
            gy = 500 + random.uniform(-200, 200)
            et.add_sample(gx, gy, True, 500, 500, t=i * 0.001)
        h = et.get_error_entropy(grid=16, t=1.0)
        assert h is not None and h > 0.3

    def test_invalid_samples_excluded(self):
        et = EntropyTracker(window_s=1000, min_samples=5)
        for i in range(10):
            et.add_sample(0, 0, False, 50, 50, t=i * 0.1)  # invalid gaze
        assert et.get_error_entropy(grid=16, t=2.0) is None


class TestScreenEntropy:
    def test_none_below_min_samples(self):
        et = EntropyTracker(window_s=1000, min_samples=5)
        for i in range(3):
            et.add_sample(100, 100, True, t=i * 0.1)
        assert et.get_screen_entropy(1000, 600, t=1.0) is None

    def test_zero_when_concentrated(self):
        et = EntropyTracker(window_s=1000, min_samples=5)
        for i in range(30):
            et.add_sample(100, 100, True, t=i * 0.01)
        assert et.get_screen_entropy(1000, 600, grid_w=20, grid_h=12, t=1.0) == 0.0

    def test_higher_when_spread(self):
        et = EntropyTracker(window_s=1000, min_samples=5)
        k = 0
        for gx in range(0, 1000, 50):
            for gy in range(0, 600, 50):
                et.add_sample(gx, gy, True, t=k * 0.001)
                k += 1
        h = et.get_screen_entropy(1000, 600, grid_w=20, grid_h=12, t=1.0)
        assert h is not None and h > 0.5

    def test_normalized_range(self):
        et = EntropyTracker(window_s=1000, min_samples=5)
        random.seed(1)
        for i in range(200):
            et.add_sample(random.uniform(0, 999), random.uniform(0, 599), True, t=i * 0.001)
        h = et.get_screen_entropy(1000, 600, t=1.0)
        assert h is not None and 0.0 <= h <= 1.0


class TestWindowTrim:
    def test_drops_samples_outside_window(self):
        et = EntropyTracker(window_s=1.0, min_samples=1)
        et.add_sample(0, 0, True, t=0.0)
        et.add_sample(1, 1, True, t=0.5)
        et.add_sample(2, 2, True, t=5.0)  # cutoff 4.0 -> older two dropped
        assert len(et._screen_samples) == 1
