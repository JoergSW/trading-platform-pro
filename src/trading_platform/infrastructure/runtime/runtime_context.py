from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class RuntimeContext:
    profile: str
    debug: bool = False
