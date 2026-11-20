"""Frame -> Signals using MediaPipe. This is the only module that imports MediaPipe.

Swapping the vision engine later means changing only this file.
"""

from __future__ import annotations

import math
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python as mpt
from mediapipe.tasks.python import vision

from .paths import models_dir
from .signals import Signals

FACE_MODEL = "face_landmarker.task"
POSE_MODEL = "pose_landmarker_lite.task"

# MediaPipe pose landmark indices
_L_EAR, _R_EAR, _L_SHOULDER, _R_SHOULDER = 7, 8, 11, 12
# MediaPipe face mesh indices for the left/right edges of the face
_FACE_LEFT, _FACE_RIGHT = 234, 454

_MIN_VISIBILITY = 0.5


class ModelsMissingError(FileNotFoundError):
    pass


class Perception:
    def __init__(self, directory: Path | None = None):
        directory = directory or models_dir()
        face_path, pose_path = directory / FACE_MODEL, directory / POSE_MODEL
        for p in (face_path, pose_path):
            if not p.exists():
                raise ModelsMissingError(
                    f"Missing model file {p}. Run `motion-mirror download-models` first."
                )
        self._face = vision.FaceLandmarker.create_from_options(
            vision.FaceLandmarkerOptions(
                base_options=mpt.BaseOptions(model_asset_path=str(face_path)),
                running_mode=vision.RunningMode.VIDEO,
                num_faces=1,
            )
        )
        self._pose = vision.PoseLandmarker.create_from_options(
            vision.PoseLandmarkerOptions(
                base_options=mpt.BaseOptions(model_asset_path=str(pose_path)),
                running_mode=vision.RunningMode.VIDEO,
                num_poses=1,
            )
        )

    def process(self, frame_bgr: np.ndarray, timestamp_ms: int) -> Signals:
        """Extract signals from one BGR frame. timestamp_ms must increase on every call."""
        rgb = np.ascontiguousarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        face_width = None
        face = self._face.detect_for_video(image, timestamp_ms)
        present = bool(face.face_landmarks)
        if present:
            lm = face.face_landmarks[0]
            face_width = abs(lm[_FACE_RIGHT].x - lm[_FACE_LEFT].x)

        neck_ratio = shoulder_tilt = None
        pose = self._pose.detect_for_video(image, timestamp_ms)
        if pose.pose_landmarks:
            lm = pose.pose_landmarks[0]
            ear_l, ear_r, sh_l, sh_r = lm[_L_EAR], lm[_R_EAR], lm[_L_SHOULDER], lm[_R_SHOULDER]
            if all((p.visibility or 0.0) >= _MIN_VISIBILITY for p in (ear_l, ear_r, sh_l, sh_r)):
                present = True
                width = abs(sh_l.x - sh_r.x)
                if width > 1e-3:
                    neck_ratio = ((sh_l.y + sh_r.y) / 2 - (ear_l.y + ear_r.y) / 2) / width
                shoulder_tilt = _normalize_angle(
                    math.degrees(math.atan2(sh_l.y - sh_r.y, sh_l.x - sh_r.x))
                )

        return Signals(
            present=present,
            neck_ratio=neck_ratio,
            shoulder_tilt=shoulder_tilt,
            face_width=face_width,
        )

    def close(self) -> None:
        self._face.close()
        self._pose.close()


def _normalize_angle(angle: float) -> float:
    """Fold an angle into (-90, 90] so that a turned torso does not read as 180 degrees."""
    if angle > 90:
        return angle - 180
    if angle <= -90:
        return angle + 180
    return angle
