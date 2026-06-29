def require(condition: bool, message: str):
    if not condition:
        raise ValueError(message)
