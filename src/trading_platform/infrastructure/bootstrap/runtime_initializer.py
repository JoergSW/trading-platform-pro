from __future__ import annotations

from collections.abc import Callable


class RuntimeInitializer:
    def __init__(self) -> None:
        self._steps: list[Callable[[], None]] = []

    def add(self, step: Callable[[], None]) -> None:
        self._steps.append(step)

    def initialize(self) -> None:
        for step in self._steps:
            step()

    def clear(self) -> None:
        self._steps.clear()

    def size(self) -> int:
        return len(self._steps)
