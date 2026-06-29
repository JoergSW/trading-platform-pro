import pytest
from trading_platform.kernel.dependency_container import DependencyContainer
from trading_platform.shared.exceptions.base import DependencyResolutionError


def test_resolve_singleton() -> None:
    container = DependencyContainer()
    service = object()
    container.register_singleton("service", service)
    assert container.resolve("service") is service


def test_missing_dependency_raises() -> None:
    container = DependencyContainer()
    with pytest.raises(DependencyResolutionError):
        container.resolve("missing")
