from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

TEntity = TypeVar("TEntity")
TId = TypeVar("TId")


class RepositoryBase(ABC, Generic[TEntity, TId]):
    """Base interface for repository implementations."""

    @abstractmethod
    def add(self, entity: TEntity) -> None:
        """Persist an entity."""

    @abstractmethod
    def get(self, identifier: TId) -> TEntity | None:
        """Return an entity by its identifier."""
