from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from trading_platform.application.trading_decisions.trading_decisions import (
    TradingDecisionAcceptanceConflictError,
    TradingDecisionAlreadyExistsError,
)
from trading_platform.domain.trading_candidates.trading_candidate import (
    TradingCandidate,
    TradingCandidateOrigin,
    TradingCandidateStatus,
)
from trading_platform.domain.trading_decisions.trading_decision import (
    TradingDecision,
    TradingDecisionStatus,
)
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


def test_sqlite_repository_lists_history_newest_update_first(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "trading-candidates.db"
    candidate_repository = SqliteTradingCandidateRepository(database_path)
    first_candidate = _reviewing_candidate()
    second_created_at = datetime(2026, 7, 16, 9, 5, tzinfo=UTC)
    second_candidate = TradingCandidate.create_new(
        candidate_id="33333333-3333-4333-8333-333333333333",
        symbol="MSFT",
        origin=TradingCandidateOrigin.SCANNER,
        observed_at=second_created_at,
    ).transition_to(
        TradingCandidateStatus.REVIEWING,
        observed_at=second_created_at + timedelta(minutes=1),
    )
    candidate_repository.add(first_candidate)
    candidate_repository.add(second_candidate)

    repository = SqliteTradingDecisionRepository(database_path)
    first_decision = _decision(first_candidate)
    second_decision = TradingDecision.create_draft(
        decision_id="44444444-4444-4444-8444-444444444444",
        candidate_id=second_candidate.candidate_id,
        symbol=second_candidate.symbol,
        rationale="A newer reviewed setup.",
        observed_at=datetime(2026, 7, 16, 10, 0, tzinfo=UTC),
    )
    repository.add(first_decision)
    repository.add(second_decision)

    restored_repository = SqliteTradingDecisionRepository(database_path)

    assert restored_repository.list_decisions() == (second_decision, first_decision)


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


def test_sqlite_repository_accepts_candidate_and_decision_atomically(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "trading-candidates.db"
    candidate_repository = SqliteTradingCandidateRepository(database_path)
    candidate = _reviewing_candidate()
    candidate_repository.add(candidate)
    decision_repository = SqliteTradingDecisionRepository(database_path)
    decision = _decision(candidate)
    decision_repository.add(decision)
    accepted_at = datetime(2026, 7, 16, 10, 0, tzinfo=UTC)
    accepted_candidate = candidate.transition_to(
        TradingCandidateStatus.ACCEPTED,
        observed_at=accepted_at,
    )
    accepted_decision = decision.transition_to(
        TradingDecisionStatus.ACCEPTED,
        observed_at=accepted_at,
    )

    decision_repository.accept(
        accepted_candidate,
        accepted_decision,
        expected_candidate_status=TradingCandidateStatus.REVIEWING,
        expected_decision_status=TradingDecisionStatus.DRAFT,
    )

    assert candidate_repository.find_by_id(candidate.candidate_id.value) == (
        accepted_candidate
    )
    assert decision_repository.find_by_candidate_id(candidate.candidate_id.value) == (
        accepted_decision
    )


def test_sqlite_repository_rolls_back_candidate_when_decision_is_stale(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "trading-candidates.db"
    candidate_repository = SqliteTradingCandidateRepository(database_path)
    candidate = _reviewing_candidate()
    candidate_repository.add(candidate)
    decision_repository = SqliteTradingDecisionRepository(database_path)
    decision = _decision(candidate)
    decision_repository.add(decision)
    externally_accepted_at = datetime(2026, 7, 16, 9, 45, tzinfo=UTC)
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            UPDATE trading_decisions
            SET status = ?, updated_at = ?
            WHERE decision_id = ?
            """,
            (
                TradingDecisionStatus.ACCEPTED.value,
                externally_accepted_at.isoformat().replace("+00:00", "Z"),
                decision.decision_id.value,
            ),
        )

    accepted_at = datetime(2026, 7, 16, 10, 0, tzinfo=UTC)
    accepted_candidate = candidate.transition_to(
        TradingCandidateStatus.ACCEPTED,
        observed_at=accepted_at,
    )
    accepted_decision = decision.transition_to(
        TradingDecisionStatus.ACCEPTED,
        observed_at=accepted_at,
    )

    with pytest.raises(TradingDecisionAcceptanceConflictError):
        decision_repository.accept(
            accepted_candidate,
            accepted_decision,
            expected_candidate_status=TradingCandidateStatus.REVIEWING,
            expected_decision_status=TradingDecisionStatus.DRAFT,
        )

    assert candidate_repository.find_by_id(candidate.candidate_id.value) == candidate
    restored_decision = decision_repository.find_by_candidate_id(
        candidate.candidate_id.value
    )
    assert restored_decision is not None
    assert restored_decision.status is TradingDecisionStatus.ACCEPTED
    assert restored_decision.updated_at == externally_accepted_at
