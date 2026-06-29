from __future__ import annotations

from collections.abc import Callable
from typing import Any


CommandHandler = Callable[[Any], Any]


class CommandBus:
    """Synchronous command bus."""

    def __init__(self) -> None:
        self._handlers: dict[type, CommandHandler] = {}

    def register(
        self,
        command_type: type,
        handler: CommandHandler,
    ) -> None:
        if not callable(handler):
            raise TypeError("Command handler must be callable.")

        if command_type in self._handlers:
            raise ValueError(
                f"Handler already registered for {command_type.__name__}"
            )

        self._handlers[command_type] = handler

    def execute(self, command: Any) -> Any:
        handler = self._handlers.get(type(command))

        if handler is None:
            raise LookupError(
                f"No handler registered for {type(command).__name__}"
            )

        return handler(command)

    def contains(self, command_type: type) -> bool:
        return command_type in self._handlers

    def clear(self) -> None:
        self._handlers.clear()