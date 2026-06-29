from dataclasses import dataclass
@dataclass(slots=True)
class StartupReport:
    success: bool
    message: str=''
