from dataclasses import dataclass

@dataclass(slots=True)
class AppSettings:
    name:str
    profile:str
