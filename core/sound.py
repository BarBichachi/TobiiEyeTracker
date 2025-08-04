# sound.py
# Handles all audio feedback logic for different tracking and interaction events.
# Uses non-blocking playback for responsiveness.

from playsound import playsound
from core import config

def play_user_mode_sound():
    playsound(str(config.USER_MODE_SOUND), block=False)

def play_computer_mode_sound():
    playsound(str(config.COMPUTER_MODE_SOUND), block=False)

def play_user_not_here_sound():
    playsound(str(config.USER_NOT_HERE_SOUND), block=False)

def play_button_pressed_sound():
    playsound(str(config.BUTTON_PRESSED_SOUND), block=False)