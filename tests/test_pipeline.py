import pytest

from emotion_mirror.camera import CameraError
from emotion_mirror.pipeline import MAX_CONSECUTIVE_FAILURES, iter_signals
from emotion_mirror.signals import Signals


class FakeCamera:
    def __init__(self, frames):
        self._frames = iter(frames)

    def read(self):
        return next(self._frames, None)


class FakePerception:
    def __init__(self):
        self.timestamps = []

    def process(self, frame, timestamp_ms):
        self.timestamps.append(timestamp_ms)
        return Signals(present=True)


def test_timestamps_strictly_increase_even_at_high_fps():
    perception = FakePerception()
    cam = FakeCamera([object()] * 5)
    seen = 0

    def stop():
        return seen >= 5

    for _ in iter_signals(cam, perception, fps=10_000, should_stop=stop):
        seen += 1
    assert perception.timestamps == sorted(set(perception.timestamps))
    assert len(perception.timestamps) == 5


def test_camera_that_never_delivers_raises():
    cam = FakeCamera([])
    with pytest.raises(CameraError):
        for _ in iter_signals(cam, FakePerception(), fps=100_000):
            pass
    assert MAX_CONSECUTIVE_FAILURES > 0


def test_invalid_fps():
    with pytest.raises(ValueError):
        next(iter_signals(FakeCamera([]), FakePerception(), fps=0))
