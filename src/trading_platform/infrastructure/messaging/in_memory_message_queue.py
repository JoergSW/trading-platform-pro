from collections import deque

class InMemoryMessageQueue:
    def __init__(self) -> None:
        self._queue = deque()

    def enqueue(self, message) -> None:
        self._queue.append(message)

    def dequeue(self):
        if not self._queue:
            return None
        return self._queue.popleft()

    def size(self) -> int:
        return len(self._queue)
