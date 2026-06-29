import pytest
from trading_platform.kernel.lifecycle import ApplicationState, LifecycleManager
from trading_platform.shared.exceptions.base import LifecycleError


def test_valid_lifecycle_transitions() -> None:
    lifecycle = LifecycleManager()
    lifecycle.transition_to(ApplicationState.BOOTSTRAPPING)
    lifecycle.transition_to(ApplicationState.READY)
    lifecycle.transition_to(ApplicationState.RUNNING)
    lifecycle.transition_to(ApplicationState.STOPPING)
    lifecycle.transition_to(ApplicationState.STOPPED)
    assert lifecycle.state == ApplicationState.STOPPED


def test_invalid_lifecycle_transition_raises() -> None:
    lifecycle = LifecycleManager()
    with pytest.raises(LifecycleError):
        lifecycle.transition_to(ApplicationState.RUNNING)
