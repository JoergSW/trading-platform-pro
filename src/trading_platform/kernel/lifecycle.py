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
    _allowed = {
        ApplicationState.CREATED: {ApplicationState.BOOTSTRAPPING, ApplicationState.FAILED},
        ApplicationState.BOOTSTRAPPING: {ApplicationState.READY, ApplicationState.FAILED},
        ApplicationState.READY: {ApplicationState.RUNNING, ApplicationState.STOPPING, ApplicationState.FAILED},
        ApplicationState.RUNNING: {ApplicationState.STOPPING, ApplicationState.FAILED},
        ApplicationState.STOPPING: {ApplicationState.STOPPED, ApplicationState.FAILED},
        ApplicationState.STOPPED: set(),
        ApplicationState.FAILED: set(),
    }

    def __init__(self) -> None:
        self._state = ApplicationState.CREATED

    @property
    def state(self) -> ApplicationState:
        return self._state

    def transition_to(self, target: ApplicationState) -> None:
        if target not in self._allowed[self._state]:
            raise LifecycleError(f"Invalid lifecycle transition: {self._state} -> {target}")
        self._state = target
