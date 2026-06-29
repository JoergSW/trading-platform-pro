from __future__ import annotations

from trading_platform.kernel.command_bus import CommandBus
from trading_platform.kernel.dependency_container import DependencyContainer
from trading_platform.kernel.event_bus import EventBus
from trading_platform.kernel.query_bus import QueryBus
from trading_platform.kernel.runtime_context import RuntimeContext


class Application:
    """Root application object."""

    def __init__(self) -> None:
        self._container = DependencyContainer()
        self._runtime = RuntimeContext()

        self._event_bus = EventBus()
        self._command_bus = CommandBus()
        self._query_bus = QueryBus()

        self._running = False

        self._container.register_singleton("runtime", self._runtime)
        self._container.register_singleton("event_bus", self._event_bus)
        self._container.register_singleton("command_bus", self._command_bus)
        self._container.register_singleton("query_bus", self._query_bus)

    @property
    def container(self) -> DependencyContainer:
        return self._container

    @property
    def runtime(self) -> RuntimeContext:
        return self._runtime

    @property
    def event_bus(self) -> EventBus:
        return self._event_bus

    @property
    def command_bus(self) -> CommandBus:
        return self._command_bus

    @property
    def query_bus(self) -> QueryBus:
        return self._query_bus

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> None:
        if self._running:
            raise RuntimeError("Application is already running.")
        self._running = True

    def stop(self) -> None:
        self._running = False