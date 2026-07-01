from pathlib import Path


class FileService:
    def read_text(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")
