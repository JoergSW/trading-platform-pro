from __future__ import annotations

from collections.abc import Callable
from typing import Any


QueryHandler = Callable[[Any], Any]


class QueryBus:
    """Synchronous query bus."""

    def __init__(self) -> None:
        self._handlers: dict[type, QueryHandler] = {}

    def register(
        self,
        query_type: type,
        handler: QueryHandler,
    ) -> None:
        if not callable(handler):
            raise TypeError("Query handler must be callable.")

        if query_type in self._handlers:
            raise ValueError(
                f"Handler already registered for {query_type.__name__}"
            )

        self._handlers[query_type] = handler

    def execute(self, query: Any) -> Any:
        handler = self._handlers.get(type(query))

        if handler is None:
            raise LookupError(
                f"No handler registered for {type(query).__name__}"
            )

        return handler(query)

    def contains(self, query_type: type) -> bool:
        return query_type in self._handlers

    def clear(self) -> None:
        self._handlers.clear()