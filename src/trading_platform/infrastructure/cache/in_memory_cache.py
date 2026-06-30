from __future__ import annotations

from typing import Any


class InMemoryCache:
    def __init__(self) -> None:
        self._store: dict[Any, Any] = {}

    def set(self, key: Any, value: Any) -> None:
        self._store[key] = value

    def get(self, key: Any, default: Any = None) -> Any:
        return self._store.get(key, default)

    def contains(self, key: Any) -> bool:
        return key in self._store

    def remove(self, key: Any) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()

    def size(self) -> int:
        return len(self._store)
