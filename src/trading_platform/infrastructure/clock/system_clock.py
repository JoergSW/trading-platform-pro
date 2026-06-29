from datetime import UTC, datetime
class SystemClock:
    def now(self):
        return datetime.now(UTC)
