from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from trading_platform.domain.trading_candidates.trading_candidate import CandidateId
from trading_platform.domain.trading_decisions.trading_decision import (
    DecisionId,
    TradingDecision,
    TradingDecisionStatus,
    validate_trading_decision_rationale,
)

DECISION_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
CANDIDATE_ID = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"


def test_create_trading_decision_draft_preserves_required_state() -> None:
    observed_at = datetime(2026, 7, 16, 9, 30, tzinfo=UTC)

    decision = TradingDecision.create_draft(
        decision_id=DECISION_ID,
        candidate_id=CandidateId(CANDIDATE_ID),
        symbol="AAPL",
        rationale="Price structure and volume confirm the reviewed setup.",
        observed_at=observed_at,
    )

    assert decision.decision_id == DecisionId(DECISION_ID)
    assert decision.candidate_id == CandidateId(CANDIDATE_ID)
    assert decision.symbol == "AAPL"
    assert decision.status is TradingDecisionStatus.DRAFT
    assert decision.rationale == (
        "Price structure and volume confirm the reviewed setup."
    )
    assert decision.created_at == observed_at
    assert decision.updated_at == observed_at


@pytest.mark.parametrize(
    "rationale",
    (
        "",
        " leading whitespace",
        "trailing whitespace ",
        "x" * 4001,
    ),
)
def test_trading_decision_rejects_invalid_rationale(rationale: str) -> None:
    with pytest.raises(ValueError):
        TradingDecision.create_draft(
            decision_id=DECISION_ID,
            candidate_id=CandidateId(CANDIDATE_ID),
            symbol="AAPL",
            rationale=rationale,
            observed_at=datetime(2026, 7, 16, 9, 30, tzinfo=UTC),
        )


def test_trading_decision_rationale_validator_preserves_multiline_evidence() -> None:
    rationale = "Price structure confirms the setup.\nVolume supports the breakout."

    assert validate_trading_decision_rationale(rationale) == rationale


def test_trading_decision_rejects_non_utc_or_regressing_timestamps() -> None:
    created_at = datetime(2026, 7, 16, 9, 30, tzinfo=UTC)

    with pytest.raises(ValueError, match="timezone-aware"):
        TradingDecision(
            decision_id=DecisionId(DECISION_ID),
            candidate_id=CandidateId(CANDIDATE_ID),
            symbol="AAPL",
            status=TradingDecisionStatus.DRAFT,
            rationale="Reviewed setup.",
            created_at=created_at.replace(tzinfo=None),
            updated_at=created_at,
        )

    with pytest.raises(ValueError, match="updated_at"):
        TradingDecision(
            decision_id=DecisionId(DECISION_ID),
            candidate_id=CandidateId(CANDIDATE_ID),
            symbol="AAPL",
            status=TradingDecisionStatus.DRAFT,
            rationale="Reviewed setup.",
            created_at=created_at,
            updated_at=created_at - timedelta(seconds=1),
        )
