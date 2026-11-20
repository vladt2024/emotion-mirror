"""Turns noisy per-frame Signals into stable metrics that rules can use."""

from __future__ import annotations

from .calibration import Baseline
from .signals import Signals

# Metric names a rule may refer to.
METRIC_NAMES = frozenset(
    {
        "neck_ratio_rel",  # neck_ratio / baseline. Below 1.0 means slouching relative to you.
        "tilt_dev",  # |shoulder_tilt - baseline| in degrees
        "face_width_rel",  # face_width / baseline. Above 1.0 means closer to the screen.
        "sitting_minutes",  # minutes of continuous presence (short absences do not reset it)
    }
)

Metrics = dict[str, float | None]


class Aggregator:
    def __init__(self, baseline: Baseline, ema_alpha: float = 0.25, break_seconds: float = 300.0):
        if not 0.0 < ema_alpha <= 1.0:
            raise ValueError("ema_alpha must be in (0, 1]")
        self._b = baseline
        self._alpha = ema_alpha
        self._break = break_seconds
        self._neck: float | None = None
        self._tilt: float | None = None
        self._face: float | None = None
        self._sitting_start: float | None = None
        self._last_present: float | None = None

    def update(self, s: Signals, now: float) -> Metrics:
        """Feed one frame's signals at time `now` (seconds, monotonic) and get current metrics."""
        self._update_sitting(s.present, now)
        self._neck = self._smooth(self._neck, s.neck_ratio if s.present else None)
        self._tilt = self._smooth(self._tilt, s.shoulder_tilt if s.present else None)
        self._face = self._smooth(self._face, s.face_width if s.present else None)

        return {
            "neck_ratio_rel": self._ratio(self._neck, self._b.neck_ratio),
            "tilt_dev": None if self._tilt is None else abs(self._tilt - self._b.shoulder_tilt),
            "face_width_rel": self._ratio(self._face, self._b.face_width),
            "sitting_minutes": self._sitting_minutes(now),
        }

    def _smooth(self, previous: float | None, value: float | None) -> float | None:
        if value is None:
            return None  # reset: do not carry stale values across a gap
        if previous is None:
            return value
        return self._alpha * value + (1.0 - self._alpha) * previous

    @staticmethod
    def _ratio(value: float | None, reference: float) -> float | None:
        if value is None or abs(reference) < 1e-6:
            return None
        return value / reference

    def _update_sitting(self, present: bool, now: float) -> None:
        if not present:
            return
        gap_too_long = self._last_present is not None and now - self._last_present > self._break
        if self._sitting_start is None or gap_too_long:
            self._sitting_start = now
        self._last_present = now

    def _sitting_minutes(self, now: float) -> float | None:
        if self._sitting_start is None or self._last_present is None:
            return 0.0
        if now - self._last_present > self._break:
            return 0.0  # you left long enough ago to count as a break
        return (now - self._sitting_start) / 60.0
