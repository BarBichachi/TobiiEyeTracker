# TobiiEyeTracker

Real-time, gaze-aware video tracking and cognitive-aid system built around a Tobii eye
tracker. It plays a video, detects on-screen objects via HSV color segmentation, and decides
in real time whether the **user** is actively following an object with their eyes or whether
the **computer** should take over. It provides audio/visual feedback and live gaze analytics.

If no Tobii device is connected, the app automatically falls back to a built-in
**MockEyeTracker**, so it can run for development/demo without hardware.

## Requirements

- **Python 3.10**
- The UI uses **PySide6** (Qt6), **not** PyQt5. Do not install both in the same environment
  (two Qt bindings in one process can crash). See `requirements.txt`.

## Setup

```powershell
# from the project root
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

For running the tests as well:

```powershell
pip install -r requirements-dev.txt
```

## Run

```powershell
python main.py
```

Three windows open:

1. **Main Window** - the video with gaze overlay, target boxes, pupil indicators, and the
   on-screen button.
2. **Trackbars** - live HSV / grayscale tuning for the detection mask.
3. **EyeTracker Analyzer** - live gaze/target delta and entropy graphs with CSV export.

## Controls

### Keyboard (focus the Main Window)

| Key     | Action                                  |
|---------|-----------------------------------------|
| `q`     | Quit                                    |
| `space` | Pause / resume the video                |
| `M`     | Mute / unmute sound (3s on-screen toast)|

### Eye gestures

| Gesture                                        | Action                                  |
|------------------------------------------------|-----------------------------------------|
| Close **left** eye (~1s) while gazing a target | Latch onto that target                  |
| Close **right** eye (~1s), left eye open       | Toggle Tracking Lock                     |
| Dwell-gaze the on-screen button (~1s)          | Toggle Cognitive Aid (grayscale mode)    |
| No gaze detected for ~3s                        | "Are you still here?" prompt + beep      |

### Analyzer window

- **Start / Stop** - begins/stops sampling into the graphs.
- **Export to CSV** - writes the buffered series to `exports/` (gitignored).

## Tracking modes

- **User** - gaze is close enough to the tracked target; the user is following it.
- **Computer** - gaze is not on the target (or Tracking Lock is on); the system takes over.

Mode switches are rate-limited and announced with a label and (when enabled) a sound.

## Configuration

Most behavior is tunable in `core/config.py`, including:

- `SOUND_ENABLED` - master audio switch (also toggled at runtime with `M`).
- HSV defaults (`HUE_*`, `SAT_*`, `VAL_*`) - the single source of truth for the detection
  mask; the trackbars are seeded from these.
- Gaze thresholds, dwell/cooldown timings, Kalman tuning, and latch/focus stickiness.
- `DEFAULT_VIDEO` - the clip to play.

## Project structure

```
core/        domain logic and shared runtime state
  bootstrap.py        startup: tracker, video, UI, threads
  gaze.py             Tobii callback, Kalman smoothing, gaze helpers
  kalman_filter.py    1D constant-velocity filter
  targeting.py        focus selection + latch tracking
  entropy.py          windowed gaze entropy metrics
  mock_eye_tracker.py hardware-free gaze source
  sound.py            lazy, mutable audio feedback
  config.py / state.py
  bbox_utils.py       bbox helpers (groundwork for a future YOLO path)
ui/          rendering and Qt graphs
  video_loop.py       main per-frame loop and interactions
  render.py           overlays, gaze trail/entropy, toasts
  live_graphs.py      PySide6 + pyqtgraph analyzer (main-thread QTimer)
  trackbars.py, target_overlay.py, eye_overlay.py, gaze_trail.py
tobii_research_64/    vendored Tobii SDK (reference only, not imported)
tests/       pytest suite for the pure logic
assets/      sounds and the default video
```

## Tests

```powershell
python -m pytest
```

## Notes

- Gaze is mapped to pixels as `normalized_gaze x video_frame_size`, which assumes the Main
  Window is shown fullscreen at the video's native resolution. If you run it windowed and the
  gaze marker looks offset, that mapping is the thing to revisit.
- Live graphs are driven by a Qt main-thread `QTimer` (all widget access stays on the GUI
  thread); pushing updates from a background thread is unsafe with Qt.
