from dataclasses import dataclass

@dataclass(slots=True)
class CommandMessage:
    payload: object

@dataclass(slots=True)
class QueryMessage:
    payload: object
