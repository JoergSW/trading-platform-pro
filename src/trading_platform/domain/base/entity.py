from dataclasses import dataclass

@dataclass(eq=False)
class Entity:
    id: str

    def __eq__(self, other):
        return isinstance(other, Entity) and self.id == other.id
