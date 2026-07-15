from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID

from trading_platform.domain.instruments.instrument_symbol import (
    validate_instrument_symbol,
)


class TradingCandidateOrigin(StrEnum):
    """Supported explicit candidate-intake origins for the current product slice."""

    SCANNER = "Scanner"
    WATCHLIST = "Watchlist"


class TradingCandidateStatus(StrEnum):
    """Implemented candidate lifecycle states."""

    NEW = "NEW"


@dataclass(frozen=True, slots=True)
class CandidateId:
    """Stable project-owned Trading Candidate identity."""

    value: str

    def __post_init__(self) -> None:
        _require_normalized_text(self.value, "candidate_id", max_length=36)
        try:
            parsed = UUID(self.value)
        except ValueError as exc:
            raise ValueError("candidate_id must be a valid UUID") from exc
        if str(parsed) != self.value:
            raise ValueError("candidate_id must use canonical lowercase UUID format")


@dataclass(frozen=True, slots=True)
class TradingCandidate:
    """Persistent aggregate representing one instrument under evaluation."""

    candidate_id: CandidateId
    symbol: str
    origin: TradingCandidateOrigin
    status: TradingCandidateStatus
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.candidate_id, CandidateId):
            raise TypeError("candidate_id must be a CandidateId")
        validate_instrument_symbol(self.symbol)
        if not isinstance(self.origin, TradingCandidateOrigin):
            raise TypeError("origin must be a TradingCandidateOrigin")
        if not isinstance(self.status, TradingCandidateStatus):
            raise TypeError("status must be a TradingCandidateStatus")
        _require_utc_datetime(self.created_at, "created_at")
        _require_utc_datetime(self.updated_at, "updated_at")
        if self.updated_at < self.created_at:
            raise ValueError("updated_at must not be earlier than created_at")

    @classmethod
    def create_new(
        cls,
        *,
        candidate_id: str,
        symbol: str,
        origin: TradingCandidateOrigin,
        observed_at: datetime,
    ) -> TradingCandidate:
        """Create one NEW candidate from an explicit intake request."""
        return cls(
            candidate_id=CandidateId(candidate_id),
            symbol=validate_instrument_symbol(symbol),
            origin=origin,
            status=TradingCandidateStatus.NEW,
            created_at=observed_at,
            updated_at=observed_at,
        )


def _require_utc_datetime(value: datetime, field_name: str) -> None:
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() != UTC.utcoffset(value):
        raise ValueError(f"{field_name} must use UTC")


def _require_normalized_text(
    value: str | None,
    field_name: str,
    *,
    max_length: int,
) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{field_name} must be normalized non-blank text")
    if len(value) > max_length:
        raise ValueError(f"{field_name} must not exceed {max_length} characters")
