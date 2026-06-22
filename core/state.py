# state.py
# Central shared runtime state for gaze tracking, attention logic, and UI coordination.
# This module intentionally holds mutable process-wide state accessed by multiple threads.

# region Gaze & Target Coordinates
# Current smoothed gaze position (pixel coordinates)
gaze_x = 0
gaze_y = 0

# Current tracked target position (pixel coordinates)
target_x = 0
target_y = 0

# Kalman filters for gaze smoothing (initialized on first gaze sample)
kalman_x = None
kalman_y = None
# endregion


# region Pupil Data
# Last known pupil diameter values (mm)
left_pupil_diameter = 0.0
right_pupil_diameter = 0.0

# Fixed on-screen positions used only for visualization
left_pupil_position = (1650, 950)
right_pupil_position = (1800, 950)
# endregion


# region Screen & Video
# Active video frame dimensions (pixels)
screen_width = 0
screen_height = 0
# endregion


# region Timing & Interaction
# Current timestamp (seconds, wall-clock based)
timestamp = 0.0

# Last time a valid gaze sample was received (epoch seconds)
last_gaze_time = 0.0

# Last time the "user not here" sound was played
last_user_not_here_beep_time = 0.0

# Button dwell tracking
button_dwell_start_time = None
current_button_progress = 0.0

# Eye-closure timing (used for gestures / mode switching)
right_eye_close_start_time = None
left_eye_close_start_time = None

# Mode / target timing
last_mode_switch_time = 0.0
last_target_ts = 0.0
# endregion


# region Status Flags
# True when no valid gaze is currently detected
gaze_lost = False

# True when user gaze is actively tracking the target
user_is_tracking = False

# Current gaze interaction mode (implementation-defined)
current_gaze_mode = None

# True when tracking lock is enabled
tracking_lock = False

# Internal latch flags for interaction logic
has_latch = False
gaze_on_latched = False

# True when a target is currently present on screen
target_present = False
# endregion


# region UI References
# Live graph window instance (Qt widget)
graph_window = None
# endregion


# region On-screen Toast (transient feedback)
# Active toast message, color, icon key, and absolute expiry time (epoch seconds)
toast_text = ""
toast_color = (255, 255, 255)
toast_icon = None
toast_expiry = 0.0
# endregion


# region UI Toggles
# Main window fullscreen (gaze->pixel mapping is only correct fullscreen)
fullscreen = True
# Whether the expanded hotkey legend is shown
show_legend = False
# Whether the head/eye position guide overlay is shown
show_position_guide = False
# endregion


# region User Position Guide (head/eye alignment in the tracker track box)
# Normalized (x, y, z) eye positions; (0.5, 0.5, 0.5) is centered. None until received.
user_left_pos = None
user_left_valid = False
user_right_pos = None
user_right_valid = False
last_user_position_time = 0.0
# endregion