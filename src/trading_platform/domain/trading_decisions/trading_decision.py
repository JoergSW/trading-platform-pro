from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID

from trading_platform.domain.instruments.instrument_symbol import (
    validate_instrument_symbol,
)
from trading_platform.domain.trading_candidates.trading_candidate import CandidateId

MAX_TRADING_DECISION_RATIONALE_LENGTH = 4000


class TradingDecisionStatus(StrEnum):
    """Implemented Trading Decision lifecycle states."""

    DRAFT = "DRAFT"


@dataclass(frozen=True, slots=True)
class DecisionId:
    """Stable project-owned Trading Decision identity."""

    value: str

    def __post_init__(self) -> None:
        _require_normalized_text(self.value, "decision_id", max_length=36)
        try:
            parsed = UUID(self.value)
        except ValueError as exc:
            raise ValueError("decision_id must be a valid UUID") from exc
        if str(parsed) != self.value:
            raise ValueError("decision_id must use canonical lowercase UUID format")


@dataclass(frozen=True, slots=True)
class TradingDecision:
    """Persistent aggregate representing one explicit trading-decision draft."""

    decision_id: DecisionId
    candidate_id: CandidateId
    symbol: str
    status: TradingDecisionStatus
    rationale: str
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.decision_id, DecisionId):
            raise TypeError("decision_id must be a DecisionId")
        if not isinstance(self.candidate_id, CandidateId):
            raise TypeError("candidate_id must be a CandidateId")
        validate_instrument_symbol(self.symbol)
        if not isinstance(self.status, TradingDecisionStatus):
            raise TypeError("status must be a TradingDecisionStatus")
        validate_trading_decision_rationale(self.rationale)
        _require_utc_datetime(self.created_at, "created_at")
        _require_utc_datetime(self.updated_at, "updated_at")
        if self.updated_at < self.created_at:
            raise ValueError("updated_at must not be earlier than created_at")

    @classmethod
    def create_draft(
        cls,
        *,
        decision_id: str,
        candidate_id: CandidateId,
        symbol: str,
        rationale: str,
        observed_at: datetime,
    ) -> TradingDecision:
        """Create one DRAFT decision from an explicit reviewed-candidate action."""
        return cls(
            decision_id=DecisionId(decision_id),
            candidate_id=candidate_id,
            symbol=validate_instrument_symbol(symbol),
            status=TradingDecisionStatus.DRAFT,
            rationale=validate_trading_decision_rationale(rationale),
            created_at=observed_at,
            updated_at=observed_at,
        )


def validate_trading_decision_rationale(value: str | None) -> str:
    """Validate one traceable, normalized Trading Decision rationale."""
    _require_normalized_text(
        value,
        "rationale",
        max_length=MAX_TRADING_DECISION_RATIONALE_LENGTH,
    )
    assert isinstance(value, str)
    return value


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
        raise ValueError(f"{field_name} must be non-blank normalized text")
    if len(value) > max_length:
        raise ValueError(f"{field_name} must not exceed {max_length} characters")
