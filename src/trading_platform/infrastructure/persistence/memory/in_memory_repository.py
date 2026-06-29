class InMemoryRepository:
    def __init__(self) -> None:
        self._items = {}

    def add(self, entity) -> None:
        self._items[entity.id] = entity

    def get(self, identifier):
        return self._items.get(identifier)

    def all(self):
        return tuple(self._items.values())

    def clear(self) -> None:
        self._items.clear()
