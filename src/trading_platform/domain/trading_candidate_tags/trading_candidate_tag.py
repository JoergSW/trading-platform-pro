from __future__ import annotations

import re
from dataclasses import dataclass

MAX_TRADING_CANDIDATE_TAG_LENGTH = 32
_MULTIPLE_WHITESPACE = re.compile(r"\s+")


@dataclass(frozen=True, slots=True)
class TradingCandidateTag:
    """Normalized Candidate-related tag value."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", normalize_trading_candidate_tag(self.value))

    @property
    def normalized_key(self) -> str:
        """Return the case-insensitive persistence and comparison key."""
        return self.value.casefold()


def normalize_trading_candidate_tag(value: str) -> str:
    """Normalize surrounding and repeated whitespace while preserving case."""
    if not isinstance(value, str):
        raise TypeError("tag must be a string")
    normalized = _MULTIPLE_WHITESPACE.sub(" ", value.strip())
    if not normalized:
        raise ValueError("tag must be non-blank normalized text")
    if len(normalized) > MAX_TRADING_CANDIDATE_TAG_LENGTH:
        raise ValueError(
            f"tag must not exceed {MAX_TRADING_CANDIDATE_TAG_LENGTH} characters"
        )
    return normalized
