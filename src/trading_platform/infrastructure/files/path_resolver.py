from pathlib import Path

class PathResolver:
    def __init__(self, base_path: Path) -> None:
        self.base_path = base_path

    def resolve(self, relative_path: str) -> Path:
        return self.base_path / relative_path
