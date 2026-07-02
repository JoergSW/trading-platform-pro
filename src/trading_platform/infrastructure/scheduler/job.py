from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(slots=True)
class Job:
    name: str
    action: Callable[[], None]
    enabled: bool = True

    def run(self) -> None:
        if self.enabled:
            self.action()
