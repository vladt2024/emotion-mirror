"""The only data that leaves the perception layer: a handful of numbers per frame."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Signals:
    """Numbers extracted from one camera frame. The frame itself is never kept.

    Any field is None when it could not be measured reliably in this frame.
    """

    present: bool
    # (shoulder_y - ear_y) / shoulder_width. Drops when the head sinks toward the shoulders.
    neck_ratio: float | None = None
    # Angle of the shoulder line in degrees. 0 means level shoulders.
    shoulder_tilt: float | None = None
    # Horizontal face width as a fraction of the frame width. Grows as you lean in.
    face_width: float | None = None
