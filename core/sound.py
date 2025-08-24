# sound.py
# Handles all audio feedback logic for different tracking and interaction events.
# Uses non-blocking playback for responsiveness.

import simpleaudio as sa
from core import config

_user_sound = sa.WaveObject.from_wave_file(str(config.USER_MODE_SOUND))
_computer_sound = sa.WaveObject.from_wave_file(str(config.COMPUTER_MODE_SOUND))
_user_not_here_sound = sa.WaveObject.from_wave_file(str(config.USER_NOT_HERE_SOUND))
_button_pressed_sound = sa.WaveObject.from_wave_file(str(config.BUTTON_PRESSED_SOUND))
_tracking_lock_enabled_sound = sa.WaveObject.from_wave_file(str(config.TRACKING_LOCK_ENABLED_SOUND))
_tracking_lock_disabled_sound = sa.WaveObject.from_wave_file(str(config.TRACKING_LOCK_DISABLED_SOUND))
_cognitive_aid_enabled_sound = sa.WaveObject.from_wave_file(str(config.COGNITIVE_AID_ENABLED_SOUND))
_cognitive_aid_disabled_sound = sa.WaveObject.from_wave_file(str(config.COGNITIVE_AID_DISABLED_SOUND))
_switched_target_sound = sa.WaveObject.from_wave_file(str(config.SWITCHED_TARGET_SOUND))

def play_user_mode_sound():
    _user_sound.play()

def play_computer_mode_sound():
    _computer_sound.play()

def play_user_not_here_sound():
    _user_not_here_sound.play()

def play_button_pressed_sound():
    _button_pressed_sound.play()

def play_tracking_lock_enabled_sound():
    _tracking_lock_enabled_sound.play()

def play_tracking_lock_disabled_sound():
    _tracking_lock_disabled_sound.play()

def play_cognitive_aid_enabled_sound():
    _cognitive_aid_enabled_sound.play()

def play_cognitive_aid_disabled_sound():
    _cognitive_aid_disabled_sound.play()

def play_switched_target_sound():
    _switched_target_sound.play()