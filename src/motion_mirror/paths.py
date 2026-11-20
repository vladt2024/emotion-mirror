"""Where Motion Mirror keeps its (local) files. Override with MOTION_MIRROR_HOME."""

from __future__ import annotations

import os
from pathlib import Path


def home_dir() -> Path:
    override = os.environ.get("MOTION_MIRROR_HOME")
    return Path(override) if override else Path.home() / ".motion-mirror"


def models_dir() -> Path:
    return home_dir() / "models"


def baseline_path() -> Path:
    return home_dir() / "baseline.json"
