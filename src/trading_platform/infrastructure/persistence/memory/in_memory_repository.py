from __future__ import annotations

from typing import Any

from trading_platform.infrastructure.persistence.repository_base import (
    RepositoryBase,
)


class InMemoryRepository(RepositoryBase):
    def __init__(self) -> None:
        self._items: dict[Any, Any] = {}

    def add(self, entity: Any) -> None:
        self._items[entity.id] = entity

    def get(self, identifier: Any) -> Any | None:
        return self._items.get(identifier)

    def all(self) -> tuple[Any, ...]:
        return tuple(self._items.values())

    def clear(self) -> None:
        self._items.clear()
