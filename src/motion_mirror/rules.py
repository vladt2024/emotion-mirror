"""Human-editable YAML rules and the engine that decides when a nudge is worth showing."""

from __future__ import annotations

import random
import time
from collections import deque
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

import yaml

from .aggregator import METRIC_NAMES, Metrics


class RulesError(ValueError):
    pass


@dataclass(frozen=True)
class Rule:
    id: str
    metric: str
    above: float | None
    below: float | None
    for_seconds: float
    cooldown_minutes: float
    title: str
    messages: tuple[str, ...]

    def triggered(self, value: float | None) -> bool:
        if value is None:
            return False
        if self.above is not None:
            return value > self.above
        return value < self.below  # type: ignore[operator]


@dataclass(frozen=True)
class Settings:
    max_per_hour: int = 4


@dataclass(frozen=True)
class Alert:
    rule_id: str
    title: str
    text: str


def default_rules_text() -> str:
    return resources.files("motion_mirror").joinpath("default_rules.yaml").read_text("utf-8")


def load_rules(path: Path | None = None) -> tuple[list[Rule], Settings]:
    text = path.read_text(encoding="utf-8") if path else default_rules_text()
    try:
        data = yaml.safe_load(text) or {}
    except yaml.YAMLError as exc:
        raise RulesError(f"Invalid YAML: {exc}") from exc
    return parse_rules(data)


def parse_rules(data: dict) -> tuple[list[Rule], Settings]:
    settings_raw = data.get("settings") or {}
    max_per_hour = int(settings_raw.get("max_per_hour", Settings.max_per_hour))
    if max_per_hour < 1:
        raise RulesError("settings.max_per_hour must be at least 1")

    rules: list[Rule] = []
    seen: set[str] = set()
    for i, raw in enumerate(data.get("rules") or []):
        rid = str(raw.get("id", f"#{i + 1}"))
        if rid in seen:
            raise RulesError(f"Duplicate rule id '{rid}'")
        seen.add(rid)

        metric = raw.get("metric")
        if metric not in METRIC_NAMES:
            raise RulesError(f"Rule '{rid}': unknown metric '{metric}'. Valid: {sorted(METRIC_NAMES)}")
        above, below = raw.get("above"), raw.get("below")
        if (above is None) == (below is None):
            raise RulesError(f"Rule '{rid}': set exactly one of 'above' or 'below'")
        messages = raw.get("messages") or []
        if not messages or not all(isinstance(m, str) and m.strip() for m in messages):
            raise RulesError(f"Rule '{rid}': 'messages' must be a non-empty list of strings")
        for_seconds = float(raw.get("for_seconds", 0))
        cooldown = float(raw.get("cooldown_minutes", 20))
        if for_seconds < 0 or cooldown < 0:
            raise RulesError(f"Rule '{rid}': for_seconds and cooldown_minutes cannot be negative")

        rules.append(
            Rule(
                id=rid,
                metric=metric,
                above=None if above is None else float(above),
                below=None if below is None else float(below),
                for_seconds=for_seconds,
                cooldown_minutes=cooldown,
                title=str(raw.get("title", "Motion Mirror")),
                messages=tuple(messages),
            )
        )
    return rules, Settings(max_per_hour=max_per_hour)


class RuleEngine:
    """Evaluates rules against metrics. At most one alert per call, in rule order."""

    def __init__(self, rules: list[Rule], settings: Settings, rng: random.Random | None = None):
        self._rules = rules
        self._settings = settings
        self._rng = rng or random.Random()
        self._since: dict[str, float | None] = {r.id: None for r in rules}
        self._last_fired: dict[str, float] = {}
        self._recent: deque[float] = deque()
        self._snooze_until = 0.0

    def snooze(self, minutes: float, now: float | None = None) -> None:
        now = time.monotonic() if now is None else now
        self._snooze_until = now + minutes * 60.0

    def evaluate(self, metrics: Metrics, now: float) -> list[Alert]:
        eligible: Rule | None = None
        for rule in self._rules:
            if not rule.triggered(metrics.get(rule.metric)):
                self._since[rule.id] = None
                continue
            if self._since[rule.id] is None:
                self._since[rule.id] = now
            if eligible is not None:
                continue
            if now - self._since[rule.id] < rule.for_seconds:  # type: ignore[operator]
                continue
            last = self._last_fired.get(rule.id)
            if last is not None and now - last < rule.cooldown_minutes * 60.0:
                continue
            eligible = rule

        if eligible is None or now < self._snooze_until:
            return []

        while self._recent and now - self._recent[0] >= 3600.0:
            self._recent.popleft()
        if len(self._recent) >= self._settings.max_per_hour:
            return []

        self._recent.append(now)
        self._last_fired[eligible.id] = now
        return [Alert(eligible.id, eligible.title, self._rng.choice(eligible.messages))]
