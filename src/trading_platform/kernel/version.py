from dataclasses import dataclass
@dataclass(frozen=True, slots=True)
class VersionInfo:
    product:str="Trading Platform Pro"
    version:str="0.1.0-beta.1"
VERSION=VersionInfo()
