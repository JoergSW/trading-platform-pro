from __future__ import annotations

from pathlib import Path


class ResourceLocator:
    def __init__(self, root: Path) -> None:
        self.root: Path = root

    def get(self, relative: str) -> Path:
        return self.root / relative
