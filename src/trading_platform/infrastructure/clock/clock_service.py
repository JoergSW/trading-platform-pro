from datetime import UTC, datetime

class ClockService:
    def now_utc(self) -> datetime:
        return datetime.now(UTC)
