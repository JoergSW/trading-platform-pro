from collections.abc import Callable
from typing import Any
from trading_platform.shared.exceptions.base import DependencyResolutionError


class DependencyContainer:
    def __init__(self) -> None:
        self._singletons: dict[str, Any] = {}
        self._factories: dict[str, Callable[[], Any]] = {}

    def register_singleton(self, key: str, instance: Any) -> None:
        if not key:
            raise ValueError("Dependency key must not be empty.")
        self._singletons[key] = instance

    def register_factory(self, key: str, factory: Callable[[], Any]) -> None:
        if not key:
            raise ValueError("Dependency key must not be empty.")
        self._factories[key] = factory

    def resolve(self, key: str) -> Any:
        if key in self._singletons:
            return self._singletons[key]
        if key in self._factories:
            return self._factories[key]()
        raise DependencyResolutionError(f"Dependency not registered: {key}")

    def contains(self, key: str) -> bool:
        return key in self._singletons or key in self._factories
