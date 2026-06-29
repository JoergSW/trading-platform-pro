from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class RuntimeContext:
    """Global runtime state shared across the application."""

    environment: str = "development"
    profile: str = "default"

    services: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def register_service(self, name: str, service: Any) -> None:
        self.services[name] = service

    def get_service(self, name: str) -> Any:
        return self.services[name]

    def has_service(self, name: str) -> bool:
        return name in self.services

    def set(self, key: str, value: Any) -> None:
        self.metadata[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self.metadata.get(key, default)

    def clear(self) -> None:
        self.services.clear()
        self.metadata.clear()