
from dataclasses import dataclass

@dataclass(frozen=True)
class VersionInfo:
    product: str = "Trading Platform Pro"
    version: str = "0.1.0-alpha.2"
    python_min: str = "3.13"

VERSION = VersionInfo()
