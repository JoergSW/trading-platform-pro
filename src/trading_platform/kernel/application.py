from __future__ import annotations

from trading_platform.kernel.dependency_container import DependencyContainer


class Application:
    """Root application object."""

    def __init__(self) -> None:
        self._container = DependencyContainer()
        self._running = False

    @property
    def container(self) -> DependencyContainer:
        return self._container

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> None:
        if self._running:
            raise RuntimeError("Application is already running.")
        self._running = True

    def stop(self) -> None:
        if not self._running:
            return
        self._running = False