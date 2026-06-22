# video_loop.py
# Runs the real-time video loop: frame acquisition, target extraction, gaze interaction, state updates, and overlay rendering.

import logging
import os
import time
import traceback

import cv2
import numpy as np

from core import config, gaze, math_utils, sound, state, targeting
from ui import eye_overlay, render, target_overlay


logger = logging.getLogger(__name__)

_WINDOW_NAME = "Main Window"


# Applies the current fullscreen state to the main window
def _apply_fullscreen(enabled):
    prop = cv2.WINDOW_FULLSCREEN if enabled else cv2.WINDOW_NORMAL
    cv2.setWindowProperty(_WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, prop)


# Toggles fullscreen (gaze->pixel mapping is only correct when fullscreen)
def _toggle_fullscreen():
    state.fullscreen = not state.fullscreen
    _apply_fullscreen(state.fullscreen)


# Runs the main video loop until quit is requested or capture ends
def show_video(cap, wait_time_ms, app):
    paused = False
    frame = None

    cv2.namedWindow(_WINDOW_NAME, cv2.WINDOW_NORMAL)
    _apply_fullscreen(state.fullscreen)

    focus_state = _create_focus_state()
    latch_state = _create_latch_state()

    try:
        while True:
            if not paused:
                frame = _read_frame_or_none(cap)
                if frame is None:
                    # End of clip (or transient miss): rewind and loop the video instead of
                    # busy-spinning on a dead capture. Break only if rewind yields nothing.
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    frame = _read_frame_or_none(cap)
                    if frame is None:
                        logger.info("Capture ended")
                        break

            now = time.time()
            targets, mask_raw = _detect_targets(frame)

            canvas = _create_canvas(frame, mask_raw)
            _render_common_overlays(canvas, now)
            _render_pupils(canvas)

            gaze_xy = targeting.gaze_point_or_none()

            focus_state, focus_from_sticky = _update_focus_state(targets, gaze_xy, focus_state, now)
            latch_state, did_request_latch = _update_latch_state(targets, focus_state["focused_idx"], latch_state, now)

            if did_request_latch:
                _maybe_play_switched_target(latch_state)

            targeting.update_state_target_xy(targets, focus_state["focused_idx"], latch_state["latched_idx"], latch_state["latched_anchor"])
            _update_latch_flags(focus_state["focused_idx"], latch_state)

            render.draw_gaze_trail_and_entropy(canvas)

            if not state.tracking_lock:
                _update_tracking_mode(now)

            target_overlay.draw_focus_and_latch(canvas, targets, focus_state["focused_idx"], focus_from_sticky, latch_state["latched_anchor"], latch_state["latched_idx"])

            render.draw_position_guide(canvas)
            render.draw_hotkey_legend(canvas)
            render.draw_toast(canvas, now)

            cv2.imshow(_WINDOW_NAME, canvas)

            paused_next = _handle_pause_quit(wait_time_ms, app, paused)
            if paused_next is None:
                break
            paused = paused_next

    except Exception:
        logger.error("Frame error\n%s", traceback.format_exc())

    finally:
        cap.release()
        cv2.destroyAllWindows()
        for _ in range(3):
            cv2.waitKey(1)  # pump HighGUI so the (fullscreen) window tears down promptly


# Creates an initial focus state dictionary
def _create_focus_state():
    return {"focused_idx": None, "focused_ts": 0.0}


# Creates an initial latch state dictionary
def _create_latch_state():
    return {"latched_anchor": None, "latched_seen_ts": 0.0, "latched_idx": None, "prev_latched_idx": None}


# Reads a frame from OpenCV capture and returns None on failure
def _read_frame_or_none(cap):
    success, frame = cap.read()
    if not success or frame is None:
        return None
    return frame


# Builds detection mask, extracts contours, and returns (targets, mask_raw)
def _detect_targets(frame):
    mask_raw = _build_processing_mask(frame)
    contours, _ = cv2.findContours(mask_raw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return _extract_targets(contours), mask_raw


# Creates the output canvas based on grayscale setting
def _create_canvas(frame, mask_raw):
    return cv2.cvtColor(mask_raw, cv2.COLOR_GRAY2BGR) if config.IS_GRAYSCALE else frame.copy()


# Draws static UI elements and runs time-based interaction handlers
def _render_common_overlays(canvas, now):
    _handle_tracking_lock_toggle(canvas, now)

    render.draw_gaze_point(canvas)

    cx = int(state.screen_width // 2)
    render.draw_hud_label(canvas, config.TRACKING_MODE_LABEL["text"], config.TRACKING_MODE_LABEL["color"], cx, 56)

    _handle_attention_timeout(canvas, now)

    render.draw_button_overlay(canvas)
    _handle_gaze_button_interaction(now)

    render.draw_hud_label(canvas, config.TRACKING_LOCK_LABEL["text"], config.TRACKING_LOCK_LABEL["color"], cx, 116)


# Draws pupil overlays at fixed positions
def _render_pupils(canvas):
    eye_overlay.draw_pupil(canvas, state.left_pupil_diameter, state.left_pupil_position)
    eye_overlay.draw_pupil(canvas, state.right_pupil_diameter, state.right_pupil_position)


# Updates focus state and returns (focus_state, focus_from_sticky)
def _update_focus_state(targets, gaze_xy, focus_state, now):
    focused_idx, focused_ts, focus_from_sticky = targeting.update_focus(targets=targets, focused_idx=focus_state["focused_idx"], focused_ts=focus_state["focused_ts"], now=now, gaze_xy=gaze_xy)
    focus_state["focused_idx"] = focused_idx
    focus_state["focused_ts"] = focused_ts
    return focus_state, focus_from_sticky


# Updates latch state and returns (latch_state, did_request_latch)
def _update_latch_state(targets, focused_idx, latch_state, now):
    latch_state["prev_latched_idx"] = latch_state["latched_idx"]

    did_request_latch = _did_request_latch(focused_idx, now)
    if did_request_latch:
        latch_state["latched_anchor"] = targeting.make_latch_anchor(targets[focused_idx])

    latched_anchor, latched_idx, latched_seen_ts = targeting.track_latched(latch_state["latched_anchor"], targets, latch_state["latched_seen_ts"], now)
    latch_state["latched_anchor"] = latched_anchor
    latch_state["latched_idx"] = latched_idx
    latch_state["latched_seen_ts"] = latched_seen_ts

    return latch_state, did_request_latch


# Returns True when left blink gesture fired while a target is focused
def _did_request_latch(focused_idx, now):
    left_blinked = _detect_eye_closure("LEFT", config.LEFT_EYE_CLOSURE_SECONDS, now)
    return bool(left_blinked and (focused_idx is not None))


# Plays switched-target sound only when latch request results in a different target
def _maybe_play_switched_target(latch_state):
    latched_idx = latch_state["latched_idx"]
    prev_latched_idx = latch_state["prev_latched_idx"]

    if latched_idx is not None and (prev_latched_idx is None or latched_idx != prev_latched_idx):
        sound.play_switched_target_sound()


# Updates state flags related to latch presence and whether gaze is on it
def _update_latch_flags(focused_idx, latch_state):
    latched_anchor = latch_state["latched_anchor"]
    latched_idx = latch_state["latched_idx"]

    state.has_latch = (latched_anchor is not None and latched_idx is not None)
    state.gaze_on_latched = state.has_latch and (focused_idx == latched_idx)


# Updates tracking mode based on gaze/target state and rate-limits changes
def _update_tracking_mode(now):
    if state.tracking_lock:
        tracking_now = False
    else:
        gx_ok = math_utils.isfinite(state.gaze_x) and math_utils.isfinite(state.gaze_y)
        tracking_now = bool(state.target_present) and gx_ok and gaze.is_user_tracking_object()

    state.user_is_tracking = tracking_now
    desired_mode = "user" if tracking_now else "computer"

    if state.has_latch and not state.gaze_on_latched:
        desired_mode = "computer"

    if desired_mode != state.current_gaze_mode and (now - state.last_mode_switch_time) >= config.MODE_SWITCH_COOLDOWN_S:
        state.current_gaze_mode = desired_mode
        state.last_mode_switch_time = now

        if desired_mode == "user":
            sound.play_user_mode_sound()
            _set_tracking_label("User", (0, 255, 0))
        else:
            sound.play_computer_mode_sound()
            _set_tracking_label("Computer", (0, 0, 255))


# Updates the mutable TRACKING_MODE_LABEL with new mode and color
def _set_tracking_label(mode, color):
    config.TRACKING_MODE_LABEL["text"] = f"Tracking mode: {mode}"
    config.TRACKING_MODE_LABEL["color"] = color


# Implements dwell-to-press behavior for the virtual button
def _handle_gaze_button_interaction(now):
    on_button = gaze.is_gaze_on_rect(config.BUTTON_RECT, config.GAZE_BUTTON_TOLERANCE)

    if not on_button:
        state.button_dwell_start_time = None
        state.current_button_progress = 0.0
        return

    if state.button_dwell_start_time is None:
        state.button_dwell_start_time = now
        state.current_button_progress = 0.0
        return

    dwell = now - state.button_dwell_start_time
    state.current_button_progress = max(0.0, min(1.0, dwell / config.BUTTON_DWELL_SECONDS))

    if dwell < config.BUTTON_DWELL_SECONDS:
        return

    if config.IS_GRAYSCALE:
        sound.play_cognitive_aid_disabled_sound()
        config.IS_GRAYSCALE = False
        render.set_toast("Cognitive Aid Off", (60, 60, 255), 3.0)
    else:
        sound.play_cognitive_aid_enabled_sound()
        config.IS_GRAYSCALE = True
        render.set_toast("Cognitive Aid On", (0, 220, 0), 3.0)

    state.button_dwell_start_time = None
    state.current_button_progress = 0.0


# Handles pause/quit/mute key inputs and returns new paused state or None to exit
def _handle_pause_quit(wait_time_ms, app, paused):
    key = cv2.waitKey(wait_time_ms) & 0xFF

    if key == ord("q"):
        # Hard-terminate immediately. Graceful teardown (Qt quit + Tobii unsubscribe) can
        # block on native threads and hang the exit; os._exit kills the whole process now.
        os._exit(0)
    if key == ord(" "):
        return not paused
    if key == ord("m"):
        _toggle_mute()
    if key == ord("f"):
        _toggle_fullscreen()
    if key == ord("h"):
        state.show_legend = not state.show_legend
    if key == ord("p"):
        state.show_position_guide = not state.show_position_guide

    return paused


# Toggles global sound and shows a transient on-screen toast as feedback
def _toggle_mute():
    enabled = sound.toggle_sound_enabled()
    if enabled:
        render.set_toast("Sound On", (0, 220, 0), 3.0, icon="sound_on")
        sound.play_button_pressed_sound()
    else:
        render.set_toast("Sound Off", (60, 60, 255), 3.0, icon="sound_off")


# Draws attention prompt and beeps when gaze timeout is exceeded (rate-limited)
def _handle_attention_timeout(canvas, now):
    if (now - state.last_gaze_time) <= config.GAZE_TIMEOUT_SECONDS:
        return False

    render.draw_attention_prompt(canvas)

    if (now - state.last_user_not_here_beep_time) > config.BEEP_TIMEOUT_SECONDS:
        sound.play_user_not_here_sound()
        state.last_user_not_here_beep_time = now

    return True


# Converts frame to HSV and thresholds it for contour detection
def _build_processing_mask(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower = np.array([config.HUE_MIN, config.SAT_MIN, config.VAL_MIN])
    upper = np.array([config.HUE_MAX, config.SAT_MAX, config.VAL_MAX])
    return cv2.inRange(hsv, lower, upper)


# Detects eye closure for the requested duration and returns True once per gesture
def _detect_eye_closure(eye, duration, now):
    if eye not in ("LEFT", "RIGHT"):
        raise ValueError("eye must be 'LEFT' or 'RIGHT'")

    pupil_diameter = state.left_pupil_diameter if eye == "LEFT" else state.right_pupil_diameter
    timer_attr = f"{eye.lower()}_eye_close_start_time"
    is_eye_closed = pupil_diameter == 0.0

    if is_eye_closed:
        start_time = getattr(state, timer_attr)
        if start_time is None:
            setattr(state, timer_attr, now)
            return False
        if now - start_time >= duration:
            setattr(state, timer_attr, None)
            return True
    else:
        setattr(state, timer_attr, None)

    return False


# Toggles tracking lock based on right eye closure (requires left eye open)
def _handle_tracking_lock_toggle(canvas, now):
    toggled = _detect_eye_closure("RIGHT", config.RIGHT_EYE_CLOSURE_SECONDS, now) and state.left_pupil_diameter > 0.0
    if not toggled:
        return

    state.tracking_lock = not state.tracking_lock

    if state.tracking_lock:
        config.TRACKING_LOCK_LABEL["text"] = "Tracking Lock: 'ON'"
        config.TRACKING_LOCK_LABEL["color"] = (0, 255, 255)
        sound.play_tracking_lock_enabled_sound()
        render.set_toast("Tracking Lock On", (0, 255, 255), 3.0)
        state.user_is_tracking = False
        state.current_gaze_mode = "computer"
        _set_tracking_label("Computer", (0, 0, 255))
    else:
        config.TRACKING_LOCK_LABEL["text"] = "Tracking Lock: 'OFF'"
        config.TRACKING_LOCK_LABEL["color"] = (255, 255, 0)
        sound.play_tracking_lock_disabled_sound()
        render.set_toast("Tracking Lock Off", (255, 255, 0), 3.0)


# Extracts contour-based targets (bbox/center/area), sorted by area descending
def _extract_targets(contours):
    items = []

    for c in contours:
        area = cv2.contourArea(c)
        if area < config.MIN_CONTOUR_AREA:
            continue

        x, y, w, h = cv2.boundingRect(c)
        items.append({"bbox": (x, y, w, h), "center": (x + w // 2, y + h // 2), "area": area})

    items.sort(key=lambda t: t["area"], reverse=True)
    return items[:config.MAX_TARGETS_CONSIDERED]
