from __future__ import annotations

from uuid import uuid4


class IdGenerator:
    def new_id(self) -> str:
        return str(uuid4())
