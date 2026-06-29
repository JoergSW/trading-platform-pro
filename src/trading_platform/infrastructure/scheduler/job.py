from dataclasses import dataclass
from collections.abc import Callable

@dataclass(slots=True)
class Job:
    name: str
    action: Callable[[], None]
    enabled: bool = True

    def run(self) -> None:
        if self.enabled:
            self.action()
