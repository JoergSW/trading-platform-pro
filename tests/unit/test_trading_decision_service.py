from __future__ import annotations

from datetime import UTC, datetime, timedelta

from trading_platform.application.trading_candidates.trading_candidates import (
    TradingCandidateAlreadyExistsError,
)
from trading_platform.application.trading_decisions.trading_decisions import (
    TradingDecisionAlreadyExistsError,
    TradingDecisionDraftCreateResult,
    TradingDecisionDraftLoadResult,
    TradingDecisionService,
)
from trading_platform.domain.trading_candidates.trading_candidate import (
    TradingCandidate,
    TradingCandidateOrigin,
    TradingCandidateStatus,
)
from trading_platform.domain.trading_decisions.trading_decision import TradingDecision

CANDIDATE_ID = "11111111-1111-4111-8111-111111111111"
DECISION_ID = "22222222-2222-4222-8222-222222222222"


class InMemoryCandidateRepository:
    def __init__(self) -> None:
        self.candidates: dict[str, TradingCandidate] = {}

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
        if candidate.symbol in self.candidates:
            raise TradingCandidateAlreadyExistsError
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


class InMemoryDecisionRepository:
    def __init__(self) -> None:
        self.decisions: dict[str, TradingDecision] = {}

    def find_by_candidate_id(self, candidate_id: str) -> TradingDecision | None:
        return self.decisions.get(candidate_id)

    def add(self, decision: TradingDecision) -> None:
        if decision.candidate_id.value in self.decisions:
            raise TradingDecisionAlreadyExistsError
        self.decisions[decision.candidate_id.value] = decision


class FixedClock:
    def now_utc(self) -> datetime:
        return datetime(2026, 7, 16, 9, 30, tzinfo=UTC)


class FixedIdGenerator:
    def new_id(self) -> str:
        return DECISION_ID


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


def _service(
    candidate: TradingCandidate | None = None,
) -> tuple[
    TradingDecisionService,
    InMemoryCandidateRepository,
    InMemoryDecisionRepository,
]:
    candidate_repository = InMemoryCandidateRepository()
    if candidate is not None:
        candidate_repository.candidates[candidate.symbol] = candidate
    decision_repository = InMemoryDecisionRepository()
    return (
        TradingDecisionService(
            candidate_repository,
            decision_repository,
            FixedClock(),
            FixedIdGenerator(),
        ),
        candidate_repository,
        decision_repository,
    )


def test_service_creates_and_loads_draft_for_reviewing_candidate() -> None:
    candidate = _reviewing_candidate()
    service, candidate_repository, _decision_repository = _service(candidate)

    created = service.create_draft(
        candidate.candidate_id.value,
        "Price structure and volume confirm the reviewed setup.",
    )
    loaded = service.load_draft_for_candidate(candidate.candidate_id.value)

    assert created.result is TradingDecisionDraftCreateResult.CREATED
    assert created.decision is not None
    assert created.decision.status.value == "DRAFT"
    assert loaded.result is TradingDecisionDraftLoadResult.READY
    assert loaded.decision == created.decision
    assert candidate_repository.find_by_id(candidate.candidate_id.value) == candidate
    assert candidate_repository.find_by_id(candidate.candidate_id.value).status is (
        TradingCandidateStatus.REVIEWING
    )


def test_service_prevents_second_draft_without_overwriting_rationale() -> None:
    candidate = _reviewing_candidate()
    service, _candidate_repository, _decision_repository = _service(candidate)

    first = service.create_draft(candidate.candidate_id.value, "Original rationale.")
    duplicate = service.create_draft(
        candidate.candidate_id.value,
        "Replacement rationale must not be stored.",
    )

    assert duplicate.result is TradingDecisionDraftCreateResult.ALREADY_EXISTS
    assert duplicate.decision == first.decision
    assert duplicate.decision is not None
    assert duplicate.decision.rationale == "Original rationale."


def test_service_requires_reviewing_candidate_and_valid_rationale() -> None:
    created_at = datetime(2026, 7, 16, 9, 0, tzinfo=UTC)
    new_candidate = TradingCandidate.create_new(
        candidate_id=CANDIDATE_ID,
        symbol="AAPL",
        origin=TradingCandidateOrigin.SCANNER,
        observed_at=created_at,
    )
    service, _candidate_repository, _decision_repository = _service(new_candidate)

    wrong_status = service.create_draft(
        new_candidate.candidate_id.value,
        "A valid rationale.",
    )
    invalid_rationale = service.create_draft(
        new_candidate.candidate_id.value,
        "",
    )

    assert wrong_status.result is (
        TradingDecisionDraftCreateResult.CANDIDATE_NOT_REVIEWING
    )
    assert invalid_rationale.result is (
        TradingDecisionDraftCreateResult.INVALID_RATIONALE
    )


def test_service_reports_missing_candidate_and_empty_draft_state() -> None:
    candidate = _reviewing_candidate()
    service, _candidate_repository, _decision_repository = _service(candidate)

    empty = service.load_draft_for_candidate(candidate.candidate_id.value)
    missing = service.load_draft_for_candidate("33333333-3333-4333-8333-333333333333")

    assert empty.result is TradingDecisionDraftLoadResult.NO_DRAFT
    assert empty.decision is None
    assert missing.result is TradingDecisionDraftLoadResult.NOT_FOUND
    assert missing.decision is None
