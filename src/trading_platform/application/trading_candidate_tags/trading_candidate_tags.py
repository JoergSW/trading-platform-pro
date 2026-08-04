from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from trading_platform.domain.trading_candidate_tags import TradingCandidateTag
from trading_platform.domain.trading_candidates.trading_candidate import (
    CandidateId,
    TradingCandidate,
    TradingCandidateStatus,
)


class TradingCandidateTagRepository(Protocol):
    """Application-owned persistence port for Candidate Tags."""

    def list_for_candidate(
        self,
        candidate_id: str,
    ) -> tuple[TradingCandidateTag, ...]: ...

    def add(self, candidate_id: str, tag: TradingCandidateTag) -> bool: ...

    def remove(self, candidate_id: str, tag: TradingCandidateTag) -> bool: ...


class TradingCandidateTagLookup(Protocol):
    """Application-owned Candidate lookup required by tag workflows."""

    def find_by_id(self, candidate_id: str) -> TradingCandidate | None: ...


class TradingCandidateTagsState(StrEnum):
    """Explicit state of the selected Candidate's persistent tags."""

    UNAVAILABLE = "UNAVAILABLE"
    LOADING = "LOADING"
    EMPTY = "EMPTY"
    READY = "READY"
    ERROR = "ERROR"


@dataclass(frozen=True, slots=True)
class TradingCandidateTags:
    """Immutable Application snapshot displayed by the Decision Center."""

    state: TradingCandidateTagsState
    tags: tuple[TradingCandidateTag, ...]
    detail: str

    def __post_init__(self) -> None:
        if not isinstance(self.state, TradingCandidateTagsState):
            raise TypeError("state must be a TradingCandidateTagsState")
        if not isinstance(self.tags, tuple):
            raise TypeError("tags must be a tuple")
        if not all(isinstance(tag, TradingCandidateTag) for tag in self.tags):
            raise TypeError("tags must contain only TradingCandidateTag values")
        if not isinstance(self.detail, str) or not self.detail:
            raise ValueError("detail must be non-blank text")
        if self.state is TradingCandidateTagsState.READY and not self.tags:
            raise ValueError("READY Candidate Tags must contain tags")
        if self.state is not TradingCandidateTagsState.READY and self.tags:
            raise ValueError(f"{self.state} Candidate Tags must not contain tags")

    @classmethod
    def unavailable(cls, detail: str) -> TradingCandidateTags:
        return cls(TradingCandidateTagsState.UNAVAILABLE, (), detail)

    @classmethod
    def loading(cls) -> TradingCandidateTags:
        return cls(
            TradingCandidateTagsState.LOADING,
            (),
            "Loading Candidate Tags.",
        )

    @classmethod
    def from_tags(
        cls,
        tags: tuple[TradingCandidateTag, ...],
    ) -> TradingCandidateTags:
        if tags:
            return cls(
                TradingCandidateTagsState.READY,
                tags,
                f"{len(tags)} Candidate Tag(s) loaded.",
            )
        return cls(
            TradingCandidateTagsState.EMPTY,
            (),
            "No Candidate Tags are stored.",
        )

    @classmethod
    def error(cls, detail: str) -> TradingCandidateTags:
        return cls(TradingCandidateTagsState.ERROR, (), detail)


class TradingCandidateTagAddResult(StrEnum):
    """Deterministic outcome of one explicit Candidate Tag add request."""

    ADDED = "ADDED"
    ALREADY_EXISTS = "ALREADY EXISTS"
    CANDIDATE_NOT_FOUND = "CANDIDATE NOT FOUND"
    NOT_ALLOWED = "NOT ALLOWED"
    INVALID = "INVALID"
    ERROR = "ERROR"


@dataclass(frozen=True, slots=True)
class TradingCandidateTagAddOutcome:
    result: TradingCandidateTagAddResult
    tag: TradingCandidateTag | None
    detail: str


class TradingCandidateTagRemoveResult(StrEnum):
    """Deterministic outcome of one explicit Candidate Tag remove request."""

    REMOVED = "REMOVED"
    TAG_NOT_FOUND = "TAG NOT FOUND"
    CANDIDATE_NOT_FOUND = "CANDIDATE NOT FOUND"
    NOT_ALLOWED = "NOT ALLOWED"
    INVALID = "INVALID"
    ERROR = "ERROR"


@dataclass(frozen=True, slots=True)
class TradingCandidateTagRemoveOutcome:
    result: TradingCandidateTagRemoveResult
    tag: TradingCandidateTag | None
    detail: str


class TradingCandidateTagService:
    """Coordinate persistent Candidate Tag reads and explicit mutations."""

    _EDITABLE_STATUSES = frozenset(
        {
            TradingCandidateStatus.NEW,
            TradingCandidateStatus.REVIEWING,
        }
    )

    def __init__(
        self,
        candidate_repository: TradingCandidateTagLookup,
        tag_repository: TradingCandidateTagRepository,
    ) -> None:
        self._candidate_repository = candidate_repository
        self._tag_repository = tag_repository

    def load_tags(self, candidate_id: str) -> TradingCandidateTags:
        try:
            validated_id = CandidateId(candidate_id)
            candidate = self._candidate_repository.find_by_id(validated_id.value)
        except (TypeError, ValueError) as exc:
            return TradingCandidateTags.error(str(exc))
        except Exception as exc:
            return TradingCandidateTags.error(
                f"Candidate Tags could not be read: {type(exc).__name__}."
            )
        if candidate is None:
            return TradingCandidateTags.error("Trading Candidate no longer exists.")
        try:
            tags = tuple(
                sorted(
                    self._tag_repository.list_for_candidate(validated_id.value),
                    key=lambda tag: (tag.normalized_key, tag.value),
                )
            )
        except Exception as exc:
            return TradingCandidateTags.error(
                f"Candidate Tags could not be read: {type(exc).__name__}."
            )
        return TradingCandidateTags.from_tags(tags)

    def add_tag(
        self,
        candidate_id: str,
        value: str,
    ) -> TradingCandidateTagAddOutcome:
        try:
            validated_id = CandidateId(candidate_id)
            candidate = self._candidate_repository.find_by_id(validated_id.value)
        except (TypeError, ValueError) as exc:
            return TradingCandidateTagAddOutcome(
                TradingCandidateTagAddResult.INVALID,
                None,
                str(exc),
            )
        except Exception as exc:
            return self._add_error(exc)
        if candidate is None:
            return TradingCandidateTagAddOutcome(
                TradingCandidateTagAddResult.CANDIDATE_NOT_FOUND,
                None,
                "Trading Candidate no longer exists.",
            )
        if candidate.status not in self._EDITABLE_STATUSES:
            return TradingCandidateTagAddOutcome(
                TradingCandidateTagAddResult.NOT_ALLOWED,
                None,
                (
                    "Candidate Tags cannot be changed while status is "
                    f"{candidate.status.value}."
                ),
            )
        try:
            tag = TradingCandidateTag(value)
            added = self._tag_repository.add(validated_id.value, tag)
        except (TypeError, ValueError) as exc:
            return TradingCandidateTagAddOutcome(
                TradingCandidateTagAddResult.INVALID,
                None,
                str(exc),
            )
        except Exception as exc:
            return self._add_error(exc)
        if not added:
            return TradingCandidateTagAddOutcome(
                TradingCandidateTagAddResult.ALREADY_EXISTS,
                tag,
                f"Candidate Tag '{tag.value}' already exists.",
            )
        return TradingCandidateTagAddOutcome(
            TradingCandidateTagAddResult.ADDED,
            tag,
            f"Candidate Tag '{tag.value}' was added.",
        )

    def remove_tag(
        self,
        candidate_id: str,
        value: str,
    ) -> TradingCandidateTagRemoveOutcome:
        try:
            validated_id = CandidateId(candidate_id)
            candidate = self._candidate_repository.find_by_id(validated_id.value)
        except (TypeError, ValueError) as exc:
            return TradingCandidateTagRemoveOutcome(
                TradingCandidateTagRemoveResult.INVALID,
                None,
                str(exc),
            )
        except Exception as exc:
            return self._remove_error(exc)
        if candidate is None:
            return TradingCandidateTagRemoveOutcome(
                TradingCandidateTagRemoveResult.CANDIDATE_NOT_FOUND,
                None,
                "Trading Candidate no longer exists.",
            )
        if candidate.status not in self._EDITABLE_STATUSES:
            return TradingCandidateTagRemoveOutcome(
                TradingCandidateTagRemoveResult.NOT_ALLOWED,
                None,
                (
                    "Candidate Tags cannot be changed while status is "
                    f"{candidate.status.value}."
                ),
            )
        try:
            tag = TradingCandidateTag(value)
            removed = self._tag_repository.remove(validated_id.value, tag)
        except (TypeError, ValueError) as exc:
            return TradingCandidateTagRemoveOutcome(
                TradingCandidateTagRemoveResult.INVALID,
                None,
                str(exc),
            )
        except Exception as exc:
            return self._remove_error(exc)
        if not removed:
            return TradingCandidateTagRemoveOutcome(
                TradingCandidateTagRemoveResult.TAG_NOT_FOUND,
                tag,
                f"Candidate Tag '{tag.value}' no longer exists.",
            )
        return TradingCandidateTagRemoveOutcome(
            TradingCandidateTagRemoveResult.REMOVED,
            tag,
            f"Candidate Tag '{tag.value}' was removed.",
        )

    @staticmethod
    def _add_error(error: Exception) -> TradingCandidateTagAddOutcome:
        return TradingCandidateTagAddOutcome(
            TradingCandidateTagAddResult.ERROR,
            None,
            f"Candidate Tag could not be added: {type(error).__name__}.",
        )

    @staticmethod
    def _remove_error(error: Exception) -> TradingCandidateTagRemoveOutcome:
        return TradingCandidateTagRemoveOutcome(
            TradingCandidateTagRemoveResult.ERROR,
            None,
            f"Candidate Tag could not be removed: {type(error).__name__}.",
        )
