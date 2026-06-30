from __future__ import annotations

from typing import Any


class InMemoryEventStore:
    def __init__(self) -> None:
        self._events: list[Any] = []

    def append(self, event: Any) -> None:
        self._events.append(event)

    def all(self) -> tuple[Any, ...]:
        return tuple(self._events)

    def clear(self) -> None:
        self._events.clear()

    def __len__(self) -> int:
        return len(self._events)
