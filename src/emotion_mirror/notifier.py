"""Desktop notifications. Falls back to printing if no notification backend works."""

from __future__ import annotations

import asyncio
import logging

log = logging.getLogger(__name__)


class Notifier:
    def __init__(self, app_name: str = "Emotion Mirror"):
        self._loop: asyncio.AbstractEventLoop | None = None
        self._notifier = None
        try:
            from desktop_notifier import DesktopNotifier

            self._notifier = DesktopNotifier(app_name=app_name)
            self._loop = asyncio.new_event_loop()
        except Exception as exc:  # backend missing or unsupported on this system
            log.warning("Desktop notifications unavailable (%s). Printing instead.", exc)

    def send(self, title: str, message: str) -> None:
        if self._notifier is not None and self._loop is not None:
            try:
                self._loop.run_until_complete(self._notifier.send(title=title, message=message))
                return
            except Exception as exc:
                log.warning("Notification failed (%s). Printing instead.", exc)
        print(f"[{title}] {message}", flush=True)

    def close(self) -> None:
        if self._loop is not None:
            self._loop.close()
            self._loop = None
