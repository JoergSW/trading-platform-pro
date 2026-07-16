from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from trading_platform.application.trading_decisions.trading_decisions import (
    TradingDecisionAlreadyExistsError,
)
from trading_platform.domain.trading_candidates.trading_candidate import (
    TradingCandidate,
    TradingCandidateOrigin,
    TradingCandidateStatus,
)
from trading_platform.domain.trading_decisions.trading_decision import TradingDecision
from trading_platform.infrastructure.trading_candidates.sqlite_repository import (
    SqliteTradingCandidateRepository,
)
from trading_platform.infrastructure.trading_decisions.sqlite_repository import (
    SqliteTradingDecisionRepository,
)

CANDIDATE_ID = "11111111-1111-4111-8111-111111111111"
DECISION_ID = "22222222-2222-4222-8222-222222222222"


def _reviewing_candidate() -> TradingCandidate:
    created_at = datetime(2026, 7, 16, 9, 0, tzinfo=UTC)
    candidate = TradingCandidate.create_new(
        candidate_id=CANDIDATE_ID,
        symbol="AAPL",
        origin=TradingCandidateOrigin.SCANNER,
        observed_at=created_at,
    )
    return candidate.transition_to(
        TradingCandidateStatus.REVIEWING,
        observed_at=created_at + timedelta(minutes=1),
    )


def _decision(candidate: TradingCandidate) -> TradingDecision:
    return TradingDecision.create_draft(
        decision_id=DECISION_ID,
        candidate_id=candidate.candidate_id,
        symbol=candidate.symbol,
        rationale="Price structure and volume confirm the reviewed setup.",
        observed_at=datetime(2026, 7, 16, 9, 30, tzinfo=UTC),
    )


def test_sqlite_repository_persists_and_restores_linked_draft(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "trading-candidates.db"
    candidate = _reviewing_candidate()
    SqliteTradingCandidateRepository(database_path).add(candidate)
    repository = SqliteTradingDecisionRepository(database_path)
    decision = _decision(candidate)

    repository.add(decision)

    restored = SqliteTradingDecisionRepository(database_path).find_by_candidate_id(
        candidate.candidate_id.value
    )
    assert restored == decision
    assert (
        SqliteTradingCandidateRepository(database_path).find_by_id(
            candidate.candidate_id.value
        )
        == candidate
    )


def test_sqlite_repository_prevents_second_draft_for_candidate(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "trading-candidates.db"
    candidate = _reviewing_candidate()
    SqliteTradingCandidateRepository(database_path).add(candidate)
    repository = SqliteTradingDecisionRepository(database_path)
    repository.add(_decision(candidate))
    duplicate = TradingDecision.create_draft(
        decision_id="33333333-3333-4333-8333-333333333333",
        candidate_id=candidate.candidate_id,
        symbol=candidate.symbol,
        rationale="Different rationale.",
        observed_at=datetime(2026, 7, 16, 9, 31, tzinfo=UTC),
    )

    with pytest.raises(TradingDecisionAlreadyExistsError):
        repository.add(duplicate)

    assert repository.find_by_candidate_id(candidate.candidate_id.value) == (
        _decision(candidate)
    )


def test_sqlite_repository_does_not_create_missing_parent_directory(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "missing" / "trading-candidates.db"
    repository = SqliteTradingDecisionRepository(database_path)

    with pytest.raises(FileNotFoundError):
        repository.find_by_candidate_id(CANDIDATE_ID)

    assert not database_path.exists()
