from __future__ import annotations

from collections.abc import Callable
from typing import TypeAlias

HealthCheck: TypeAlias = Callable[[], object]


class HealthService:
    def __init__(self) -> None:
        self._checks: list[HealthCheck] = []

    def register(self, check: HealthCheck) -> None:
        self._checks.append(check)

    def run(self) -> list[object]:
        return [check() for check in self._checks]
