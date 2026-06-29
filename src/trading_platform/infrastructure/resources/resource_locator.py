from pathlib import Path

class ResourceLocator:
    def __init__(self, root: Path):
        self.root=root

    def get(self, relative:str)->Path:
        return self.root/relative
