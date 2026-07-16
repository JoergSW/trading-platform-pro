from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol

from trading_platform.domain.trading_candidates.trading_candidate import (
    CandidateId,
    TradingCandidate,
    TradingCandidateStatus,
)
from trading_platform.domain.trading_decisions.trading_decision import (
    TradingDecision,
    validate_trading_decision_rationale,
)


class TradingDecisionRepositoryError(RuntimeError):
    """Base error raised by Trading Decision persistence adapters."""


class TradingDecisionAlreadyExistsError(TradingDecisionRepositoryError):
    """Raised when persistence rejects a duplicate Candidate-linked decision."""


class TradingDecisionCandidateRepository(Protocol):
    """Narrow Application port for candidate eligibility lookup."""

    def find_by_id(self, candidate_id: str) -> TradingCandidate | None:
        """Return one Trading Candidate by stable identity, if present."""


class TradingDecisionRepository(Protocol):
    """Application-owned persistence port for Trading Decisions."""

    def find_by_candidate_id(self, candidate_id: str) -> TradingDecision | None:
        """Return the decision linked to one candidate, if present."""

    def add(self, decision: TradingDecision) -> None:
        """Persist one Trading Decision atomically."""


class TradingDecisionClock(Protocol):
    """Application-owned UTC clock port."""

    def now_utc(self) -> datetime:
        """Return the current timezone-aware UTC timestamp."""


class TradingDecisionIdGenerator(Protocol):
    """Application-owned Trading Decision identity port."""

    def new_id(self) -> str:
        """Return one new canonical decision identifier."""


class TradingDecisionDraftLoadResult(StrEnum):
    """Deterministic outcome of loading one candidate-linked draft."""

    READY = "READY"
    NO_DRAFT = "NO DRAFT"
    NOT_FOUND = "NOT FOUND"
    ERROR = "ERROR"


@dataclass(frozen=True, slots=True)
class TradingDecisionDraftLoadOutcome:
    """Application result for one linked-draft lookup."""

    result: TradingDecisionDraftLoadResult
    decision: TradingDecision | None
    detail: str


class TradingDecisionDraftCreateResult(StrEnum):
    """Deterministic outcome of one explicit Create Decision Draft action."""

    CREATED = "CREATED"
    ALREADY_EXISTS = "ALREADY EXISTS"
    CANDIDATE_NOT_REVIEWING = "CANDIDATE NOT REVIEWING"
    NOT_FOUND = "NOT FOUND"
    INVALID_RATIONALE = "INVALID RATIONALE"
    ERROR = "ERROR"


@dataclass(frozen=True, slots=True)
class TradingDecisionDraftCreateOutcome:
    """Application result for one explicit decision-draft creation."""

    result: TradingDecisionDraftCreateResult
    decision: TradingDecision | None
    detail: str


class TradingDecisionService:
    """Coordinate explicit, persistent Trading Decision draft creation."""

    def __init__(
        self,
        candidate_repository: TradingDecisionCandidateRepository,
        decision_repository: TradingDecisionRepository,
        clock: TradingDecisionClock,
        id_generator: TradingDecisionIdGenerator,
    ) -> None:
        self._candidate_repository = candidate_repository
        self._decision_repository = decision_repository
        self._clock = clock
        self._id_generator = id_generator

    def load_draft_for_candidate(
        self,
        candidate_id: str,
    ) -> TradingDecisionDraftLoadOutcome:
        validated_id = CandidateId(candidate_id)
        try:
            candidate = self._candidate_repository.find_by_id(validated_id.value)
            if candidate is None:
                return TradingDecisionDraftLoadOutcome(
                    TradingDecisionDraftLoadResult.NOT_FOUND,
                    None,
                    "Trading Candidate no longer exists.",
                )
            decision = self._decision_repository.find_by_candidate_id(
                validated_id.value
            )
        except Exception as exc:
            return TradingDecisionDraftLoadOutcome(
                TradingDecisionDraftLoadResult.ERROR,
                None,
                f"Trading Decision storage could not be read: {type(exc).__name__}.",
            )

        if decision is None:
            return TradingDecisionDraftLoadOutcome(
                TradingDecisionDraftLoadResult.NO_DRAFT,
                None,
                f"No Trading Decision draft exists for {candidate.symbol}.",
            )
        return TradingDecisionDraftLoadOutcome(
            TradingDecisionDraftLoadResult.READY,
            decision,
            f"Trading Decision draft for {candidate.symbol} loaded.",
        )

    def create_draft(
        self,
        candidate_id: str,
        rationale: str,
    ) -> TradingDecisionDraftCreateOutcome:
        validated_id = CandidateId(candidate_id)
        try:
            validated_rationale = validate_trading_decision_rationale(rationale)
        except (TypeError, ValueError) as exc:
            return TradingDecisionDraftCreateOutcome(
                TradingDecisionDraftCreateResult.INVALID_RATIONALE,
                None,
                str(exc),
            )

        try:
            candidate = self._candidate_repository.find_by_id(validated_id.value)
            if candidate is None:
                return TradingDecisionDraftCreateOutcome(
                    TradingDecisionDraftCreateResult.NOT_FOUND,
                    None,
                    "Trading Candidate no longer exists.",
                )
            if candidate.status is not TradingCandidateStatus.REVIEWING:
                return TradingDecisionDraftCreateOutcome(
                    TradingDecisionDraftCreateResult.CANDIDATE_NOT_REVIEWING,
                    None,
                    "A Trading Decision draft requires a REVIEWING candidate.",
                )

            existing = self._decision_repository.find_by_candidate_id(
                validated_id.value
            )
            if existing is not None:
                return TradingDecisionDraftCreateOutcome(
                    TradingDecisionDraftCreateResult.ALREADY_EXISTS,
                    existing,
                    f"A Trading Decision draft already exists for {candidate.symbol}.",
                )

            decision = TradingDecision.create_draft(
                decision_id=self._id_generator.new_id(),
                candidate_id=candidate.candidate_id,
                symbol=candidate.symbol,
                rationale=validated_rationale,
                observed_at=self._clock.now_utc(),
            )
            self._decision_repository.add(decision)
        except TradingDecisionAlreadyExistsError:
            return self._restore_duplicate(
                candidate.candidate_id.value, candidate.symbol
            )
        except Exception as exc:
            return TradingDecisionDraftCreateOutcome(
                TradingDecisionDraftCreateResult.ERROR,
                None,
                f"Trading Decision draft could not be created: {type(exc).__name__}.",
            )

        return TradingDecisionDraftCreateOutcome(
            TradingDecisionDraftCreateResult.CREATED,
            decision,
            f"Trading Decision draft for {candidate.symbol} was created.",
        )

    def _restore_duplicate(
        self,
        candidate_id: str,
        symbol: str,
    ) -> TradingDecisionDraftCreateOutcome:
        try:
            existing = self._decision_repository.find_by_candidate_id(candidate_id)
        except Exception as exc:
            return TradingDecisionDraftCreateOutcome(
                TradingDecisionDraftCreateResult.ERROR,
                None,
                (
                    "Duplicate Trading Decision could not be restored: "
                    f"{type(exc).__name__}."
                ),
            )
        if existing is None:
            return TradingDecisionDraftCreateOutcome(
                TradingDecisionDraftCreateResult.ERROR,
                None,
                "Duplicate Trading Decision could not be restored.",
            )
        return TradingDecisionDraftCreateOutcome(
            TradingDecisionDraftCreateResult.ALREADY_EXISTS,
            existing,
            f"A Trading Decision draft already exists for {symbol}.",
        )
