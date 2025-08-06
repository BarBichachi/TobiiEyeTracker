# state.py
# Shared mutable runtime state for gaze tracking, attention, and UI behavior.
# Used to coordinate values across modules without using global declarations.

# ---------------------- Eye Openness ----------------------
eye_openness_data = {
    "left_eye_validity": False,
    "right_eye_validity": False,
    "left_eye_openness_value": 0.0,
    "right_eye_openness_value": 0.0
}

# ---------------------- Gaze & Target ----------------------
gaze_x, gaze_y = 0, 0
target_x, target_y = 0, 0

# ---------------------- Screen Dimensions ----------------------
screen_width = 0
screen_height = 0

# ---------------------- Timestamps ----------------------
timestamp = 0
last_gaze_time = 0
last_user_not_here_beep_time = 0
last_button_press_time = 0

# ---------------------- Status Flags ----------------------
gaze_lost = False
user_is_tracking = False
current_gaze_mode = None

# ---------------------- UI References ----------------------
graph_window = None

