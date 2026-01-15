# sound.py
# Handles audio feedback for tracking and interaction events.
# Uses non-blocking playback with lazy loading and optional global mute.

import simpleaudio as sa

from core import config


_SOUND_ENABLED = False
_SOUND_CACHE = {}
_FAILED_SOUNDS = set()


# Plays a configured sound if sound is enabled and the file is available
def _play(sound_path):
    if not _SOUND_ENABLED:
        return

    sound = _get_sound(sound_path)
    if sound is not None:
        sound.play()


# Lazily loads and caches a WaveObject, caching failures to avoid log spam
def _get_sound(sound_path):
    key = str(sound_path)

    if key in _FAILED_SOUNDS:
        return None

    cached = _SOUND_CACHE.get(key)
    if cached is not None:
        return cached

    try:
        wave = sa.WaveObject.from_wave_file(key)
    except Exception as e:
        _FAILED_SOUNDS.add(key)
        print(f"[Sound] Failed to load: {key} ({e})")
        return None

    _SOUND_CACHE[key] = wave
    return wave


# Enables or disables all sound playback globally
def set_sound_enabled(enabled: bool):
    global _SOUND_ENABLED
    _SOUND_ENABLED = bool(enabled)


# Preloads all known sound assets (optional; keeps runtime playback consistent)
def preload_sounds():
    _get_sound(config.USER_MODE_SOUND)
    _get_sound(config.COMPUTER_MODE_SOUND)
    _get_sound(config.USER_NOT_HERE_SOUND)
    _get_sound(config.BUTTON_PRESSED_SOUND)
    _get_sound(config.TRACKING_LOCK_ENABLED_SOUND)
    _get_sound(config.TRACKING_LOCK_DISABLED_SOUND)
    _get_sound(config.COGNITIVE_AID_ENABLED_SOUND)
    _get_sound(config.COGNITIVE_AID_DISABLED_SOUND)
    _get_sound(config.SWITCHED_TARGET_SOUND)


# Plays sound when user mode is activated
def play_user_mode_sound():
    _play(config.USER_MODE_SOUND)


# Plays sound when computer mode is activated
def play_computer_mode_sound():
    _play(config.COMPUTER_MODE_SOUND)


# Plays sound when user is detected as absent
def play_user_not_here_sound():
    _play(config.USER_NOT_HERE_SOUND)


# Plays sound when the virtual button is pressed
def play_button_pressed_sound():
    _play(config.BUTTON_PRESSED_SOUND)


# Plays sound when tracking lock is enabled
def play_tracking_lock_enabled_sound():
    _play(config.TRACKING_LOCK_ENABLED_SOUND)


# Plays sound when tracking lock is disabled
def play_tracking_lock_disabled_sound():
    _play(config.TRACKING_LOCK_DISABLED_SOUND)


# Plays sound when cognitive aid is enabled
def play_cognitive_aid_enabled_sound():
    _play(config.COGNITIVE_AID_ENABLED_SOUND)


# Plays sound when cognitive aid is disabled
def play_cognitive_aid_disabled_sound():
    _play(config.COGNITIVE_AID_DISABLED_SOUND)


# Plays sound when the tracked target changes
def play_switched_target_sound():
    _play(config.SWITCHED_TARGET_SOUND)