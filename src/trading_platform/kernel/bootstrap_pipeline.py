from __future__ import annotations

from collections.abc import Callable


class BootstrapPipeline:
    """Deterministic bootstrap pipeline."""

    def __init__(self) -> None:
        self._steps: list[Callable[[], None]] = []

    def add_step(self, step: Callable[[], None]) -> None:
        if not callable(step):
            raise TypeError("Bootstrap step must be callable.")
        self._steps.append(step)

    def execute(self) -> None:
        for index, step in enumerate(self._steps, start=1):
            try:
                step()
            except Exception as exc:
                raise RuntimeError(
                    f"Bootstrap step {index} failed."
                ) from exc

    @property
    def step_count(self) -> int:
        return len(self._steps)

    def clear(self) -> None:
        self._steps.clear()