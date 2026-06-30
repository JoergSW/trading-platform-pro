from __future__ import annotations

from typing import Any


class BootstrapContext:
    def __init__(self) -> None:
        self.services: dict[str, Any] = {}

    def register(self, name: str, service: Any) -> None:
        self.services[name] = service

    def resolve(self, name: str) -> Any:
        return self.services[name]

    def contains(self, name: str) -> bool:
        return name in self.services

    def clear(self) -> None:
        self.services.clear()
