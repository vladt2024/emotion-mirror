"""Webcam capture with OpenCV. Frames live in memory only and are never written to disk."""

from __future__ import annotations

import sys

import cv2
import numpy as np


class CameraError(RuntimeError):
    pass


class Camera:
    def __init__(self, index: int = 0, width: int = 640, height: int = 480):
        self.index = index
        self.width = width
        self.height = height
        self._cap: cv2.VideoCapture | None = None

    def open(self) -> "Camera":
        # DirectShow avoids very slow start-up on Windows.
        backend = cv2.CAP_DSHOW if sys.platform == "win32" else cv2.CAP_ANY
        cap = cv2.VideoCapture(self.index, backend)
        if not cap.isOpened():
            cap.release()
            raise CameraError(
                f"Could not open camera {self.index}. Check that no other app is using it. "
                "Windows: Settings > Privacy & security > Camera, turn on camera access for apps "
                "and desktop apps (if Python came from the Microsoft Store, also turn on 'Python 3.x' "
                "in the app list). macOS: allow camera access for your terminal or IDE in "
                "System Settings > Privacy & Security > Camera. "
                "For another camera try --camera 1."
            )
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self._cap = cap
        return self

    def read(self) -> np.ndarray | None:
        """Return one BGR frame, or None if the camera did not deliver one."""
        if self._cap is None:
            raise CameraError("Camera is not open.")
        ok, frame = self._cap.read()
        return frame if ok else None

    def close(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def __enter__(self) -> "Camera":
        return self.open()

    def __exit__(self, *exc) -> None:
        self.close()
