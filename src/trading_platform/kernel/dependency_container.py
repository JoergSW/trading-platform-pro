from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from threading import RLock
from typing import Any, TypeVar

from trading_platform.shared.exceptions.base import DependencyResolutionError

T = TypeVar("T")


class ServiceLifetime(StrEnum):
    SINGLETON = "singleton"
    FACTORY = "factory"


@dataclass(frozen=True, slots=True)
class ServiceDescriptor:
    key: str
    lifetime: ServiceLifetime
    provider: Any


class DependencyContainer:
    def __init__(self) -> None:
        self._descriptors: dict[str, ServiceDescriptor] = {}
        self._singletons: dict[str, Any] = {}
        self._lock = RLock()

    def register_singleton(self, key: str, instance: Any) -> None:
        self._register(key, ServiceLifetime.SINGLETON, instance)
        with self._lock:
            self._singletons[key] = instance

    def register_factory(self, key: str, factory: Callable[[], T]) -> None:
        if not callable(factory):
            raise TypeError(f"Factory for dependency '{key}' must be callable.")
        self._register(key, ServiceLifetime.FACTORY, factory)

    def resolve(self, key: str) -> Any:
        with self._lock:
            descriptor = self._descriptors.get(key)
            if descriptor is None:
                raise DependencyResolutionError(f"Dependency not registered: {key}")

            if descriptor.lifetime == ServiceLifetime.SINGLETON:
                return self._singletons[key]

            if descriptor.lifetime == ServiceLifetime.FACTORY:
                return descriptor.provider()

        raise DependencyResolutionError(f"Unsupported dependency lifetime for: {key}")

    def contains(self, key: str) -> bool:
        with self._lock:
            return key in self._descriptors

    def keys(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(self._descriptors.keys())

    def clear(self) -> None:
        with self._lock:
            self._descriptors.clear()
            self._singletons.clear()

    def _register(self, key: str, lifetime: ServiceLifetime, provider: Any) -> None:
        if not key or not key.strip():
            raise ValueError("Dependency key must not be empty.")

        normalized_key = key.strip()

        with self._lock:
            if normalized_key in self._descriptors:
                raise ValueError(f"Dependency already registered: {normalized_key}")

            self._descriptors[normalized_key] = ServiceDescriptor(
                key=normalized_key,
                lifetime=lifetime,
                provider=provider,
            )