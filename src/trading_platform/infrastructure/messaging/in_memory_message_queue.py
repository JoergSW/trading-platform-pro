from __future__ import annotations

from collections import deque
from typing import Any


class InMemoryMessageQueue:
    def __init__(self) -> None:
        self._queue: deque[Any] = deque()

    def enqueue(self, message: Any) -> None:
        self._queue.append(message)

    def dequeue(self) -> Any | None:
        if not self._queue:
            return None
        return self._queue.popleft()

    def size(self) -> int:
        return len(self._queue)

    def is_empty(self) -> bool:
        return not self._queue

    def clear(self) -> None:
        self._queue.clear()
