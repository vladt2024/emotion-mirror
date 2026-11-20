import random

import pytest

from motion_mirror.rules import RuleEngine, RulesError, Settings, load_rules, parse_rules


def make_engine(max_per_hour=4):
    rules, _ = parse_rules(
        {
            "rules": [
                {
                    "id": "slouch",
                    "metric": "neck_ratio_rel",
                    "below": 0.85,
                    "for_seconds": 60,
                    "cooldown_minutes": 10,
                    "messages": ["sit up"],
                },
                {
                    "id": "sedentary",
                    "metric": "sitting_minutes",
                    "above": 50,
                    "messages": ["move"],
                },
            ]
        }
    )
    return RuleEngine(rules, Settings(max_per_hour=max_per_hour), random.Random(0))


def m(neck=1.0, sitting=0.0):
    return {"neck_ratio_rel": neck, "tilt_dev": 0.0, "face_width_rel": 1.0, "sitting_minutes": sitting}


def test_default_rules_are_valid():
    rules, settings = load_rules()
    assert rules and settings.max_per_hour >= 1


def test_fires_only_after_sustained_duration():
    e = make_engine()
    assert e.evaluate(m(neck=0.7), 0) == []
    assert e.evaluate(m(neck=0.7), 59) == []
    alerts = e.evaluate(m(neck=0.7), 60)
    assert [a.rule_id for a in alerts] == ["slouch"]


def test_good_posture_resets_the_timer():
    e = make_engine()
    e.evaluate(m(neck=0.7), 0)
    e.evaluate(m(neck=0.7), 50)
    e.evaluate(m(neck=1.0), 55)  # sits up: timer resets
    assert e.evaluate(m(neck=0.7), 60) == []
    assert e.evaluate(m(neck=0.7), 119) == []
    assert len(e.evaluate(m(neck=0.7), 120)) == 1


def test_cooldown_blocks_repeat_then_allows():
    e = make_engine()
    e.evaluate(m(neck=0.7), 0)
    assert len(e.evaluate(m(neck=0.7), 60)) == 1
    assert e.evaluate(m(neck=0.7), 300) == []  # within 10 min cooldown
    assert len(e.evaluate(m(neck=0.7), 60 + 600)) == 1


def test_missing_metric_never_fires():
    e = make_engine()
    metrics = m()
    metrics["neck_ratio_rel"] = None
    for t in range(0, 600, 10):
        assert e.evaluate(metrics, t) == []


def test_one_alert_at_a_time_in_rule_order():
    e = make_engine()
    e.evaluate(m(neck=0.7, sitting=0), 0)  # slouch starts counting
    first = e.evaluate(m(neck=0.7, sitting=60), 60)  # both eligible: rule order wins
    assert [a.rule_id for a in first] == ["slouch"]
    second = e.evaluate(m(neck=0.7, sitting=60), 61)  # slouch is on cooldown now
    assert [a.rule_id for a in second] == ["sedentary"]


def test_hourly_limit():
    e = make_engine(max_per_hour=1)
    e.evaluate(m(neck=0.7, sitting=0), 0)
    assert len(e.evaluate(m(neck=0.7, sitting=60), 60)) == 1
    assert e.evaluate(m(neck=0.7, sitting=60), 61) == []  # limit reached
    assert len(e.evaluate(m(neck=0.7, sitting=60), 3700)) == 1  # window moved on


def test_snooze():
    e = make_engine()
    e.snooze(30, now=0)
    e.evaluate(m(neck=0.7), 0)
    assert e.evaluate(m(neck=0.7), 100) == []
    assert len(e.evaluate(m(neck=0.7), 1801)) == 1


@pytest.mark.parametrize(
    "rule",
    [
        {"id": "a", "metric": "nope", "above": 1, "messages": ["x"]},
        {"id": "a", "metric": "tilt_dev", "messages": ["x"]},
        {"id": "a", "metric": "tilt_dev", "above": 1, "below": 0, "messages": ["x"]},
        {"id": "a", "metric": "tilt_dev", "above": 1, "messages": []},
        {"id": "a", "metric": "tilt_dev", "above": 1, "messages": ["x"], "for_seconds": -1},
    ],
)
def test_invalid_rules_are_rejected(rule):
    with pytest.raises(RulesError):
        parse_rules({"rules": [rule]})


def test_duplicate_ids_rejected():
    r = {"id": "a", "metric": "tilt_dev", "above": 1, "messages": ["x"]}
    with pytest.raises(RulesError):
        parse_rules({"rules": [r, r]})
