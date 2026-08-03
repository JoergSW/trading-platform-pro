from datetime import UTC, datetime

from trading_platform.application.trading_candidate_notes import (
    TradingCandidateNoteAddResult,
    TradingCandidateNoteService,
    TradingCandidateNotesState,
)
from trading_platform.domain.trading_candidates.trading_candidate import (
    CandidateId,
    TradingCandidate,
    TradingCandidateOrigin,
    TradingCandidateStatus,
)


class Repository:
    def __init__(self, candidate: TradingCandidate) -> None:
        self.candidate = candidate
        self.notes = []

    def find_by_id(self, candidate_id: str) -> TradingCandidate | None:
        return (
            self.candidate
            if self.candidate.candidate_id.value == candidate_id
            else None
        )

    def list_for_candidate(self, candidate_id: str):
        return tuple(self.notes)

    def add(self, note) -> None:
        self.notes.append(note)


class Clock:
    def now_utc(self) -> datetime:
        return datetime(2026, 8, 3, 9, 30, tzinfo=UTC)


class IdGenerator:
    def new_id(self) -> str:
        return "00000000-0000-4000-8000-000000000010"


def _candidate(status: TradingCandidateStatus) -> TradingCandidate:
    return TradingCandidate(
        candidate_id=CandidateId("00000000-0000-4000-8000-000000000001"),
        symbol="AAPL",
        origin=TradingCandidateOrigin.SCANNER,
        status=status,
        created_at=datetime(2026, 8, 3, 9, 0, tzinfo=UTC),
        updated_at=datetime(2026, 8, 3, 9, 0, tzinfo=UTC),
    )


def test_add_and_reload_candidate_note() -> None:
    repository = Repository(_candidate(TradingCandidateStatus.NEW))
    service = TradingCandidateNoteService(
        repository, repository, Clock(), IdGenerator()
    )

    outcome = service.add_note(repository.candidate.candidate_id.value, "Evidence")
    loaded = service.load_notes(repository.candidate.candidate_id.value)

    assert outcome.result is TradingCandidateNoteAddResult.ADDED
    assert loaded.state is TradingCandidateNotesState.READY
    assert loaded.notes[0].text == "Evidence"


def test_add_note_is_blocked_for_closed_candidate() -> None:
    repository = Repository(_candidate(TradingCandidateStatus.ARCHIVED))
    service = TradingCandidateNoteService(
        repository, repository, Clock(), IdGenerator()
    )

    outcome = service.add_note(repository.candidate.candidate_id.value, "Evidence")

    assert outcome.result is TradingCandidateNoteAddResult.NOT_ALLOWED
    assert repository.notes == []
