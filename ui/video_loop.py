# video_loop.py
# Runs the real-time video display loop. Handles video capture,
# gaze detection, tracking state updates, interaction logic, and UI rendering.

import time
import cv2
import numpy as np

from core import state, config, sound, gaze
from ui import render

# ---------------------- Video Display Loop ----------------------
def show_video(cap, wait_time, app):
    paused = False
    frame = None
    tracking_label = config.TRACKING_MODE_LABEL
    cv2.namedWindow('Main Window', cv2.WINDOW_NORMAL)

    while True:
        if not paused:
            success, frame = cap.read()
            if not success:
                print("Warning: Frame read failed.")
                continue

        current_time = time.time()

        # HSV mask to isolate tracked object
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower = np.array([config.HUE_MIN, config.SAT_MIN, config.VAL_MIN])
        upper = np.array([config.HUE_MAX, config.SAT_MAX, config.VAL_MAX])
        mask = cv2.inRange(hsv, lower, upper)

        # Draw gaze location
        render.draw_gaze_point(frame)

        # Process tracking object if detected
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            x, y, w, h = _extract_largest_bbox(contours)
            state.target_x, state.target_y = x + w // 2, y + h // 2

            _update_tracking_mode(current_time)
            render.draw_tracking_overlay(frame, (x, y, w, h), tracking_label["color"])

            _handle_gaze_button_interaction(current_time)

        # Show mode label (User / Computer)
        render.draw_tracking_label(frame, tracking_label)

        # Prompt if gaze lost
        if current_time - state.last_gaze_time > config.GAZE_TIMEOUT_SECONDS:
            render.draw_attention_prompt(frame)
            if current_time - state.last_user_not_here_beep_time > 2:
                sound.play_user_not_here_sound()
                state.last_user_not_here_beep_time = current_time

        # UI buttons and overlays
        render.draw_button_overlay(frame)

        # Display frame
        cv2.imshow('Main Window', frame)

        # Handle key inputs
        key = cv2.waitKey(wait_time) & 0xFF
        if key == ord(' '):
            paused = not paused
        elif key == ord('q'):
            app.quit()
            break

    cap.release()
    cv2.destroyAllWindows()


# ---------------------- Internal Helpers ----------------------

def _extract_largest_bbox(contours):
    """Returns bounding box (x, y, w, h) for the largest contour."""
    largest = max(contours, key=cv2.contourArea)
    return cv2.boundingRect(largest)


def _update_tracking_mode(current_time):
    """
    Determines whether the user is currently tracking the object.
    Updates gaze state and plays corresponding mode-change sounds.
    """
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
    """
    Triggers sound and cooldown when the user's gaze is focused
    on the interactive button.
    """
    if gaze.is_gaze_on_rect(config.BUTTON_RECT):
        if current_time - state.last_button_press_time > config.BUTTON_PRESSED_COOLDOWN:
            sound.play_button_pressed_sound()
            state.last_button_press_time = current_time