# Emotion Mirror

Local-first wellbeing copilot for people who work at a computer. It uses your webcam and on-device AI ([NeuroBrix](https://neurobrix.ai)) to notice poor posture, long sitting spells, fatigue and tension, and gives you gentle, personalised nudges.

**Your video never leaves your PC and is never saved.**

> Status: early development (pre-v0.1). Nothing here is stable yet.

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
