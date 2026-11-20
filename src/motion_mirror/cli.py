"""Command line interface: download-models, calibrate, run, default-rules."""

from __future__ import annotations

import argparse
import sys
import time
import urllib.request
from pathlib import Path

from . import __version__
from .paths import models_dir

_MODEL_BASE = "https://storage.googleapis.com/mediapipe-models"
MODEL_URLS = {
    "face_landmarker.task": f"{_MODEL_BASE}/face_landmarker/face_landmarker/float16/1/face_landmarker.task",
    "pose_landmarker_lite.task": f"{_MODEL_BASE}/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task",
}


def cmd_download_models(args: argparse.Namespace) -> int:
    target = models_dir()
    target.mkdir(parents=True, exist_ok=True)
    for name, url in MODEL_URLS.items():
        dest = target / name
        if dest.exists() and not args.force:
            print(f"{name}: already present")
            continue
        print(f"{name}: downloading...")
        tmp = dest.with_suffix(dest.suffix + ".part")
        urllib.request.urlretrieve(url, tmp)
        tmp.replace(dest)
    print(f"Models are in {target}")
    return 0


def cmd_calibrate(args: argparse.Namespace) -> int:
    from .calibration import CalibrationError, Calibrator, save_baseline
    from .camera import Camera
    from .perception import Perception
    from .pipeline import iter_signals

    print("Sit the way you want to sit: back supported, screen at eye level, relaxed shoulders.")
    print("Make sure your face and both shoulders are visible.")
    for n in (3, 2, 1):
        print(f"Starting in {n}...", flush=True)
        time.sleep(1)

    perception = Perception()
    calibrator = Calibrator()
    deadline = time.monotonic() + args.seconds
    try:
        with Camera(args.camera) as camera:
            for signals, now in iter_signals(camera, perception, args.fps, lambda: time.monotonic() >= deadline):
                calibrator.add(signals)
    except KeyboardInterrupt:
        print("Cancelled.")
        return 1
    finally:
        perception.close()

    try:
        baseline = calibrator.result()
    except CalibrationError as exc:
        print(f"Calibration failed: {exc}", file=sys.stderr)
        return 1
    path = save_baseline(baseline)
    print(f"Calibration saved to {path} ({calibrator.samples} frames used).")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    from .aggregator import Aggregator
    from .calibration import load_baseline
    from .camera import Camera
    from .notifier import Notifier
    from .perception import Perception
    from .pipeline import iter_signals
    from .rules import RuleEngine, load_rules

    baseline = load_baseline()
    rules, settings = load_rules(Path(args.rules) if args.rules else None)
    aggregator = Aggregator(baseline)
    engine = RuleEngine(rules, settings)
    notifier = Notifier()
    perception = Perception()

    print("Motion Mirror is running. Press Ctrl+C to stop. Video is processed in memory and never saved.")
    last_report = 0.0
    try:
        with Camera(args.camera) as camera:
            for signals, now in iter_signals(camera, perception, args.fps):
                metrics = aggregator.update(signals, now)
                if args.verbose and now - last_report >= 5.0:
                    last_report = now
                    shown = {k: (None if v is None else round(v, 2)) for k, v in metrics.items()}
                    print(f"present={signals.present} {shown}", flush=True)
                for alert in engine.evaluate(metrics, now):
                    if args.dry_run:
                        print(f"[dry-run] {alert.rule_id}: {alert.text}", flush=True)
                    else:
                        if args.verbose:
                            print(f"[alert] {alert.rule_id}: {alert.text}", flush=True)
                        notifier.send(alert.title, alert.text)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        perception.close()
        notifier.close()
    return 0


def cmd_default_rules(_: argparse.Namespace) -> int:
    from .rules import default_rules_text

    sys.stdout.write(default_rules_text())
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="motion-mirror", description="Local-first wellbeing copilot.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("download-models", help="Download the MediaPipe models (once).")
    p.add_argument("--force", action="store_true", help="Download again even if present.")
    p.set_defaults(func=cmd_download_models)

    p = sub.add_parser("calibrate", help="Record your 'sitting well' reference.")
    p.add_argument("--seconds", type=float, default=10.0)
    p.add_argument("--camera", type=int, default=0)
    p.add_argument("--fps", type=float, default=6.0)
    p.set_defaults(func=cmd_calibrate)

    p = sub.add_parser("run", help="Watch posture and sitting time and show nudges.")
    p.add_argument("--rules", help="Path to your own rules YAML (see `default-rules`).")
    p.add_argument("--camera", type=int, default=0)
    p.add_argument("--fps", type=float, default=6.0)
    p.add_argument("--verbose", action="store_true", help="Print metrics every 5 seconds to tune thresholds.")
    p.add_argument("--dry-run", action="store_true", help="Print nudges instead of showing notifications.")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("default-rules", help="Print the default rules YAML to copy and edit.")
    p.set_defaults(func=cmd_default_rules)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (OSError, RuntimeError, ValueError) as exc:  # OSError covers network and file errors
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
