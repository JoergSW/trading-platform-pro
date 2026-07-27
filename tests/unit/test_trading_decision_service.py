from __future__ import annotations

from datetime import UTC, datetime, timedelta

from trading_platform.application.trading_candidates.trading_candidates import (
    TradingCandidateAlreadyExistsError,
)
from trading_platform.application.trading_decisions.trading_decisions import (
    TradingDecisionAcceptanceConflictError,
    TradingDecisionAcceptanceResult,
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
from trading_platform.domain.trading_decisions.trading_decision import (
    TradingDecision,
    TradingDecisionStatus,
)

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
    def __init__(self, candidate_repository: InMemoryCandidateRepository) -> None:
        self.candidate_repository = candidate_repository
        self.decisions: dict[str, TradingDecision] = {}

    def find_by_candidate_id(self, candidate_id: str) -> TradingDecision | None:
        return self.decisions.get(candidate_id)

    def add(self, decision: TradingDecision) -> None:
        if decision.candidate_id.value in self.decisions:
            raise TradingDecisionAlreadyExistsError
        self.decisions[decision.candidate_id.value] = decision

    def accept(
        self,
        candidate: TradingCandidate,
        decision: TradingDecision,
        *,
        expected_candidate_status: TradingCandidateStatus,
        expected_decision_status: TradingDecisionStatus,
    ) -> None:
        stored_candidate = self.candidate_repository.find_by_id(
            candidate.candidate_id.value
        )
        stored_decision = self.find_by_candidate_id(candidate.candidate_id.value)
        assert stored_candidate is not None
        assert stored_decision is not None
        assert stored_candidate.status is expected_candidate_status
        assert stored_decision.status is expected_decision_status
        self.candidate_repository.candidates[candidate.symbol] = candidate
        self.decisions[candidate.candidate_id.value] = decision


class ConflictingDecisionRepository(InMemoryDecisionRepository):
    def accept(
        self,
        candidate: TradingCandidate,
        decision: TradingDecision,
        *,
        expected_candidate_status: TradingCandidateStatus,
        expected_decision_status: TradingDecisionStatus,
    ) -> None:
        raise TradingDecisionAcceptanceConflictError("controlled")


class AdvancingClock:
    def __init__(self) -> None:
        self.current = datetime(2026, 7, 16, 9, 30, tzinfo=UTC)

    def now_utc(self) -> datetime:
        value = self.current
        self.current += timedelta(minutes=1)
        return value


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
    decision_repository = InMemoryDecisionRepository(candidate_repository)
    return (
        TradingDecisionService(
            candidate_repository,
            decision_repository,
            AdvancingClock(),
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


def test_service_accepts_candidate_and_decision_atomically() -> None:
    candidate = _reviewing_candidate()
    service, candidate_repository, decision_repository = _service(candidate)
    created = service.create_draft(candidate.candidate_id.value, "Reviewed setup.")
    assert created.decision is not None

    accepted = service.accept_decision(candidate.candidate_id.value)

    assert accepted.result is TradingDecisionAcceptanceResult.ACCEPTED
    assert accepted.candidate is not None
    assert accepted.decision is not None
    assert accepted.candidate.status is TradingCandidateStatus.ACCEPTED
    assert accepted.decision.status is TradingDecisionStatus.ACCEPTED
    assert accepted.candidate.updated_at == accepted.decision.updated_at
    assert candidate_repository.find_by_id(candidate.candidate_id.value) == (
        accepted.candidate
    )
    assert decision_repository.find_by_candidate_id(candidate.candidate_id.value) == (
        accepted.decision
    )


def test_service_requires_reviewing_candidate_and_draft_for_acceptance() -> None:
    candidate = _reviewing_candidate()
    service, candidate_repository, decision_repository = _service(candidate)

    missing_draft = service.accept_decision(candidate.candidate_id.value)
    assert missing_draft.result is TradingDecisionAcceptanceResult.NOT_FOUND

    created = service.create_draft(candidate.candidate_id.value, "Reviewed setup.")
    assert created.decision is not None
    rejected_candidate = candidate.transition_to(
        TradingCandidateStatus.REJECTED,
        observed_at=datetime(2026, 7, 16, 9, 32, tzinfo=UTC),
    )
    candidate_repository.candidates[candidate.symbol] = rejected_candidate

    wrong_candidate = service.accept_decision(candidate.candidate_id.value)
    assert wrong_candidate.result is (
        TradingDecisionAcceptanceResult.CANDIDATE_NOT_REVIEWING
    )

    candidate_repository.candidates[candidate.symbol] = candidate
    decision_repository.decisions[candidate.candidate_id.value] = (
        created.decision.transition_to(
            TradingDecisionStatus.ACCEPTED,
            observed_at=datetime(2026, 7, 16, 9, 33, tzinfo=UTC),
        )
    )
    wrong_decision = service.accept_decision(candidate.candidate_id.value)
    assert wrong_decision.result is TradingDecisionAcceptanceResult.DECISION_NOT_DRAFT


def test_service_reports_atomic_acceptance_conflict_without_mutation() -> None:
    candidate = _reviewing_candidate()
    candidate_repository = InMemoryCandidateRepository()
    candidate_repository.candidates[candidate.symbol] = candidate
    decision_repository = ConflictingDecisionRepository(candidate_repository)
    service = TradingDecisionService(
        candidate_repository,
        decision_repository,
        AdvancingClock(),
        FixedIdGenerator(),
    )
    created = service.create_draft(candidate.candidate_id.value, "Reviewed setup.")
    assert created.decision is not None

    outcome = service.accept_decision(candidate.candidate_id.value)

    assert outcome.result is TradingDecisionAcceptanceResult.CONFLICT
    assert candidate_repository.find_by_id(candidate.candidate_id.value) == candidate
    assert decision_repository.find_by_candidate_id(candidate.candidate_id.value) == (
        created.decision
    )
