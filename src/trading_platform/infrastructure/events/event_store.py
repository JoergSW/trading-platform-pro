class InMemoryEventStore:
    def __init__(self) -> None:
        self._events = []

    def append(self, event) -> None:
        self._events.append(event)

    def all(self):
        return tuple(self._events)

    def clear(self) -> None:
        self._events.clear()
