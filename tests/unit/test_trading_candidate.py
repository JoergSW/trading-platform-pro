from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from trading_platform.domain.trading_candidates.trading_candidate import (
    CandidateId,
    TradingCandidate,
    TradingCandidateOrigin,
    TradingCandidateStatus,
)

CANDIDATE_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"


def test_create_new_trading_candidate_preserves_required_state() -> None:
    observed_at = datetime(2026, 7, 15, 15, 30, tzinfo=UTC)

    candidate = TradingCandidate.create_new(
        candidate_id=CANDIDATE_ID,
        symbol="AAPL",
        origin=TradingCandidateOrigin.SCANNER,
        observed_at=observed_at,
    )

    assert candidate.candidate_id == CandidateId(CANDIDATE_ID)
    assert candidate.symbol == "AAPL"
    assert candidate.origin is TradingCandidateOrigin.SCANNER
    assert candidate.status is TradingCandidateStatus.NEW
    assert candidate.created_at == observed_at
    assert candidate.updated_at == observed_at


def test_trading_candidate_rejects_non_utc_timestamps() -> None:
    non_utc = datetime(2026, 7, 15, 17, 30, tzinfo=UTC) + timedelta(hours=1)
    non_utc = non_utc.replace(tzinfo=None)

    with pytest.raises(ValueError, match="timezone-aware"):
        TradingCandidate.create_new(
            candidate_id=CANDIDATE_ID,
            symbol="AAPL",
            origin=TradingCandidateOrigin.WATCHLIST,
            observed_at=non_utc,
        )


def test_trading_candidate_rejects_updated_time_before_creation() -> None:
    created_at = datetime(2026, 7, 15, 15, 30, tzinfo=UTC)

    with pytest.raises(ValueError, match="updated_at"):
        TradingCandidate(
            candidate_id=CandidateId(CANDIDATE_ID),
            symbol="AAPL",
            origin=TradingCandidateOrigin.SCANNER,
            status=TradingCandidateStatus.NEW,
            created_at=created_at,
            updated_at=created_at - timedelta(seconds=1),
        )


def test_candidate_id_requires_canonical_uuid() -> None:
    with pytest.raises(ValueError, match="canonical lowercase UUID"):
        CandidateId(CANDIDATE_ID.upper())
