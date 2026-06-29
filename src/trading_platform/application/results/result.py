from dataclasses import dataclass
from typing import Generic, TypeVar

T=TypeVar("T")

@dataclass(slots=True)
class Result(Generic[T]):
    success: bool
    value: T|None=None
    error: str|None=None
