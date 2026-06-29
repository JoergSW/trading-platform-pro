from dataclasses import dataclass
@dataclass(frozen=True, slots=True)
class Identifier:
    value:str
