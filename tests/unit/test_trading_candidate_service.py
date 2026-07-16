from __future__ import annotations

from datetime import UTC, datetime, timedelta

from trading_platform.application.trading_candidates.trading_candidates import (
    TradingCandidateAddResult,
    TradingCandidateCollectionState,
    TradingCandidateConcurrentUpdateError,
    TradingCandidateReviewResult,
    TradingCandidateService,
)
from trading_platform.domain.trading_candidates.trading_candidate import (
    TradingCandidate,
    TradingCandidateStatus,
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

    def find_by_id(self, candidate_id: str) -> TradingCandidate | None:
        return next(
            (
                candidate
                for candidate in self.candidates.values()
                if candidate.candidate_id.value == candidate_id
            ),
            None,
        )

    def add(self, candidate: TradingCandidate) -> None:
        self.add_calls += 1
        self.candidates[candidate.symbol] = candidate

    def update_status(
        self,
        candidate: TradingCandidate,
        *,
        expected_status: TradingCandidateStatus,
    ) -> None:
        stored = self.find_by_id(candidate.candidate_id.value)
        assert stored is not None
        assert stored.status is expected_status
        self.candidates[candidate.symbol] = candidate


class FailingTradingCandidateRepository(InMemoryTradingCandidateRepository):
    def list_candidates(self) -> tuple[TradingCandidate, ...]:
        raise OSError("controlled")

    def find_by_symbol(self, symbol: str) -> TradingCandidate | None:
        raise OSError("controlled")

    def find_by_id(self, candidate_id: str) -> TradingCandidate | None:
        raise OSError("controlled")


class ConflictingTradingCandidateRepository(InMemoryTradingCandidateRepository):
    def update_status(
        self,
        candidate: TradingCandidate,
        *,
        expected_status: TradingCandidateStatus,
    ) -> None:
        raise TradingCandidateConcurrentUpdateError("controlled")


class AdjustableClock:
    def __init__(self) -> None:
        self.current = datetime(2026, 7, 15, 15, 30, tzinfo=UTC)

    def now_utc(self) -> datetime:
        return self.current


class FixedIdGenerator:
    def new_id(self) -> str:
        return CANDIDATE_ID


def _service(
    repository: InMemoryTradingCandidateRepository,
    clock: AdjustableClock | None = None,
) -> tuple[TradingCandidateService, AdjustableClock]:
    service_clock = clock or AdjustableClock()
    return (
        TradingCandidateService(repository, service_clock, FixedIdGenerator()),
        service_clock,
    )


def test_trading_candidate_service_adds_and_publishes_candidate() -> None:
    repository = InMemoryTradingCandidateRepository()
    service, _clock = _service(repository)
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
    service, _clock = _service(repository)

    first = service.add_candidate("AAPL", "Scanner")
    duplicate = service.add_candidate("AAPL", "Watchlist")

    assert first.result is TradingCandidateAddResult.ADDED
    assert duplicate.result is TradingCandidateAddResult.ALREADY_EXISTS
    assert duplicate.candidate is first.candidate
    assert repository.add_calls == 1
    assert service.collection.candidates[0].origin.value == "Scanner"


def test_trading_candidate_service_persists_review_lifecycle() -> None:
    repository = InMemoryTradingCandidateRepository()
    service, clock = _service(repository)
    added = service.add_candidate("AAPL", "Scanner")
    assert added.candidate is not None

    clock.current += timedelta(minutes=1)
    reviewing = service.transition_candidate(
        added.candidate.candidate_id.value,
        TradingCandidateStatus.REVIEWING,
    )
    clock.current += timedelta(minutes=1)
    rejected = service.transition_candidate(
        added.candidate.candidate_id.value,
        TradingCandidateStatus.REJECTED,
    )
    clock.current += timedelta(minutes=1)
    archived = service.transition_candidate(
        added.candidate.candidate_id.value,
        TradingCandidateStatus.ARCHIVED,
    )

    assert reviewing.result is TradingCandidateReviewResult.UPDATED
    assert reviewing.candidate is not None
    assert reviewing.candidate.status is TradingCandidateStatus.REVIEWING
    assert rejected.result is TradingCandidateReviewResult.UPDATED
    assert rejected.candidate is not None
    assert rejected.candidate.status is TradingCandidateStatus.REJECTED
    assert archived.result is TradingCandidateReviewResult.UPDATED
    assert archived.candidate is not None
    assert archived.candidate.status is TradingCandidateStatus.ARCHIVED
    assert service.collection.candidates == (archived.candidate,)


def test_trading_candidate_service_rejects_invalid_transition() -> None:
    repository = InMemoryTradingCandidateRepository()
    service, clock = _service(repository)
    added = service.add_candidate("AAPL", "Scanner")
    assert added.candidate is not None
    clock.current += timedelta(minutes=1)

    outcome = service.transition_candidate(
        added.candidate.candidate_id.value,
        TradingCandidateStatus.NEW,
    )

    assert outcome.result is TradingCandidateReviewResult.INVALID_TRANSITION
    assert outcome.candidate == added.candidate
    assert repository.find_by_symbol("AAPL") == added.candidate


def test_trading_candidate_service_reports_concurrent_update() -> None:
    repository = ConflictingTradingCandidateRepository()
    service, clock = _service(repository)
    added = service.add_candidate("AAPL", "Scanner")
    assert added.candidate is not None
    clock.current += timedelta(minutes=1)

    outcome = service.transition_candidate(
        added.candidate.candidate_id.value,
        TradingCandidateStatus.REVIEWING,
    )

    assert outcome.result is TradingCandidateReviewResult.CONFLICT
    assert repository.find_by_symbol("AAPL") == added.candidate
    assert service.collection.candidates == (added.candidate,)


def test_trading_candidate_service_translates_repository_failure() -> None:
    service, _clock = _service(FailingTradingCandidateRepository())

    collection = service.refresh()
    add_outcome = service.add_candidate("AAPL", "Scanner")
    review_outcome = service.transition_candidate(
        CANDIDATE_ID,
        TradingCandidateStatus.REVIEWING,
    )

    assert collection.state is TradingCandidateCollectionState.ERROR
    assert add_outcome.result is TradingCandidateAddResult.ERROR
    assert add_outcome.candidate is None
    assert review_outcome.result is TradingCandidateReviewResult.ERROR
    assert review_outcome.candidate is None
    assert service.collection.state is TradingCandidateCollectionState.ERROR
