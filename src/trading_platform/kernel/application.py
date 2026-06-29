from __future__ import annotations

from trading_platform.kernel.command_bus import CommandBus
from trading_platform.kernel.dependency_container import DependencyContainer
from trading_platform.kernel.event_bus import EventBus
from trading_platform.kernel.lifecycle import (
    ApplicationState,
    LifecycleManager,
)
from trading_platform.kernel.query_bus import QueryBus
from trading_platform.kernel.runtime_context import RuntimeContext


class Application:
    """Root application."""

    def __init__(self) -> None:
        self._container = DependencyContainer()
        self._runtime = RuntimeContext()

        self._event_bus = EventBus()
        self._command_bus = CommandBus()
        self._query_bus = QueryBus()

        self._lifecycle = LifecycleManager()

        self._container.register_singleton("runtime", self._runtime)
        self._container.register_singleton("event_bus", self._event_bus)
        self._container.register_singleton("command_bus", self._command_bus)
        self._container.register_singleton("query_bus", self._query_bus)
        self._container.register_singleton("lifecycle", self._lifecycle)

    @property
    def container(self) -> DependencyContainer:
        return self._container

    @property
    def runtime(self) -> RuntimeContext:
        return self._runtime

    @property
    def running(self) -> bool:
        return self.is_running

    @property
    def lifecycle(self) -> LifecycleManager:
        return self._lifecycle

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
        return self._lifecycle.state is ApplicationState.RUNNING

    def start(self) -> None:
        self._lifecycle.transition_to(ApplicationState.BOOTSTRAPPING)
        self._lifecycle.transition_to(ApplicationState.READY)
        self._lifecycle.transition_to(ApplicationState.RUNNING)

    def stop(self) -> None:
        if self._lifecycle.state is ApplicationState.RUNNING:
            self._lifecycle.transition_to(ApplicationState.STOPPING)
            self._lifecycle.transition_to(ApplicationState.STOPPED)