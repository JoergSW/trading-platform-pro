from __future__ import annotations

from enum import StrEnum

from trading_platform.shared.exceptions.base import LifecycleError


class ApplicationState(StrEnum):
    CREATED = "created"
    BOOTSTRAPPING = "bootstrapping"
    READY = "ready"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


class LifecycleManager:
    _allowed: dict[ApplicationState, set[ApplicationState]] = {
        ApplicationState.CREATED: {
            ApplicationState.BOOTSTRAPPING,
            ApplicationState.FAILED,
        },
        ApplicationState.BOOTSTRAPPING: {
            ApplicationState.READY,
            ApplicationState.FAILED,
        },
        ApplicationState.READY: {
            ApplicationState.RUNNING,
            ApplicationState.STOPPING,
            ApplicationState.FAILED,
        },
        ApplicationState.RUNNING: {
            ApplicationState.STOPPING,
            ApplicationState.FAILED,
        },
        ApplicationState.STOPPING: {
            ApplicationState.STOPPED,
            ApplicationState.FAILED,
        },
        ApplicationState.STOPPED: set(),
        ApplicationState.FAILED: set(),
    }

    def __init__(self) -> None:
        self._state = ApplicationState.CREATED

    @property
    def state(self) -> ApplicationState:
        return self._state

    @property
    def is_running(self) -> bool:
        return self._state is ApplicationState.RUNNING

    def can_transition(self, target: ApplicationState) -> bool:
        return target in self._allowed[self._state]

    def transition_to(self, target: ApplicationState) -> None:
        if not self.can_transition(target):
            raise LifecycleError(
                f"Invalid lifecycle transition: "
                f"{self._state.value} -> {target.value}"
            )
        self._state = target

    def reset(self) -> None:
        self._state = ApplicationState.CREATED