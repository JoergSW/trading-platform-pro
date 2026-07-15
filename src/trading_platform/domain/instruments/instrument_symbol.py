from __future__ import annotations


def validate_instrument_symbol(value: str | None) -> str:
    """Validate and return one normalized project-owned instrument symbol."""
    if not isinstance(value, str):
        raise TypeError("symbol must be a string")
    if not value or value != value.strip():
        raise ValueError("symbol must be normalized non-blank text")
    if len(value) > 32:
        raise ValueError("symbol must not exceed 32 characters")
    if not value.isascii():
        raise ValueError("symbol must use ASCII characters")
    if value != value.upper():
        raise ValueError("symbol must use uppercase characters")
    if not all(character.isalnum() or character in ".-/^" for character in value):
        raise ValueError("symbol contains unsupported characters")
    return value
