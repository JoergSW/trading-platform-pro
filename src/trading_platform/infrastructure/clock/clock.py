from __future__ import annotations

from datetime import UTC, datetime


class SystemClock:
    """Provides the current UTC time."""

    def now_utc(self) -> datetime:
        return datetime.now(UTC)
