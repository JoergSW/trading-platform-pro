from dataclasses import dataclass
from datetime import UTC, datetime

@dataclass(slots=True,frozen=True)
class Event:
    name:str
    created_at:datetime=datetime.now(UTC)
