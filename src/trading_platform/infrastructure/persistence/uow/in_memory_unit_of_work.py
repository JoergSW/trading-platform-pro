from __future__ import annotations


class InMemoryUnitOfWork:
    def __init__(self) -> None:
        self.reset()

    def __enter__(self) -> "InMemoryUnitOfWork":
        self.reset()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc is not None:
            self.rollback()

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True

    def reset(self) -> None:
        self.committed = False
        self.rolled_back = False
