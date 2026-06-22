import math

from core import math_utils


class TestDelta:
    def test_finite(self):
        assert math_utils.delta(10, 3) == 7

    def test_non_finite_returns_none(self):
        assert math_utils.delta(float("nan"), 3) is None
        assert math_utils.delta(3, float("inf")) is None
        assert math_utils.delta("x", 3) is None


class TestDistance:
    def test_basic(self):
        assert math.isclose(math_utils.distance(0, 0, 3, 4), 5.0)

    def test_zero(self):
        assert math_utils.distance(2, 2, 2, 2) == 0.0

    def test_invalid_returns_none(self):
        assert math_utils.distance(0, 0, float("nan"), 4) is None
        assert math_utils.distance(None, 0, 3, 4) is None


class TestSafeAverage:
    def test_both_valid(self):
        assert math_utils.safe_average(2.0, 4.0) == 3.0

    def test_one_nan_returns_other(self):
        assert math_utils.safe_average(float("nan"), 4.0) == 4.0
        assert math_utils.safe_average(2.0, float("nan")) == 2.0

    def test_both_nan_returns_none(self):
        assert math_utils.safe_average(float("nan"), float("nan")) is None


class TestIsFinite:
    def test_valid_numbers(self):
        assert math_utils.isfinite(0)
        assert math_utils.isfinite(-3.5)

    def test_invalid(self):
        assert not math_utils.isfinite(float("nan"))
        assert not math_utils.isfinite(float("inf"))
        assert not math_utils.isfinite("3")
        assert not math_utils.isfinite(None)
