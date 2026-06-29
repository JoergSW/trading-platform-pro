from dataclasses import dataclass, field
from datetime import UTC, datetime
import uuid

@dataclass(frozen=True, slots=True)
class DomainEvent:
    event_id:str=field(default_factory=lambda:str(uuid.uuid4()))
    occurred_at:datetime=field(default_factory=lambda:datetime.now(UTC))
