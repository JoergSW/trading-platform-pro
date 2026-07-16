from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol

from trading_platform.domain.instruments.instrument_symbol import (
    validate_instrument_symbol,
)
from trading_platform.domain.trading_candidates.trading_candidate import (
    CandidateId,
    InvalidTradingCandidateStatusTransitionError,
    TradingCandidate,
    TradingCandidateOrigin,
    TradingCandidateStatus,
)


class TradingCandidateRepositoryError(RuntimeError):
    """Base error raised by Trading Candidate persistence adapters."""


class TradingCandidateAlreadyExistsError(TradingCandidateRepositoryError):
    """Raised when persistence rejects a duplicate candidate symbol."""


class TradingCandidateNotFoundError(TradingCandidateRepositoryError):
    """Raised when persistence cannot update the requested candidate."""


class TradingCandidateConcurrentUpdateError(TradingCandidateRepositoryError):
    """Raised when persistence detects a stale candidate status."""


class TradingCandidateRepository(Protocol):
    """Application-owned persistence port for Trading Candidates."""

    def list_candidates(self) -> tuple[TradingCandidate, ...]:
        """Return all candidates in deterministic creation order."""

    def find_by_symbol(self, symbol: str) -> TradingCandidate | None:
        """Return one candidate by symbol, if present."""

    def find_by_id(self, candidate_id: str) -> TradingCandidate | None:
        """Return one candidate by stable identity, if present."""

    def add(self, candidate: TradingCandidate) -> None:
        """Persist one candidate atomically."""

    def update_status(
        self,
        candidate: TradingCandidate,
        *,
        expected_status: TradingCandidateStatus,
    ) -> None:
        """Persist one status change using optimistic status matching."""


class TradingCandidateClock(Protocol):
    """Application-owned UTC clock port."""

    def now_utc(self) -> datetime:
        """Return the current timezone-aware UTC timestamp."""


class TradingCandidateIdGenerator(Protocol):
    """Application-owned candidate identity port."""

    def new_id(self) -> str:
        """Return one new canonical candidate identifier."""


class TradingCandidateCollectionState(StrEnum):
    """Explicit state of the persistent candidate collection."""

    UNAVAILABLE = "UNAVAILABLE"
    EMPTY = "EMPTY"
    READY = "READY"
    ERROR = "ERROR"


@dataclass(frozen=True, slots=True)
class TradingCandidateCollection:
    """Immutable Application snapshot displayed by the Decision Center."""

    state: TradingCandidateCollectionState
    candidates: tuple[TradingCandidate, ...]
    detail: str

    def __post_init__(self) -> None:
        if not isinstance(self.state, TradingCandidateCollectionState):
            raise TypeError("state must be a TradingCandidateCollectionState")
        if not isinstance(self.candidates, tuple):
            raise TypeError("candidates must be a tuple")
        if not isinstance(self.detail, str) or not self.detail:
            raise ValueError("detail must be non-blank text")
        if self.state is TradingCandidateCollectionState.READY and not self.candidates:
            raise ValueError("READY collection must contain candidates")
        if self.state is not TradingCandidateCollectionState.READY and self.candidates:
            raise ValueError(f"{self.state} collection must not contain candidates")

    @classmethod
    def unavailable(cls, detail: str) -> TradingCandidateCollection:
        return cls(TradingCandidateCollectionState.UNAVAILABLE, (), detail)

    @classmethod
    def from_candidates(
        cls,
        candidates: tuple[TradingCandidate, ...],
    ) -> TradingCandidateCollection:
        if candidates:
            return cls(
                TradingCandidateCollectionState.READY,
                candidates,
                f"{len(candidates)} persistent Trading Candidate(s) loaded.",
            )
        return cls(
            TradingCandidateCollectionState.EMPTY,
            (),
            "No persistent Trading Candidates are currently stored.",
        )

    @classmethod
    def error(cls, detail: str) -> TradingCandidateCollection:
        return cls(TradingCandidateCollectionState.ERROR, (), detail)


class TradingCandidateAddResult(StrEnum):
    """Deterministic outcome of one explicit candidate-intake request."""

    ADDED = "ADDED"
    ALREADY_EXISTS = "ALREADY EXISTS"
    ERROR = "ERROR"


@dataclass(frozen=True, slots=True)
class TradingCandidateAddOutcome:
    """Application result for an explicit Add to Decision Center action."""

    result: TradingCandidateAddResult
    candidate: TradingCandidate | None
    detail: str


class TradingCandidateReviewResult(StrEnum):
    """Deterministic outcome of one explicit candidate-review action."""

    UPDATED = "UPDATED"
    INVALID_TRANSITION = "INVALID TRANSITION"
    NOT_FOUND = "NOT FOUND"
    CONFLICT = "CONFLICT"
    ERROR = "ERROR"


@dataclass(frozen=True, slots=True)
class TradingCandidateReviewOutcome:
    """Application result for one explicit candidate lifecycle action."""

    result: TradingCandidateReviewResult
    candidate: TradingCandidate | None
    detail: str


TradingCandidateCollectionListener = Callable[[TradingCandidateCollection], None]


class TradingCandidateService:
    """Coordinate persistent Trading Candidate intake, review and collection reads."""

    def __init__(
        self,
        repository: TradingCandidateRepository,
        clock: TradingCandidateClock,
        id_generator: TradingCandidateIdGenerator,
    ) -> None:
        self._repository = repository
        self._clock = clock
        self._id_generator = id_generator
        self._collection = TradingCandidateCollection.unavailable(
            "Trading Candidates have not been loaded yet."
        )
        self._listeners: list[TradingCandidateCollectionListener] = []

    @property
    def collection(self) -> TradingCandidateCollection:
        return self._collection

    def refresh(self) -> TradingCandidateCollection:
        try:
            candidates = self._repository.list_candidates()
        except Exception as exc:  # translate infrastructure failures at the boundary
            collection = TradingCandidateCollection.error(
                f"Trading Candidate storage could not be read: {type(exc).__name__}."
            )
        else:
            collection = TradingCandidateCollection.from_candidates(candidates)
        self._publish(collection)
        return collection

    def add_candidate(
        self,
        symbol: str,
        origin: str | TradingCandidateOrigin,
    ) -> TradingCandidateAddOutcome:
        validated_symbol = validate_instrument_symbol(symbol)
        validated_origin = TradingCandidateOrigin(origin)

        try:
            existing = self._repository.find_by_symbol(validated_symbol)
            if existing is not None:
                self._refresh_after_change()
                return TradingCandidateAddOutcome(
                    TradingCandidateAddResult.ALREADY_EXISTS,
                    existing,
                    f"{validated_symbol} already exists in the Decision Center.",
                )

            candidate = TradingCandidate.create_new(
                candidate_id=self._id_generator.new_id(),
                symbol=validated_symbol,
                origin=validated_origin,
                observed_at=self._clock.now_utc(),
            )
            self._repository.add(candidate)
        except TradingCandidateAlreadyExistsError:
            try:
                existing = self._repository.find_by_symbol(validated_symbol)
            except Exception as exc:
                return self._add_error_outcome(exc)
            if existing is None:
                return self._add_error_outcome(
                    TradingCandidateRepositoryError(
                        "Duplicate persistence result could not be restored."
                    )
                )
            self._refresh_after_change()
            return TradingCandidateAddOutcome(
                TradingCandidateAddResult.ALREADY_EXISTS,
                existing,
                f"{validated_symbol} already exists in the Decision Center.",
            )
        except Exception as exc:  # translate infrastructure failures at the boundary
            return self._add_error_outcome(exc)

        refresh_error = self._refresh_after_change()
        detail = f"{validated_symbol} was added to the Decision Center."
        if refresh_error is not None:
            detail += f" Candidate list refresh failed: {refresh_error}."
        return TradingCandidateAddOutcome(
            TradingCandidateAddResult.ADDED,
            candidate,
            detail,
        )

    def transition_candidate(
        self,
        candidate_id: str,
        target_status: str | TradingCandidateStatus,
    ) -> TradingCandidateReviewOutcome:
        validated_id = CandidateId(candidate_id)
        validated_target = TradingCandidateStatus(target_status)

        try:
            existing = self._repository.find_by_id(validated_id.value)
        except Exception as exc:
            return self._review_error_outcome(exc)
        if existing is None:
            self._refresh_after_change()
            return TradingCandidateReviewOutcome(
                TradingCandidateReviewResult.NOT_FOUND,
                None,
                "Trading Candidate no longer exists.",
            )

        try:
            updated = existing.transition_to(
                validated_target,
                observed_at=self._clock.now_utc(),
            )
        except InvalidTradingCandidateStatusTransitionError as exc:
            return TradingCandidateReviewOutcome(
                TradingCandidateReviewResult.INVALID_TRANSITION,
                existing,
                str(exc),
            )
        except Exception as exc:
            return self._review_error_outcome(exc)

        try:
            self._repository.update_status(
                updated,
                expected_status=existing.status,
            )
        except TradingCandidateNotFoundError:
            self._refresh_after_change()
            return TradingCandidateReviewOutcome(
                TradingCandidateReviewResult.NOT_FOUND,
                None,
                "Trading Candidate no longer exists.",
            )
        except TradingCandidateConcurrentUpdateError:
            self._refresh_after_change()
            return TradingCandidateReviewOutcome(
                TradingCandidateReviewResult.CONFLICT,
                None,
                "Trading Candidate changed concurrently. Refresh and review it again.",
            )
        except Exception as exc:  # translate infrastructure failures at the boundary
            return self._review_error_outcome(exc)

        refresh_error = self._refresh_after_change()
        detail = (
            f"{updated.symbol} status changed from {existing.status.value} "
            f"to {updated.status.value}."
        )
        if refresh_error is not None:
            detail += f" Candidate list refresh failed: {refresh_error}."
        return TradingCandidateReviewOutcome(
            TradingCandidateReviewResult.UPDATED,
            updated,
            detail,
        )

    def subscribe(
        self,
        listener: TradingCandidateCollectionListener,
        *,
        notify_current: bool = True,
    ) -> None:
        if not callable(listener):
            raise TypeError("listener must be callable")
        if listener in self._listeners:
            return
        self._listeners.append(listener)
        if notify_current:
            listener(self._collection)

    def unsubscribe(self, listener: TradingCandidateCollectionListener) -> bool:
        try:
            self._listeners.remove(listener)
        except ValueError:
            return False
        return True

    def _add_error_outcome(self, error: Exception) -> TradingCandidateAddOutcome:
        error_name = type(error).__name__
        self._publish(
            TradingCandidateCollection.error(
                f"Trading Candidate storage failed during intake: {error_name}."
            )
        )
        return TradingCandidateAddOutcome(
            TradingCandidateAddResult.ERROR,
            None,
            f"Trading Candidate could not be added: {error_name}.",
        )

    def _review_error_outcome(
        self,
        error: Exception,
    ) -> TradingCandidateReviewOutcome:
        error_name = type(error).__name__
        self._publish(
            TradingCandidateCollection.error(
                f"Trading Candidate storage failed during review: {error_name}."
            )
        )
        return TradingCandidateReviewOutcome(
            TradingCandidateReviewResult.ERROR,
            None,
            f"Trading Candidate could not be updated: {error_name}.",
        )

    def _refresh_after_change(self) -> str | None:
        try:
            candidates = self._repository.list_candidates()
        except Exception as exc:
            error_name = type(exc).__name__
            self._publish(
                TradingCandidateCollection.error(
                    f"Trading Candidate list refresh failed: {error_name}."
                )
            )
            return error_name
        self._publish(TradingCandidateCollection.from_candidates(candidates))
        return None

    def _publish(self, collection: TradingCandidateCollection) -> None:
        self._collection = collection
        for listener in tuple(self._listeners):
            listener(collection)
