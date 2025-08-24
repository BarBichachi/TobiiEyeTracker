import time

from core import state, config, math_utils, sound
from ui import render

def gaze_point_or_none():
    """Return (gx, gy) if finite; else None."""
    gx, gy = state.gaze_x, state.gaze_y
    return (gx, gy) if (math_utils.isfinite(gx) and math_utils.isfinite(gy)) else None


def select_focused_target(targets, gaze_xy, last_focus_idx, last_focus_ts, now):
    """Prefer the target whose CENTER is closest to gaze, but only if within tolerance.
    Tie-break by area when distances are almost equal.
    Falls back to sticky focus window."""

    # No valid gaze or no targets: maybe keep sticky
    if not targets or gaze_xy is None:
        if last_focus_idx is not None and (now - last_focus_ts) < config.FOCUS_STICKY_SECONDS:
            return last_focus_idx, True
        return None, False

    gx, gy = gaze_xy
    thr = config.GAZE_TARGET_TOLERANCE
    thr2 = thr * thr

    best_idx = None
    best_d2 = None

    for i, t in enumerate(targets):
        cx, cy = t["center"]
        dx = gx - cx
        dy = gy - cy
        d2 = dx*dx + dy*dy
        if d2 <= thr2:
            if best_idx is None:
                best_idx, best_d2 = i, d2
            else:
                # primary: nearest center
                if d2 < best_d2 - 1.0:  # 1 px^2 slack
                    best_idx, best_d2 = i, d2
                # tie-break: larger area wins
                elif abs(d2 - best_d2) <= 1.0 and t["area"] > targets[best_idx]["area"]:
                    best_idx, best_d2 = i, d2

    if best_idx is not None:
        return best_idx, False

    # Sticky fallback (avoid one-frame drops)
    if last_focus_idx is not None and (now - last_focus_ts) < config.FOCUS_STICKY_SECONDS:
        return last_focus_idx, True

    return None, False


def update_focus(targets, focused_idx, focused_ts, now, gaze_xy):
    """Run selector + apply sticky policy. Returns (focused_idx, focused_ts, focus_from_sticky)."""
    new_focus, focus_from_sticky = (select_focused_target
                                    (targets=targets, gaze_xy=gaze_xy, last_focus_idx=focused_idx, last_focus_ts=focused_ts, now=now))

    if new_focus != focused_idx:
        focused_idx = new_focus

    # Refresh ts only when focus is real (not sticky)
    if new_focus is not None and not focus_from_sticky:
        focused_ts = now

    return focused_idx, focused_ts, focus_from_sticky


def make_latch_anchor(target):
    """Freeze minimal info to re-find same object across frames."""
    (x, y, w, h) = target["bbox"]
    return {"center": target["center"], "size": (w, h)}


def remap_latched_to_current_targets(latched_anchor, targets):
    """Return idx of closest target to the latched center within max_dist, else None."""
    if not latched_anchor or not targets:
        return None

    lx, ly = latched_anchor["center"]
    best_idx, best_d = None, float("inf")

    for i, t in enumerate(targets):
        cx, cy = t["center"]
        d = math_utils.distance(lx, ly, cx, cy)
        if d < best_d:
            best_idx, best_d = i, d

    return best_idx if best_d <= config.MAX_REID_DIST_PX else None


def maybe_latch_on_left_blink(focused_idx, targets, blinked_left: bool, latched_anchor):
    """If left-eye gesture fired while gazing a target, (re)create the latch anchor."""
    if blinked_left and focused_idx is not None:
        return make_latch_anchor(targets[focused_idx])

    return latched_anchor


def track_latched(latched_anchor, targets, latched_seen_ts, now):
    """Re-id the latched target this frame and apply loss sticky.
    Returns (latched_anchor, latched_idx, latched_seen_ts)"""
    latched_idx = None

    if latched_anchor is not None:
        latched_idx = remap_latched_to_current_targets(latched_anchor, targets)
        if latched_idx is not None:
            latched_anchor["center"] = targets[latched_idx]["center"]
            latched_seen_ts = now
        else:
            if (now - latched_seen_ts) > config.LATCH_STICKY_SECONDS:
                latched_anchor = None
                latched_idx = None

    return latched_anchor, latched_idx, latched_seen_ts


def update_state_target_xy(targets, focused_idx, latched_idx, latched_anchor):
    """Keep state.target_x/y coherent for downstream users.
       Be defensive against stale indexes when targets shrink/vanish.
    """
    now = time.time()
    n = len(targets)

    # --- helper: check index validity for this frame ---
    def _has_idx(idx: int) -> bool:
        return idx is not None and 0 <= idx < n

    # --- 1) Focused target (only if the index is valid now) ---
    if _has_idx(focused_idx):
        cx, cy = targets[focused_idx]["center"]
        state.target_x, state.target_y = float(cx), float(cy)
        state.target_present = True
        state.last_target_ts = now
        return

    # --- 2) Latched target (only if re-identified this frame) ---
    if latched_anchor is not None and _has_idx(latched_idx):
        cx, cy = targets[latched_idx]["center"]
        state.target_x, state.target_y = float(cx), float(cy)
        state.target_present = True
        state.last_target_ts = now
        return

    # --- 3) Fallback to gaze if finite (keeps numbers, avoids NaN/None) ---
    gx, gy = state.gaze_x, state.gaze_y
    if math_utils.isfinite(gx) and math_utils.isfinite(gy):
        state.target_x, state.target_y = float(gx), float(gy)
        state.target_present = False
        return

    # --- 4) Hold last numeric target briefly to avoid flicker ---
    ttl = getattr(config, "TARGET_STALE_SECONDS", 0.30)
    last_ts = getattr(state, "last_target_ts", 0.0)
    if (now - last_ts) <= ttl and math_utils.isfinite(getattr(state, "target_x", 0.0)) and math_utils.isfinite(getattr(state, "target_y", 0.0)):
        state.target_present = False
        return

    # --- 5) Final fallback: park at (0,0), never NaN ---
    state.target_x, state.target_y = 0.0, 0.0
    state.target_present = False


def draw_focus_and_latch(canvas, targets, focused_idx, focus_from_sticky, latched_anchor, latched_idx):
    """Overlays:
      - Green while truly focused (not sticky).
      - Red for latched when not being gazed at."""

    # --- RED: draw latched only if it isn't the thing you're currently gazing at ---
    if latched_anchor is not None and latched_idx is not None:
        show_red = state.tracking_lock or (focused_idx is None or latched_idx != focused_idx)
        if show_red:
            bb = _bbox_or_none(latched_idx, targets)
            if bb is not None:
                red_center = targets[latched_idx]["center"]
                # while locked, aim the line at the red box explicitly
                line_target = red_center if state.tracking_lock else None
                render.draw_tracking_overlay(canvas, bb, (0, 0, 255), line_target=line_target)

    # --- GREEN (ignored when lock is ON) ---
    if not state.tracking_lock and focused_idx is not None and not focus_from_sticky:
        bb = _bbox_or_none(focused_idx, targets)
        if bb is not None:
            render.draw_tracking_overlay(canvas, bb, (0, 255, 0))

def _bbox_or_none(idx, targets):
    if idx is None:
        return None
    if idx < 0 or idx >= len(targets):
        return None

    x, y, w, h = targets[idx].get("bbox", (0, 0, 0, 0))

    if w <= 0 or h <= 0:
        return None

    return (x, y, w, h)