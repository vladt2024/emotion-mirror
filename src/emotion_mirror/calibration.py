"""Per-user calibration: your own 'sitting well' reference, stored locally as JSON."""

from __future__ import annotations

import json
import statistics
from dataclasses import asdict, dataclass
from pathlib import Path

from .paths import baseline_path
from .signals import Signals

MIN_SAMPLES = 30


class CalibrationError(RuntimeError):
    pass


@dataclass(frozen=True)
class Baseline:
    neck_ratio: float
    shoulder_tilt: float
    face_width: float
    version: int = 1


class Calibrator:
    """Collects frames while the user sits upright and returns the median of each signal."""

    def __init__(self) -> None:
        self._neck: list[float] = []
        self._tilt: list[float] = []
        self._face: list[float] = []

    def add(self, s: Signals) -> bool:
        """Add a frame. Returns True if the frame was usable (all signals measured)."""
        if not s.present or s.neck_ratio is None or s.shoulder_tilt is None or s.face_width is None:
            return False
        self._neck.append(s.neck_ratio)
        self._tilt.append(s.shoulder_tilt)
        self._face.append(s.face_width)
        return True

    @property
    def samples(self) -> int:
        return len(self._neck)

    def result(self) -> Baseline:
        if self.samples < MIN_SAMPLES:
            raise CalibrationError(
                f"Only {self.samples} usable frames (need {MIN_SAMPLES}). "
                "Make sure your face, ears and both shoulders are visible to the camera."
            )
        return Baseline(
            neck_ratio=statistics.median(self._neck),
            shoulder_tilt=statistics.median(self._tilt),
            face_width=statistics.median(self._face),
        )


def save_baseline(baseline: Baseline, path: Path | None = None) -> Path:
    path = path or baseline_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(baseline), indent=2), encoding="utf-8")
    return path


def load_baseline(path: Path | None = None) -> Baseline:
    path = path or baseline_path()
    if not path.exists():
        raise CalibrationError(f"No calibration found at {path}. Run `emotion-mirror calibrate`.")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return Baseline(
            neck_ratio=float(data["neck_ratio"]),
            shoulder_tilt=float(data["shoulder_tilt"]),
            face_width=float(data["face_width"]),
            version=int(data.get("version", 1)),
        )
    except (KeyError, ValueError, TypeError) as exc:
        raise CalibrationError(f"Calibration file {path} is corrupt: {exc}. Recalibrate.") from exc
