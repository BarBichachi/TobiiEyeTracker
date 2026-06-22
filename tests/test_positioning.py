from core import positioning, state


def _reset():
    state.user_left_pos = None
    state.user_left_valid = False
    state.user_right_pos = None
    state.user_right_valid = False


class TestOnUserPositionGuide:
    def test_updates_state(self):
        _reset()
        data = {
            "left_user_position": (0.5, 0.5, 0.5),
            "left_user_position_validity": 1,
            "right_user_position": (0.6, 0.5, 0.5),
            "right_user_position_validity": 0,
        }
        positioning.on_user_position_guide(data)
        assert state.user_left_pos == (0.5, 0.5, 0.5)
        assert state.user_left_valid is True
        assert state.user_right_valid is False


class TestAveragePosition:
    def test_none_when_no_valid_eyes(self):
        assert positioning.average_position(None, False, None, False) is None

    def test_uses_only_valid_eyes(self):
        avg = positioning.average_position((0.4, 0.4, 0.4), True, (0.6, 0.6, 0.6), False)
        assert avg == (0.4, 0.4, 0.4)

    def test_averages_both_eyes(self):
        avg = positioning.average_position((0.4, 0.4, 0.4), True, (0.6, 0.6, 0.6), True)
        assert avg == (0.5, 0.5, 0.5)


class TestFeedback:
    def test_no_eyes(self):
        text, color, centered = positioning.position_feedback(None)
        assert centered is False and "No eyes" in text

    def test_centered(self):
        text, color, centered = positioning.position_feedback((0.5, 0.5, 0.5))
        assert centered is True and color == (0, 220, 0)

    def test_off_center_x(self):
        text, _, centered = positioning.position_feedback((0.9, 0.5, 0.5))
        assert centered is False and "Adjust" in text

    def test_off_center_depth(self):
        _, _, centered = positioning.position_feedback((0.5, 0.5, 0.9))
        assert centered is False

    def test_within_tolerance_is_centered(self):
        # Just inside the default tolerance on every axis
        d = positioning.CENTER_TOLERANCE - 0.001
        assert positioning.is_centered((0.5 + d, 0.5 - d, 0.5 + d)) is True

    def test_outside_tolerance_not_centered(self):
        d = positioning.CENTER_TOLERANCE + 0.01
        assert positioning.is_centered((0.5 + d, 0.5, 0.5)) is False
