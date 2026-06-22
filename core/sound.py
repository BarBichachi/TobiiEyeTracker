# sound.py
# Audio feedback via the Windows-native winsound (SND_ASYNC): OS-level playback that
# returns immediately and does NOT hold the Python GIL. simpleaudio's play() blocked the
# caller ~1s AND held the GIL, freezing the video loop on every sound-playing event.

from core import config

try:
    import winsound
except ImportError:  # non-Windows: degrade to silent rather than crashing on import
    winsound = None


_SOUND_ENABLED = False
_FAILED_SOUNDS = set()

_PLAY_FLAGS = (winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT) if winsound else 0


# Plays a configured sound asynchronously (non-blocking) if enabled and available
def _play(sound_path):
    if not _SOUND_ENABLED or winsound is None:
        return

    key = str(sound_path)
    if key in _FAILED_SOUNDS:
        return

    if not sound_path.exists():
        _FAILED_SOUNDS.add(key)
        print(f"[Sound] Missing file: {key}")
        return

    try:
        winsound.PlaySound(key, _PLAY_FLAGS)
    except Exception as e:
        _FAILED_SOUNDS.add(key)
        print(f"[Sound] Playback failed: {key} ({e})")


# Enables or disables all sound playback globally
def set_sound_enabled(enabled: bool):
    global _SOUND_ENABLED
    _SOUND_ENABLED = bool(enabled)


# Returns whether sound playback is currently enabled
def is_sound_enabled():
    return _SOUND_ENABLED


# Toggles sound on/off and returns the new state
def toggle_sound_enabled():
    global _SOUND_ENABLED
    _SOUND_ENABLED = not _SOUND_ENABLED
    return _SOUND_ENABLED


# Validates that sound assets exist (winsound needs no preloading); logs any missing ones
def preload_sounds():
    paths = [
        config.USER_MODE_SOUND, config.COMPUTER_MODE_SOUND, config.USER_NOT_HERE_SOUND,
        config.BUTTON_PRESSED_SOUND, config.TRACKING_LOCK_ENABLED_SOUND,
        config.TRACKING_LOCK_DISABLED_SOUND, config.COGNITIVE_AID_ENABLED_SOUND,
        config.COGNITIVE_AID_DISABLED_SOUND, config.SWITCHED_TARGET_SOUND,
    ]
    for p in paths:
        if not p.exists():
            _FAILED_SOUNDS.add(str(p))
            print(f"[Sound] Missing file: {p}")


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