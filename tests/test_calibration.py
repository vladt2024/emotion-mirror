import pytest

from emotion_mirror.calibration import (
    MIN_SAMPLES,
    Baseline,
    CalibrationError,
    Calibrator,
    load_baseline,
    save_baseline,
)
from emotion_mirror.signals import Signals


def frame(neck=0.5, tilt=1.0, face=0.2):
    return Signals(present=True, neck_ratio=neck, shoulder_tilt=tilt, face_width=face)


def test_median_ignores_outliers():
    c = Calibrator()
    for _ in range(MIN_SAMPLES):
        c.add(frame(neck=0.5))
    c.add(frame(neck=5.0))  # glitch
    assert c.result().neck_ratio == pytest.approx(0.5)


def test_unusable_frames_are_skipped():
    c = Calibrator()
    assert not c.add(Signals(present=False))
    assert not c.add(Signals(present=True, neck_ratio=0.5, shoulder_tilt=None, face_width=0.2))
    assert c.samples == 0


def test_too_few_samples_fails():
    c = Calibrator()
    for _ in range(MIN_SAMPLES - 1):
        c.add(frame())
    with pytest.raises(CalibrationError):
        c.result()


def test_save_and_load_roundtrip(tmp_path):
    b = Baseline(neck_ratio=0.51, shoulder_tilt=1.5, face_width=0.22)
    path = save_baseline(b, tmp_path / "nested" / "baseline.json")
    assert load_baseline(path) == b


def test_missing_and_corrupt_files(tmp_path):
    with pytest.raises(CalibrationError):
        load_baseline(tmp_path / "nope.json")
    bad = tmp_path / "bad.json"
    bad.write_text("{}", encoding="utf-8")
    with pytest.raises(CalibrationError):
        load_baseline(bad)
