from __future__ import annotations

from collections.abc import Callable


class Scheduler:
    def __init__(self) -> None:
        self._jobs: list[Callable[[], None]] = []

    def add(self, job: Callable[[], None]) -> None:
        self._jobs.append(job)

    def run_pending(self) -> None:
        for job in list(self._jobs):
            job()
