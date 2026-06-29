from trading_platform.kernel.dependency_container import DependencyContainer
from trading_platform.kernel.lifecycle import ApplicationState, LifecycleManager


class Application:
    def __init__(self, container: DependencyContainer | None = None) -> None:
        self.container = container or DependencyContainer()
        self.lifecycle = LifecycleManager()

    @property
    def state(self) -> ApplicationState:
        return self.lifecycle.state

    def mark_ready(self) -> None:
        self.lifecycle.transition_to(ApplicationState.BOOTSTRAPPING)
        self.lifecycle.transition_to(ApplicationState.READY)

    def start(self) -> None:
        if self.state == ApplicationState.CREATED:
            self.mark_ready()
        self.lifecycle.transition_to(ApplicationState.RUNNING)

    def shutdown(self) -> None:
        self.lifecycle.transition_to(ApplicationState.STOPPING)
        self.lifecycle.transition_to(ApplicationState.STOPPED)
