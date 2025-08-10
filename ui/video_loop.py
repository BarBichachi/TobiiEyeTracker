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
                _update_tracking_mode(current_time)
            else:
                # --- Sticky reuse: keep last box for a short grace period ---
                if last_bbox and (current_time - last_bbox_time) < box_stale_seconds:
                    bbox = last_bbox

            # --- Choose a canvas to draw UI on (mask visualization OR color) ---
            canvas = cv2.cvtColor(mask_raw, cv2.COLOR_GRAY2BGR) if config.IS_GRAYSCALE else frame.copy()

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

            # --- Draw tracking box on target if we have one ---
            if bbox is not None:
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
    on_button = gaze.is_gaze_on_rect(config.BUTTON_RECT)

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
        sound.play_button_pressed_sound()
        config.IS_GRAYSCALE = not config.IS_GRAYSCALE
        state.last_button_press_time = current_time

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
