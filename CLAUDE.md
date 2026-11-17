# Emotion Mirror: notes for Claude Code

Local-first wellbeing copilot. Webcam -> signals -> YAML rules -> notification. Video never leaves the PC and is never stored. See README.md for the product and privacy promises; they are requirements, not marketing.

## Architecture (src/emotion_mirror/)
- `camera.py` OpenCV capture. Frames stay in memory.
- `perception.py` MediaPipe Face + Pose Landmarker -> `Signals`. The ONLY module that imports MediaPipe.
- `signals.py` the only data crossing out of perception: a few floats per frame.
- `calibration.py` per-user baseline (median of a few seconds sitting well), JSON in `~/.emotion-mirror/`.
- `aggregator.py` smoothing + relative metrics + continuous sitting time.
- `rules.py` + `default_rules.yaml` YAML rules, sustain time, cooldown, hourly limit, snooze.
- `notifier.py` desktop-notifier with print fallback.
- `pipeline.py`, `cli.py` loop and commands.

## Rules for changes
- Never write frames or images to disk, never add network calls at runtime (model download is the one explicit exception, in `cli.py`).
- No administrator mode, multi-user reporting or sending data to third parties (EU AI Act, see README "Intended use").
- Keep perception swappable: other modules must not import MediaPipe or OpenCV types beyond `camera.py`.
- Everything except `camera.py` and `perception.py` must be testable without a camera or models. Time is passed in as `now`, never read inside logic.

## Roadmap
v0.1 posture + sedentary + calibration (this). v0.2 blink/yawn/fatigue + adaptive Pomodoro. v0.3 NeuroBrix phrases the messages (keep YAML templates as fallback, NeuroBrix is optional at runtime and has no documented HTTP/Python API in its README: integrate through its CLI `serve`/`run`, and verify against current docs). v0.4 mood check-in, voice (NeuroBrix Whisper-V3-Turbo / Kokoro-82M), community rules.

## Dev
```
pip install -e ".[dev]"
pytest
```
