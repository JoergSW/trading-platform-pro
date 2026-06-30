from __future__ import annotations

from datetime import datetime


class TestClock:
    """Controllable clock for unit tests."""

    def __init__(self, fixed_time: datetime) -> None:
        self._fixed_time = fixed_time

    def now_utc(self) -> datetime:
        return self._fixed_time

    def set_time(self, fixed_time: datetime) -> None:
        self._fixed_time = fixed_time
