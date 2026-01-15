# target_overlay.py
# Renders visual overlays for focus (user gaze) and latch takeover (computer) on top of the video frame.

from core import state
from ui import render


# Draws focus (green) and latch takeover (red) overlays
def draw_focus_and_latch(canvas, targets, focused_idx, focus_from_sticky, latched_anchor, latched_idx):
    if latched_anchor is not None and latched_idx is not None:
        show_red = state.tracking_lock or (focused_idx is None or latched_idx != focused_idx)
        if show_red:
            bb = _bbox_or_none(latched_idx, targets)
            if bb is not None:
                red_center = targets[latched_idx]["center"]
                line_target = red_center if state.tracking_lock else None
                render.draw_tracking_overlay(canvas, bb, (0, 0, 255), line_target=line_target)

    if not state.tracking_lock and focused_idx is not None and not focus_from_sticky:
        bb = _bbox_or_none(focused_idx, targets)
        if bb is not None:
            render.draw_tracking_overlay(canvas, bb, (0, 255, 0))


# Returns bbox tuple if idx is valid and bbox dimensions are positive
def _bbox_or_none(idx, targets):
    if idx is None or idx < 0 or idx >= len(targets):
        return None

    x, y, w, h = targets[idx].get("bbox", (0, 0, 0, 0))
    if w <= 0 or h <= 0:
        return None

    return x, y, w, h
