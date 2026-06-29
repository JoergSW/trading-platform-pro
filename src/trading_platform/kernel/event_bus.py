from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from typing import Any


EventHandler = Callable[[Any], None]


class EventBus:
    """Simple synchronous in-process event bus."""

    def __init__(self) -> None:
        self._subscriptions: dict[type, list[EventHandler]] = defaultdict(list)

    def subscribe(
        self,
        event_type: type,
        handler: EventHandler,
    ) -> None:
        if not callable(handler):
            raise TypeError("Event handler must be callable.")

        self._subscriptions[event_type].append(handler)

    def unsubscribe(
        self,
        event_type: type,
        handler: EventHandler,
    ) -> None:
        handlers = self._subscriptions.get(event_type)
        if not handlers:
            return

        if handler in handlers:
            handlers.remove(handler)

    def publish(self, event: Any) -> None:
        for handler in self._subscriptions.get(type(event), ()):
            handler(event)

    def clear(self) -> None:
        self._subscriptions.clear()

    @property
    def subscription_count(self) -> int:
        return sum(len(v) for v in self._subscriptions.values())