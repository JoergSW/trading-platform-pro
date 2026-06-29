from dataclasses import dataclass
from trading_platform.infrastructure.persistence.memory.in_memory_repository import InMemoryRepository

@dataclass
class Item:
    id: str

def test_in_memory_repository():
    repo = InMemoryRepository()
    item = Item("A")
    repo.add(item)
    assert repo.get("A") is item
    assert repo.all() == (item,)
