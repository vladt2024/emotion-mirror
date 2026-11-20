"""Camera -> Signals loop. Frames are processed and dropped immediately; nothing is stored."""

from __future__ import annotations

import time
from collections.abc import Callable, Iterator

from .camera import Camera, CameraError
from .signals import Signals

MAX_CONSECUTIVE_FAILURES = 50


def iter_signals(
    camera: Camera,
    perception,
    fps: float,
    should_stop: Callable[[], bool] = lambda: False,
) -> Iterator[tuple[Signals, float]]:
    """Yield (signals, monotonic_time) at roughly `fps` frames per second."""
    if fps <= 0:
        raise ValueError("fps must be positive")
    interval = 1.0 / fps
    t0 = time.monotonic()
    last_ts = -1
    failures = 0

    while not should_stop():
        start = time.monotonic()
        frame = camera.read()
        if frame is None:
            failures += 1
            if failures >= MAX_CONSECUTIVE_FAILURES:
                raise CameraError("The camera stopped delivering frames.")
        else:
            failures = 0
            ts = max(int((start - t0) * 1000), last_ts + 1)  # MediaPipe needs increasing ts
            last_ts = ts
            signals = perception.process(frame, ts)
            del frame  # drop the image right away
            yield signals, start

        remaining = interval - (time.monotonic() - start)
        if remaining > 0:
            time.sleep(remaining)
