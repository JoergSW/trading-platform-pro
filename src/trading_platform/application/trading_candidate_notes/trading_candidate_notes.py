from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol

from trading_platform.domain.trading_candidate_notes.trading_candidate_note import (
    TradingCandidateNote,
)
from trading_platform.domain.trading_candidates.trading_candidate import (
    CandidateId,
    TradingCandidate,
    TradingCandidateStatus,
)


class TradingCandidateNoteRepository(Protocol):
    def list_for_candidate(
        self,
        candidate_id: str,
    ) -> tuple[TradingCandidateNote, ...]: ...

    def add(self, note: TradingCandidateNote) -> None: ...


class TradingCandidateLookup(Protocol):
    def find_by_id(self, candidate_id: str) -> TradingCandidate | None: ...


class TradingCandidateNoteClock(Protocol):
    def now_utc(self) -> datetime: ...


class TradingCandidateNoteIdGenerator(Protocol):
    def new_id(self) -> str: ...


class TradingCandidateNotesState(StrEnum):
    UNAVAILABLE = "UNAVAILABLE"
    LOADING = "LOADING"
    EMPTY = "EMPTY"
    READY = "READY"
    ERROR = "ERROR"


@dataclass(frozen=True, slots=True)
class TradingCandidateNotes:
    state: TradingCandidateNotesState
    notes: tuple[TradingCandidateNote, ...]
    detail: str

    @classmethod
    def unavailable(cls, detail: str) -> TradingCandidateNotes:
        return cls(TradingCandidateNotesState.UNAVAILABLE, (), detail)

    @classmethod
    def loading(cls) -> TradingCandidateNotes:
        return cls(TradingCandidateNotesState.LOADING, (), "Loading Candidate Notes.")

    @classmethod
    def from_notes(
        cls,
        notes: tuple[TradingCandidateNote, ...],
    ) -> TradingCandidateNotes:
        if notes:
            return cls(
                TradingCandidateNotesState.READY,
                notes,
                f"{len(notes)} Candidate Note(s) loaded.",
            )
        return cls(
            TradingCandidateNotesState.EMPTY,
            (),
            "No Candidate Notes are stored.",
        )

    @classmethod
    def error(cls, detail: str) -> TradingCandidateNotes:
        return cls(TradingCandidateNotesState.ERROR, (), detail)


class TradingCandidateNoteAddResult(StrEnum):
    ADDED = "ADDED"
    NOT_FOUND = "NOT FOUND"
    NOT_ALLOWED = "NOT ALLOWED"
    INVALID = "INVALID"
    ERROR = "ERROR"


@dataclass(frozen=True, slots=True)
class TradingCandidateNoteAddOutcome:
    result: TradingCandidateNoteAddResult
    note: TradingCandidateNote | None
    detail: str


class TradingCandidateNoteService:
    def __init__(
        self,
        candidate_repository: TradingCandidateLookup,
        note_repository: TradingCandidateNoteRepository,
        clock: TradingCandidateNoteClock,
        id_generator: TradingCandidateNoteIdGenerator,
    ) -> None:
        self._candidate_repository = candidate_repository
        self._note_repository = note_repository
        self._clock = clock
        self._id_generator = id_generator

    def load_notes(self, candidate_id: str) -> TradingCandidateNotes:
        try:
            validated_id = CandidateId(candidate_id)
            candidate = self._candidate_repository.find_by_id(validated_id.value)
            if candidate is None:
                return TradingCandidateNotes.error(
                    "Trading Candidate no longer exists."
                )
            return TradingCandidateNotes.from_notes(
                self._note_repository.list_for_candidate(validated_id.value)
            )
        except Exception as exc:
            return TradingCandidateNotes.error(
                f"Candidate Notes could not be read: {type(exc).__name__}."
            )

    def add_note(
        self,
        candidate_id: str,
        text: str,
    ) -> TradingCandidateNoteAddOutcome:
        try:
            validated_id = CandidateId(candidate_id)
            candidate = self._candidate_repository.find_by_id(validated_id.value)
        except (TypeError, ValueError) as exc:
            return TradingCandidateNoteAddOutcome(
                TradingCandidateNoteAddResult.INVALID,
                None,
                str(exc),
            )
        except Exception as exc:
            return self._error(exc)
        if candidate is None:
            return TradingCandidateNoteAddOutcome(
                TradingCandidateNoteAddResult.NOT_FOUND,
                None,
                "Trading Candidate no longer exists.",
            )
        if candidate.status not in {
            TradingCandidateStatus.NEW,
            TradingCandidateStatus.REVIEWING,
        }:
            return TradingCandidateNoteAddOutcome(
                TradingCandidateNoteAddResult.NOT_ALLOWED,
                None,
                (
                    "Candidate Notes cannot be added while status is "
                    f"{candidate.status.value}."
                ),
            )
        try:
            note = TradingCandidateNote.create(
                note_id=self._id_generator.new_id(),
                candidate_id=validated_id.value,
                text=text,
                created_at=self._clock.now_utc(),
            )
            self._note_repository.add(note)
        except (TypeError, ValueError) as exc:
            return TradingCandidateNoteAddOutcome(
                TradingCandidateNoteAddResult.INVALID,
                None,
                str(exc),
            )
        except Exception as exc:
            return self._error(exc)
        return TradingCandidateNoteAddOutcome(
            TradingCandidateNoteAddResult.ADDED,
            note,
            "Candidate Note was added.",
        )

    @staticmethod
    def _error(error: Exception) -> TradingCandidateNoteAddOutcome:
        return TradingCandidateNoteAddOutcome(
            TradingCandidateNoteAddResult.ERROR,
            None,
            f"Candidate Note could not be added: {type(error).__name__}.",
        )
