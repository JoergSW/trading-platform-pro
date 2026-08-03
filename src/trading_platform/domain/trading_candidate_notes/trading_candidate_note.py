from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from trading_platform.domain.trading_candidates.trading_candidate import CandidateId

MAX_TRADING_CANDIDATE_NOTE_LENGTH = 4000


@dataclass(frozen=True, slots=True)
class NoteId:
    value: str

    def __post_init__(self) -> None:
        _require_canonical_uuid(self.value, "note_id")


@dataclass(frozen=True, slots=True)
class TradingCandidateNote:
    note_id: NoteId
    candidate_id: CandidateId
    text: str
    created_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.note_id, NoteId):
            raise TypeError("note_id must be a NoteId")
        if not isinstance(self.candidate_id, CandidateId):
            raise TypeError("candidate_id must be a CandidateId")
        _require_normalized_text(self.text)
        _require_utc_datetime(self.created_at, "created_at")

    @classmethod
    def create(
        cls,
        *,
        note_id: str,
        candidate_id: str,
        text: str,
        created_at: datetime,
    ) -> TradingCandidateNote:
        return cls(
            NoteId(note_id),
            CandidateId(candidate_id),
            normalize_note_text(text),
            created_at,
        )


def normalize_note_text(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("text must be a string")
    normalized = value.strip()
    _require_normalized_text(normalized)
    return normalized


def _require_normalized_text(value: str) -> None:
    if not isinstance(value, str):
        raise TypeError("text must be a string")
    if not value or value != value.strip():
        raise ValueError("text must be non-blank normalized text")
    if len(value) > MAX_TRADING_CANDIDATE_NOTE_LENGTH:
        raise ValueError(
            f"text must not exceed {MAX_TRADING_CANDIDATE_NOTE_LENGTH} characters"
        )


def _require_canonical_uuid(value: str, field_name: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    try:
        parsed = UUID(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a valid UUID") from exc
    if str(parsed) != value:
        raise ValueError(f"{field_name} must use canonical lowercase UUID format")


def _require_utc_datetime(value: datetime, field_name: str) -> None:
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() != UTC.utcoffset(value):
        raise ValueError(f"{field_name} must use UTC")
