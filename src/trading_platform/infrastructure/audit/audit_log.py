from dataclasses import dataclass, field
from datetime import UTC, datetime

@dataclass(slots=True)
class AuditRecord:
    event: str
    details: dict
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

class AuditLog:
    def __init__(self) -> None:
        self._records: list[AuditRecord] = []

    def append(self, event: str, details: dict | None = None) -> None:
        self._records.append(AuditRecord(event=event, details=details or {}))

    def records(self) -> tuple[AuditRecord, ...]:
        return tuple(self._records)
