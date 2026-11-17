# Emotion Mirror

Local-first wellbeing copilot for people who work at a computer. It uses your webcam and on-device AI ([NeuroBrix](https://neurobrix.ai)) to notice poor posture, long sitting spells, fatigue and tension, and gives you gentle, personalised nudges.

**Your video never leaves your PC and is never saved.**

> Status: v0.1 (early). Posture, sitting-time nudges and calibration work in code and are unit-tested, but the camera pipeline has not been field-tested on real hardware yet. Expect to tune thresholds. NeuroBrix is not wired in yet (planned for v0.3); v0.1 uses message templates from the rules file.

## Quick start

Requires Python 3.10+ and a webcam.

```bash
git clone https://github.com/vladt2024/emotion-mirror.git
cd emotion-mirror
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

emotion-mirror download-models   # once: fetches the two MediaPipe models (the only network use)
emotion-mirror calibrate         # sit well for 10 seconds
emotion-mirror run --verbose     # --verbose prints metrics every 5 s so you can tune thresholds
```

Useful options:

- `emotion-mirror run --dry-run` prints nudges instead of showing notifications.
- `emotion-mirror default-rules > my_rules.yaml`, edit it, then `emotion-mirror run --rules my_rules.yaml`.
- Files live in `~/.emotion-mirror/` (set `EMOTION_MIRROR_HOME` to change it). Delete the folder to remove everything.
- On macOS, allow camera access for your terminal or editor the first time.

Run the tests (no camera needed): `pytest`.

## How it works

One pipeline, running entirely on your machine:

```
camera -> signal extractor -> YAML rule engine -> local LLM (NeuroBrix) -> desktop notification
          (pose, face landmarks)
```

1. **Signal extractor** turns each frame into a few numbers (e.g. neck-shoulder angle, distance to screen, blink rate) and discards the frame immediately.
2. **Rule engine** reads human-editable YAML rules and decides when a nudge is worth showing.
3. **Local LLM** (via NeuroBrix) phrases the nudge in a short, friendly message.
4. **Notifier** shows it on your desktop, with a per-hour limit, snooze and a quiet mode for meetings.

## Modules and roadmap

| Version | Scope |
|---------|-------|
| v0.1 | Posture, movement / sedentary alerts, per-user calibration |
| v0.2 | Focus and fatigue signals, adaptive Pomodoro |
| v0.3 | Messages generated with NeuroBrix, daily summary |
| v0.4 | Mood check-in (encouragement, breathing exercises, poem on demand), voice, community rules |

A camera-free mode (keyboard and mouse activity only) is planned as an alternative for people who prefer not to use a webcam.

## Privacy principles

- **Everything is local.** No network calls, no cloud inference, no telemetry.
- **No images or video are stored.** Only aggregated numbers are kept, on your own machine, and you can delete them at any time.
- **Opt-in and personal.** You choose to turn it on, and you can turn it off at any time.

## Intended use

Emotion Mirror is a **personal tool for the person using the computer**. It is not designed, and must not be deployed, to monitor employees, students or any other third party.

Inferring emotions of people in workplaces and educational settings is prohibited under the EU AI Act. For that reason the project has no administrator mode, no multi-user reporting and no way to send data to anyone else, and contributions that add them will not be accepted.

## What it is not

- It does not "detect your emotions". It reacts to measurable cues such as posture and expression, and those cues can be wrong.
- It is **not a medical device** and does not diagnose, treat or prevent any condition. If you have persistent pain, fatigue or low mood, please talk to a health professional.

## Getting started

Not available yet. Installation and usage instructions will be added with v0.1.

## Contributing

Issues and ideas are welcome. Please keep the privacy principles and intended use above in mind: changes that weaken them will not be merged.

## License

[Apache-2.0](LICENSE)
