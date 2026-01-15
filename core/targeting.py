# targeting.py
# Target selection and tracking logic based on gaze focus and optional latch behavior.
# Maintains stable target selection across frames using focus and latch sticky windows.

import time

from core import config, math_utils, state


# Returns (gx, gy) if finite; else None
def gaze_point_or_none():
    gx, gy = state.gaze_x, state.gaze_y
    return (gx, gy) if (math_utils.isfinite(gx) and math_utils.isfinite(gy)) else None


# Selects the target whose center is closest to gaze (within tolerance), with sticky fallback
def select_focused_target(targets, gaze_xy, last_focus_idx, last_focus_ts, now):
    if not targets or gaze_xy is None:
        if last_focus_idx is not None and (now - last_focus_ts) < config.FOCUS_STICKY_SECONDS:
            return last_focus_idx, True
        return None, False

    gx, gy = gaze_xy
    thr2 = config.GAZE_TARGET_TOLERANCE * config.GAZE_TARGET_TOLERANCE

    best_idx = None
    best_d2 = None

    for i, t in enumerate(targets):
        cx, cy = t["center"]
        dx = float(gx) - float(cx)
        dy = float(gy) - float(cy)
        d2 = dx * dx + dy * dy

        if d2 > thr2:
            continue

        if best_idx is None:
            best_idx, best_d2 = i, d2
            continue

        if d2 < best_d2 - 1.0:
            best_idx, best_d2 = i, d2
            continue

        if abs(d2 - best_d2) <= 1.0 and t.get("area", 0) > targets[best_idx].get("area", 0):
            best_idx, best_d2 = i, d2

    if best_idx is not None:
        return best_idx, False

    if last_focus_idx is not None and (now - last_focus_ts) < config.FOCUS_STICKY_SECONDS:
        return last_focus_idx, True

    return None, False


# Updates focus index and timestamp based on gaze, targets, and sticky policy
def update_focus(targets, focused_idx, focused_ts, now, gaze_xy):
    new_focus, focus_from_sticky = select_focused_target(targets=targets, gaze_xy=gaze_xy, last_focus_idx=focused_idx, last_focus_ts=focused_ts, now=now)

    if new_focus != focused_idx:
        focused_idx = new_focus

    if new_focus is not None and not focus_from_sticky:
        focused_ts = now

    return focused_idx, focused_ts, focus_from_sticky


# Creates a minimal anchor used to re-identify a target across frames
def make_latch_anchor(target):
    x, y, w, h = target["bbox"]
    return {"center": target["center"], "size": (w, h)}


# Returns idx of closest target to the latched center within max_dist, else None
def remap_latched_to_current_targets(latched_anchor, targets):
    if not latched_anchor or not targets:
        return None

    lx, ly = latched_anchor["center"]
    best_idx, best_d = None, float("inf")

    for i, t in enumerate(targets):
        cx, cy = t["center"]
        d = math_utils.distance(lx, ly, cx, cy)
        if d is None:
            continue
        if d < best_d:
            best_idx, best_d = i, d

    return best_idx if best_d <= config.MAX_REID_DIST_PX else None


# Recreates latch anchor when left blink gesture fires on a focused target
def maybe_latch_on_left_blink(focused_idx, targets, blinked_left, latched_anchor):
    if blinked_left and focused_idx is not None:
        return make_latch_anchor(targets[focused_idx])
    return latched_anchor


# Tracks the latched target this frame and applies a short loss-sticky policy
def track_latched(latched_anchor, targets, latched_seen_ts, now):
    latched_idx = None

    if latched_anchor is None:
        return None, None, latched_seen_ts

    latched_idx = remap_latched_to_current_targets(latched_anchor, targets)
    if latched_idx is not None:
        latched_anchor["center"] = targets[latched_idx]["center"]
        latched_seen_ts = now
        return latched_anchor, latched_idx, latched_seen_ts

    if (now - latched_seen_ts) > config.LATCH_STICKY_SECONDS:
        return None, None, latched_seen_ts

    return latched_anchor, None, latched_seen_ts


# Updates state.target_x/y coherently for downstream consumers
def update_state_target_xy(targets, focused_idx, latched_idx, latched_anchor):
    now = time.time()
    n = len(targets)

    def has_idx(idx):
        return idx is not None and 0 <= idx < n

    if has_idx(focused_idx):
        cx, cy = targets[focused_idx]["center"]
        state.target_x, state.target_y = float(cx), float(cy)
        state.target_present = True
        state.last_target_ts = now
        return

    if latched_anchor is not None and has_idx(latched_idx):
        cx, cy = targets[latched_idx]["center"]
        state.target_x, state.target_y = float(cx), float(cy)
        state.target_present = True
        state.last_target_ts = now
        return

    gx, gy = state.gaze_x, state.gaze_y
    if math_utils.isfinite(gx) and math_utils.isfinite(gy):
        state.target_x, state.target_y = float(gx), float(gy)
        state.target_present = False
        return

    ttl = getattr(config, "TARGET_STALE_SECONDS", 0.30)
    last_ts = getattr(state, "last_target_ts", 0.0)
    if (now - last_ts) <= ttl and math_utils.isfinite(getattr(state, "target_x", 0.0)) and math_utils.isfinite(getattr(state, "target_y", 0.0)):
        state.target_present = False
        return

    state.target_x, state.target_y = 0.0, 0.0
    state.target_present = False
