from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from trading_platform.application.trading_candidates.trading_candidates import (
    TradingCandidateAlreadyExistsError,
    TradingCandidateConcurrentUpdateError,
)
from trading_platform.domain.trading_candidates.trading_candidate import (
    TradingCandidate,
    TradingCandidateOrigin,
    TradingCandidateStatus,
)
from trading_platform.infrastructure.trading_candidates.sqlite_repository import (
    SqliteTradingCandidateRepository,
)


def _candidate(candidate_id: str, symbol: str, minute: int) -> TradingCandidate:
    return TradingCandidate.create_new(
        candidate_id=candidate_id,
        symbol=symbol,
        origin=TradingCandidateOrigin.SCANNER,
        observed_at=datetime(2026, 7, 15, 15, minute, tzinfo=UTC),
    )


def test_sqlite_repository_persists_and_restores_candidates(tmp_path: Path) -> None:
    database_path = tmp_path / "trading-candidates.db"
    repository = SqliteTradingCandidateRepository(database_path)
    first = _candidate("11111111-1111-4111-8111-111111111111", "AAPL", 30)
    second = _candidate("22222222-2222-4222-8222-222222222222", "MSFT", 31)

    assert repository.list_candidates() == ()
    assert database_path.is_file()

    repository.add(second)
    repository.add(first)

    restored = SqliteTradingCandidateRepository(database_path).list_candidates()

    assert restored == (first, second)
    assert repository.find_by_symbol("AAPL") == first
    assert repository.find_by_id(first.candidate_id.value) == first
    assert repository.find_by_symbol("NVDA") is None


def test_sqlite_repository_persists_status_update(tmp_path: Path) -> None:
    database_path = tmp_path / "trading-candidates.db"
    repository = SqliteTradingCandidateRepository(database_path)
    candidate = _candidate("11111111-1111-4111-8111-111111111111", "AAPL", 30)
    repository.add(candidate)
    reviewing = candidate.transition_to(
        TradingCandidateStatus.REVIEWING,
        observed_at=candidate.updated_at + timedelta(minutes=1),
    )

    repository.update_status(
        reviewing,
        expected_status=TradingCandidateStatus.NEW,
    )

    restored = SqliteTradingCandidateRepository(database_path).find_by_id(
        candidate.candidate_id.value
    )
    assert restored == reviewing
    assert restored is not None
    assert restored.created_at == candidate.created_at
    assert restored.updated_at > candidate.updated_at


def test_sqlite_repository_rejects_stale_status_update(tmp_path: Path) -> None:
    repository = SqliteTradingCandidateRepository(tmp_path / "candidates.db")
    candidate = _candidate("11111111-1111-4111-8111-111111111111", "AAPL", 30)
    repository.add(candidate)
    reviewing = candidate.transition_to(
        TradingCandidateStatus.REVIEWING,
        observed_at=candidate.updated_at + timedelta(minutes=1),
    )
    repository.update_status(
        reviewing,
        expected_status=TradingCandidateStatus.NEW,
    )
    stale_rejection = candidate.transition_to(
        TradingCandidateStatus.REJECTED,
        observed_at=candidate.updated_at + timedelta(minutes=2),
    )

    with pytest.raises(TradingCandidateConcurrentUpdateError):
        repository.update_status(
            stale_rejection,
            expected_status=TradingCandidateStatus.NEW,
        )

    assert repository.find_by_id(candidate.candidate_id.value) == reviewing


def test_sqlite_repository_prevents_duplicate_symbol(tmp_path: Path) -> None:
    repository = SqliteTradingCandidateRepository(tmp_path / "candidates.db")
    first = _candidate("11111111-1111-4111-8111-111111111111", "AAPL", 30)
    duplicate = _candidate("22222222-2222-4222-8222-222222222222", "AAPL", 31)
    repository.add(first)

    with pytest.raises(TradingCandidateAlreadyExistsError):
        repository.add(duplicate)

    assert repository.list_candidates() == (first,)


def test_sqlite_repository_does_not_create_missing_parent(tmp_path: Path) -> None:
    missing_parent = tmp_path / "missing"
    repository = SqliteTradingCandidateRepository(
        missing_parent / "trading-candidates.db"
    )

    with pytest.raises(FileNotFoundError):
        repository.list_candidates()

    assert not missing_parent.exists()
