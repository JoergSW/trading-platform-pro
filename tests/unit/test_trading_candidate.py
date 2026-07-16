from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from trading_platform.domain.trading_candidates.trading_candidate import (
    CandidateId,
    InvalidTradingCandidateStatusTransitionError,
    TradingCandidate,
    TradingCandidateOrigin,
    TradingCandidateStatus,
)

CANDIDATE_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"


def _candidate() -> TradingCandidate:
    return TradingCandidate.create_new(
        candidate_id=CANDIDATE_ID,
        symbol="AAPL",
        origin=TradingCandidateOrigin.SCANNER,
        observed_at=datetime(2026, 7, 15, 15, 30, tzinfo=UTC),
    )


def test_create_new_trading_candidate_preserves_required_state() -> None:
    candidate = _candidate()

    assert candidate.candidate_id == CandidateId(CANDIDATE_ID)
    assert candidate.symbol == "AAPL"
    assert candidate.origin is TradingCandidateOrigin.SCANNER
    assert candidate.status is TradingCandidateStatus.NEW
    assert candidate.created_at == datetime(2026, 7, 15, 15, 30, tzinfo=UTC)
    assert candidate.updated_at == candidate.created_at


@pytest.mark.parametrize(
    ("initial_status", "target_status"),
    (
        (TradingCandidateStatus.NEW, TradingCandidateStatus.REVIEWING),
        (TradingCandidateStatus.NEW, TradingCandidateStatus.REJECTED),
        (TradingCandidateStatus.NEW, TradingCandidateStatus.ARCHIVED),
        (TradingCandidateStatus.REVIEWING, TradingCandidateStatus.REJECTED),
        (TradingCandidateStatus.REVIEWING, TradingCandidateStatus.ARCHIVED),
        (TradingCandidateStatus.REJECTED, TradingCandidateStatus.ARCHIVED),
    ),
)
def test_trading_candidate_allows_configured_status_transition(
    initial_status: TradingCandidateStatus,
    target_status: TradingCandidateStatus,
) -> None:
    candidate = _candidate()
    if initial_status is not TradingCandidateStatus.NEW:
        candidate = candidate.transition_to(
            initial_status,
            observed_at=candidate.updated_at + timedelta(minutes=1),
        )

    updated = candidate.transition_to(
        target_status,
        observed_at=candidate.updated_at + timedelta(minutes=1),
    )

    assert updated.status is target_status
    assert updated.updated_at > candidate.updated_at


def test_trading_candidate_supports_explicit_review_lifecycle() -> None:
    candidate = _candidate()
    review_time = candidate.updated_at + timedelta(minutes=1)
    reject_time = review_time + timedelta(minutes=1)
    archive_time = reject_time + timedelta(minutes=1)

    reviewing = candidate.transition_to(
        TradingCandidateStatus.REVIEWING,
        observed_at=review_time,
    )
    rejected = reviewing.transition_to(
        TradingCandidateStatus.REJECTED,
        observed_at=reject_time,
    )
    archived = rejected.transition_to(
        TradingCandidateStatus.ARCHIVED,
        observed_at=archive_time,
    )

    assert reviewing.status is TradingCandidateStatus.REVIEWING
    assert reviewing.updated_at == review_time
    assert rejected.status is TradingCandidateStatus.REJECTED
    assert rejected.updated_at == reject_time
    assert archived.status is TradingCandidateStatus.ARCHIVED
    assert archived.updated_at == archive_time
    assert archived.created_at == candidate.created_at
    assert archived.symbol == candidate.symbol
    assert archived.origin == candidate.origin


@pytest.mark.parametrize(
    ("initial_status", "target_status"),
    (
        (TradingCandidateStatus.NEW, TradingCandidateStatus.NEW),
        (TradingCandidateStatus.REVIEWING, TradingCandidateStatus.NEW),
        (TradingCandidateStatus.REJECTED, TradingCandidateStatus.REVIEWING),
        (TradingCandidateStatus.ARCHIVED, TradingCandidateStatus.REJECTED),
    ),
)
def test_trading_candidate_rejects_invalid_status_transition(
    initial_status: TradingCandidateStatus,
    target_status: TradingCandidateStatus,
) -> None:
    candidate = _candidate()
    if initial_status is TradingCandidateStatus.REVIEWING:
        candidate = candidate.transition_to(
            initial_status,
            observed_at=candidate.updated_at + timedelta(minutes=1),
        )
    elif initial_status is TradingCandidateStatus.REJECTED:
        candidate = candidate.transition_to(
            initial_status,
            observed_at=candidate.updated_at + timedelta(minutes=1),
        )
    elif initial_status is TradingCandidateStatus.ARCHIVED:
        candidate = candidate.transition_to(
            initial_status,
            observed_at=candidate.updated_at + timedelta(minutes=1),
        )

    with pytest.raises(
        InvalidTradingCandidateStatusTransitionError,
        match=f"from {initial_status.value} to {target_status.value}",
    ):
        candidate.transition_to(
            target_status,
            observed_at=candidate.updated_at + timedelta(minutes=1),
        )


def test_trading_candidate_rejects_transition_timestamp_regression() -> None:
    candidate = _candidate()

    with pytest.raises(ValueError, match="observed_at"):
        candidate.transition_to(
            TradingCandidateStatus.REVIEWING,
            observed_at=candidate.updated_at - timedelta(seconds=1),
        )


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
