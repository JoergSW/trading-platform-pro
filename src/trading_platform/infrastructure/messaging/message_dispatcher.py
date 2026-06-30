from __future__ import annotations

from typing import Any, Callable


class MessageDispatcher:
    def __init__(self) -> None:
        self._routes: dict[type, Callable[[Any], Any]] = {}

    def register(
        self,
        message_type: type,
        handler: Callable[[Any], Any],
    ) -> None:
        self._routes[message_type] = handler

    def dispatch(self, message: Any) -> Any:
        handler = self._routes.get(type(message))
        if handler is None:
            raise LookupError(f"No handler registered for {type(message).__name__}")
        return handler(message)
