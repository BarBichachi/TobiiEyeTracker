# video_loop.py
# Runs the real-time video display loop. Handles video capture,
# gaze detection, tracking state updates, interaction logic, and UI rendering.

import time
import cv2
import numpy as np

from core import state, config, sound, gaze
from ui import render, eye_overlay

# ---------------------- Video Display Loop ----------------------
def show_video(cap, wait_time, app):
    paused = False
    frame = None
    tracking_label = config.TRACKING_MODE_LABEL
    cv2.namedWindow('Main Window', cv2.WINDOW_NORMAL)

    # --- Sticky bbox (local): reuse last box briefly to avoid flicker ---
    last_bbox = None
    last_bbox_time = 0.0
    box_stale_seconds = 0.3

    try:
        while True:
            # --- Capture frame (unless paused) ---
            if not paused:
                success, frame = cap.read()
                if not success:
                    print("Warning: Frame read failed.")
                    continue

            current_time = time.time()
            bbox = None

            # --- Build the processing mask ---
            mask_raw = _build_processing_mask(frame)

            # --- Find contours from the ORIGINAL mask ---
            contours, _ = cv2.findContours(mask_raw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                x, y, w, h = _extract_largest_bbox(contours)
                bbox = (x, y, w, h)
                last_bbox = bbox
                last_bbox_time = current_time

                # --- Retrieves the center of the target ---
                state.target_x, state.target_y = x + w // 2, y + h // 2

                # --- Update mode/label/sounds based on current gaze state ---
                if not state.tracking_lock:
                    _update_tracking_mode(current_time)
            else:
                # --- Sticky reuse: keep last box for a short grace period ---
                if last_bbox and (current_time - last_bbox_time) < box_stale_seconds:
                    bbox = last_bbox

            # --- Choose a canvas to draw UI on (mask visualization OR color) ---
            canvas = cv2.cvtColor(mask_raw, cv2.COLOR_GRAY2BGR) if config.IS_GRAYSCALE else frame.copy()

            # --- Handle Tracking Lock toggle (using right eye) ---
            _handle_tracking_lock_toggle(canvas, current_time)

            # --- Draw gaze location ---
            render.draw_gaze_point(canvas)

            # --- Show mode label (User / Computer) ---
            render.draw_tracking_label(canvas, tracking_label)

            # --- Attention prompt & beep ---
            _handle_attention_timeout(canvas, current_time)

            # --- Draw button & handle interaction ---
            render.draw_button_overlay(canvas)
            _handle_gaze_button_interaction(current_time)

            # --- Draw left and right pupil indicators (fixed position) ---
            eye_overlay.draw_pupil(canvas, state.left_pupil_diameter, state.left_pupil_position)
            eye_overlay.draw_pupil(canvas, state.right_pupil_diameter, state.right_pupil_position)

            # --- Draw tracking box on target if we have one and tracking mode is not computer ---
            if bbox is not None and not state.user_is_tracking:
                render.draw_tracking_overlay(canvas, bbox, tracking_label["color"])

            # --- Display ---
            cv2.imshow('Main Window', canvas)

            # --- Keyboard input: pause / quit ---
            new_paused = _handle_pause_quit(wait_time, app, paused)
            if new_paused is None:
                break
            paused = new_paused

    finally:
        cap.release()
        cv2.destroyAllWindows()


# ---------------------- Internal Helpers ----------------------
def _extract_largest_bbox(contours):
    """Returns bounding box (x, y, w, h) for the largest contour."""
    largest = max(contours, key=cv2.contourArea)
    return cv2.boundingRect(largest)


def _update_tracking_mode(current_time):
    """Determines whether the user is currently tracking the object.
    Updates gaze state and plays corresponding mode-change sounds."""
    if gaze.is_user_tracking_object():
        state.user_is_tracking = True
        state.last_gaze_time = current_time
        state.gaze_lost = False

        if state.current_gaze_mode != "user":
            sound.play_user_mode_sound()
            state.current_gaze_mode = "user"

        _set_tracking_label("User", (0, 255, 0))

    else:
        state.user_is_tracking = False

        if state.current_gaze_mode != "computer":
            sound.play_computer_mode_sound()
            state.current_gaze_mode = "computer"

        _set_tracking_label("Computer", (0, 0, 255))


def _set_tracking_label(mode, color):
    """Updates the mutable TRACKING_MODE_LABEL with new mode and color."""
    config.TRACKING_MODE_LABEL["text"] = f"Tracking mode: {mode}"
    config.TRACKING_MODE_LABEL["color"] = color


def _handle_gaze_button_interaction(current_time):
    """Dwell-to-press: requires continuous gaze on button for BUTTON_DWELL_SECONDS"""
    on_button = gaze.is_gaze_on_rect(config.BUTTON_RECT, config.GAZE_BUTTON_TOLERANCE)

    # Reset on exit
    if not on_button:
        state.button_dwell_start_time = None
        state.current_button_progress = 0.0
        return

    # Start dwell
    if state.button_dwell_start_time is None:
        state.button_dwell_start_time = current_time
        state.current_button_progress = 0.0
        return

    # Update progress
    dwell = current_time - state.button_dwell_start_time
    state.current_button_progress = max(0.0, min(1.0, dwell / config.BUTTON_DWELL_SECONDS))

    # Fire only after dwell time
    if dwell >= config.BUTTON_DWELL_SECONDS:

        if config.IS_GRAYSCALE:
            sound.play_cognitive_aid_disabled_sound()
            config.IS_GRAYSCALE = False
        else:
            sound.play_cognitive_aid_enabled_sound()
            config.IS_GRAYSCALE = True

        # Reset so user must dwell again
        state.button_dwell_start_time = None
        state.current_button_progress = 0.0


def _handle_pause_quit(wait_time, app, paused):
    """Handles pause/quit key inputs."""
    key = cv2.waitKey(wait_time) & 0xFF

    # Map keys directly
    if key == ord('q'):
        app.quit()
        return None  # signal to exit main loop
    elif key == ord(' '):
        return not paused  # toggle pause

    return paused


def _handle_attention_timeout(canvas, current_time):
    """If gaze timeout exceeded, draw prompt and play beep (with cooldown)."""
    if (current_time - state.last_gaze_time) > config.GAZE_TIMEOUT_SECONDS:
        render.draw_attention_prompt(canvas)
        if (current_time - state.last_user_not_here_beep_time) > config.BEEP_TIMEOUT_SECONDS:
            sound.play_user_not_here_sound()
            state.last_user_not_here_beep_time = current_time
        return True
    return False


def _build_processing_mask(frame):
    """Convert frame to HSV, used for contour detection only."""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower = np.array([config.HUE_MIN, config.SAT_MIN, config.VAL_MIN])
    upper = np.array([config.HUE_MAX, config.SAT_MAX, config.VAL_MAX])
    return cv2.inRange(hsv, lower, upper)


def _detect_eye_closure(eye, duration, current_time):
    """Generic function to detect if the specified eye has been closed for the given duration.
    Returns True if closure is detected (and resets the timer), False otherwise.
    """
    if eye not in ("LEFT", "RIGHT"):
        raise ValueError("Eye must be 'LEFT' or 'RIGHT'")

    # Get the corresponding pupil diameter and timer attribute
    pupil_diameter = state.left_pupil_diameter if eye == "LEFT" else state.right_pupil_diameter
    timer_attr = f"{eye.lower()}_eye_close_start_time"

    # Check if eye is closed (pupil diameter == 0.0)
    is_eye_closed = pupil_diameter == 0.0

    if is_eye_closed:
        # Get current timer value
        start_time = getattr(state, timer_attr)

        if start_time is None:
            # Start timing
            setattr(state, timer_attr, current_time)
            return False
        elif current_time - start_time >= duration:
            # Closure detected: reset timer and return True
            setattr(state, timer_attr, None)
            return True
    else:
        # Eye is open: reset timer
        setattr(state, timer_attr, None)

    return False

def _handle_tracking_lock_toggle(frame, current_time):
    """Feature-specific handler for Tracking Lock: toggles based on right eye closure."""
    if _detect_eye_closure("RIGHT", config.RIGHT_EYE_CLOSURE_SECONDS, current_time) and state.left_pupil_diameter > 0.0:
        # Toggle tracking lock state
        state.tracking_lock = not state.tracking_lock

        if state.tracking_lock:
            config.TRACKING_LOCK_LABEL["text"] = "Tracking Lock: 'ON'"
            config.TRACKING_LOCK_LABEL["color"] = (0, 255, 255)
            sound.play_tracking_lock_enabled_sound()
            state.user_is_tracking = False
            state.current_gaze_mode = "computer"
            _set_tracking_label("Computer", (0, 0, 255))
        else:
            config.TRACKING_LOCK_LABEL["text"] = "Tracking Lock: 'OFF'"
            config.TRACKING_LOCK_LABEL["color"] = (255, 255, 0)
            sound.play_tracking_lock_disabled_sound()

    render.draw_tracking_label(frame, config.TRACKING_LOCK_LABEL)