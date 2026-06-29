from dataclasses import dataclass
@dataclass(slots=True)
class Result:
    success: bool
    message: str=""
