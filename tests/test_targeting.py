from core import config, state, targeting


def _target(cx, cy, area=100, w=20, h=20):
    return {"center": (cx, cy), "area": area, "bbox": (cx - w // 2, cy - h // 2, w, h)}


class TestSelectFocusedTarget:
    def test_picks_nearest_within_tolerance(self):
        targets = [_target(100, 100), _target(400, 100)]
        idx, sticky = targeting.select_focused_target(targets, (110, 100), None, 0.0, now=1.0)
        assert idx == 0 and sticky is False

    def test_none_when_all_outside_tolerance(self):
        targets = [_target(100, 100)]
        far = (100 + config.GAZE_TARGET_TOLERANCE + 50, 100)
        idx, sticky = targeting.select_focused_target(targets, far, None, 0.0, now=1.0)
        assert idx is None and sticky is False

    def test_tie_break_prefers_larger_area(self):
        # Both centers equidistant (50px) from gaze at (200,100); larger area should win.
        targets = [_target(150, 100, area=100), _target(250, 100, area=900)]
        idx, sticky = targeting.select_focused_target(targets, (200, 100), None, 0.0, now=1.0)
        assert idx == 1 and sticky is False

    def test_sticky_fallback_when_no_targets(self):
        idx, sticky = targeting.select_focused_target([], None, last_focus_idx=2, last_focus_ts=0.9, now=1.0)
        assert idx == 2 and sticky is True

    def test_sticky_expires(self):
        now = 1.0 + config.FOCUS_STICKY_SECONDS + 0.01
        idx, sticky = targeting.select_focused_target([], None, last_focus_idx=2, last_focus_ts=1.0, now=now)
        assert idx is None and sticky is False


class TestUpdateFocus:
    def test_refreshes_ts_on_real_focus(self):
        targets = [_target(100, 100)]
        idx, ts, sticky = targeting.update_focus(targets=targets, focused_idx=None, focused_ts=0.0, now=5.0, gaze_xy=(100, 100))
        assert idx == 0 and ts == 5.0 and sticky is False

    def test_keeps_ts_when_sticky(self):
        idx, ts, sticky = targeting.update_focus(targets=[], focused_idx=1, focused_ts=4.9, now=5.0, gaze_xy=None)
        assert idx == 1 and sticky is True and ts == 4.9


class TestRemapLatched:
    def test_nearest_within_max_dist(self):
        anchor = {"center": (100, 100)}
        targets = [_target(105, 105), _target(400, 400)]
        assert targeting.remap_latched_to_current_targets(anchor, targets) == 0

    def test_none_when_too_far(self):
        anchor = {"center": (100, 100)}
        far = config.MAX_REID_DIST_PX + 100
        targets = [_target(100 + far, 100)]
        assert targeting.remap_latched_to_current_targets(anchor, targets) is None

    def test_none_without_anchor_or_targets(self):
        assert targeting.remap_latched_to_current_targets(None, [_target(1, 1)]) is None
        assert targeting.remap_latched_to_current_targets({"center": (1, 1)}, []) is None


class TestTrackLatched:
    def test_reidentifies_and_updates_anchor(self):
        anchor = {"center": (100, 100)}
        targets = [_target(108, 100)]
        a, idx, ts = targeting.track_latched(anchor, targets, latched_seen_ts=0.0, now=2.0)
        assert idx == 0 and ts == 2.0 and a["center"] == (108, 100)

    def test_loss_sticky_keeps_then_drops(self):
        anchor = {"center": (100, 100)}
        targets = []  # nothing to re-identify

        # within sticky window: keep anchor, idx None
        a, idx, ts = targeting.track_latched(anchor, targets, latched_seen_ts=1.0, now=1.0 + config.LATCH_STICKY_SECONDS - 0.01)
        assert a is anchor and idx is None

        # past sticky window: drop the latch
        a2, idx2, _ = targeting.track_latched(anchor, targets, latched_seen_ts=1.0, now=1.0 + config.LATCH_STICKY_SECONDS + 0.01)
        assert a2 is None and idx2 is None


class TestUpdateStateTargetXY:
    def test_focused_sets_present_target(self):
        targets = [_target(321, 222)]
        targeting.update_state_target_xy(targets, focused_idx=0, latched_idx=None, latched_anchor=None)
        assert state.target_x == 321.0 and state.target_y == 222.0
        assert state.target_present is True
