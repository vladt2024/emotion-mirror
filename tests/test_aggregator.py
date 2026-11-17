import pytest

from emotion_mirror.aggregator import Aggregator
from emotion_mirror.calibration import Baseline
from emotion_mirror.signals import Signals

BASE = Baseline(neck_ratio=0.5, shoulder_tilt=2.0, face_width=0.2)


def good():
    return Signals(present=True, neck_ratio=0.5, shoulder_tilt=2.0, face_width=0.2)


def test_metrics_relative_to_baseline():
    a = Aggregator(BASE, ema_alpha=1.0)
    m = a.update(Signals(True, neck_ratio=0.4, shoulder_tilt=10.0, face_width=0.3), now=0)
    assert m["neck_ratio_rel"] == pytest.approx(0.8)
    assert m["tilt_dev"] == pytest.approx(8.0)
    assert m["face_width_rel"] == pytest.approx(1.5)


def test_smoothing_dampens_a_single_outlier_frame():
    a = Aggregator(BASE, ema_alpha=0.25)
    for t in range(10):
        a.update(good(), now=t)
    # A raw frame at 0.4 would read 0.8 (below the 0.85 slouch threshold)...
    m = a.update(Signals(True, neck_ratio=0.4, shoulder_tilt=2.0, face_width=0.2), now=10)
    # ...but smoothed it stays above it.
    assert m["neck_ratio_rel"] > 0.85


def test_absent_resets_posture_metrics():
    a = Aggregator(BASE)
    a.update(good(), now=0)
    m = a.update(Signals(present=False), now=1)
    assert m["neck_ratio_rel"] is None and m["tilt_dev"] is None and m["face_width_rel"] is None


def test_sitting_minutes_accumulate():
    a = Aggregator(BASE)
    for t in range(0, 601, 60):  # frames keep arriving while you sit
        m = a.update(good(), now=t)
    assert m["sitting_minutes"] == pytest.approx(10.0)


def test_short_absence_does_not_reset_sitting():
    a = Aggregator(BASE, break_seconds=300)
    a.update(good(), now=0)
    a.update(Signals(present=False), now=100)
    m = a.update(good(), now=200)  # gone for 200 s < 300 s
    assert m["sitting_minutes"] == pytest.approx(200 / 60)


def test_long_absence_resets_sitting():
    a = Aggregator(BASE, break_seconds=300)
    a.update(good(), now=0)
    a.update(Signals(present=False), now=100)
    m = a.update(good(), now=1000)  # gone for 1000 s
    assert m["sitting_minutes"] == pytest.approx(0.0)
    m = a.update(good(), now=1060)
    assert m["sitting_minutes"] == pytest.approx(1.0)


def test_invalid_alpha():
    with pytest.raises(ValueError):
        Aggregator(BASE, ema_alpha=0)
