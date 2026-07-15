from __future__ import annotations

from datetime import UTC, datetime

from trading_platform.application.trading_candidates.trading_candidates import (
    TradingCandidateAddResult,
    TradingCandidateCollectionState,
    TradingCandidateService,
)
from trading_platform.domain.trading_candidates.trading_candidate import (
    TradingCandidate,
)

CANDIDATE_ID = "11111111-1111-4111-8111-111111111111"


class InMemoryTradingCandidateRepository:
    def __init__(self) -> None:
        self.candidates: dict[str, TradingCandidate] = {}
        self.add_calls = 0

    def list_candidates(self) -> tuple[TradingCandidate, ...]:
        return tuple(self.candidates.values())

    def find_by_symbol(self, symbol: str) -> TradingCandidate | None:
        return self.candidates.get(symbol)

    def add(self, candidate: TradingCandidate) -> None:
        self.add_calls += 1
        self.candidates[candidate.symbol] = candidate


class FailingTradingCandidateRepository(InMemoryTradingCandidateRepository):
    def list_candidates(self) -> tuple[TradingCandidate, ...]:
        raise OSError("controlled")

    def find_by_symbol(self, symbol: str) -> TradingCandidate | None:
        raise OSError("controlled")


class FixedClock:
    def now_utc(self) -> datetime:
        return datetime(2026, 7, 15, 15, 30, tzinfo=UTC)


class FixedIdGenerator:
    def new_id(self) -> str:
        return CANDIDATE_ID


def _service(repository: InMemoryTradingCandidateRepository) -> TradingCandidateService:
    return TradingCandidateService(repository, FixedClock(), FixedIdGenerator())


def test_trading_candidate_service_adds_and_publishes_candidate() -> None:
    repository = InMemoryTradingCandidateRepository()
    service = _service(repository)
    observed_states: list[TradingCandidateCollectionState] = []
    service.subscribe(lambda collection: observed_states.append(collection.state))

    outcome = service.add_candidate("AAPL", "Scanner")

    assert outcome.result is TradingCandidateAddResult.ADDED
    assert outcome.candidate is not None
    assert outcome.candidate.symbol == "AAPL"
    assert repository.add_calls == 1
    assert service.collection.state is TradingCandidateCollectionState.READY
    assert service.collection.candidates == (outcome.candidate,)
    assert observed_states == [
        TradingCandidateCollectionState.UNAVAILABLE,
        TradingCandidateCollectionState.READY,
    ]


def test_trading_candidate_service_prevents_duplicate_symbol() -> None:
    repository = InMemoryTradingCandidateRepository()
    service = _service(repository)

    first = service.add_candidate("AAPL", "Scanner")
    duplicate = service.add_candidate("AAPL", "Watchlist")

    assert first.result is TradingCandidateAddResult.ADDED
    assert duplicate.result is TradingCandidateAddResult.ALREADY_EXISTS
    assert duplicate.candidate is first.candidate
    assert repository.add_calls == 1
    assert service.collection.candidates[0].origin.value == "Scanner"


def test_trading_candidate_service_translates_repository_failure() -> None:
    service = _service(FailingTradingCandidateRepository())

    collection = service.refresh()
    outcome = service.add_candidate("AAPL", "Scanner")

    assert collection.state is TradingCandidateCollectionState.ERROR
    assert outcome.result is TradingCandidateAddResult.ERROR
    assert outcome.candidate is None
    assert service.collection.state is TradingCandidateCollectionState.ERROR
