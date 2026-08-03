from datetime import UTC, datetime, timedelta

from trading_platform.domain.trading_candidate_notes.trading_candidate_note import (
    TradingCandidateNote,
)
from trading_platform.domain.trading_candidates.trading_candidate import (
    TradingCandidate,
    TradingCandidateOrigin,
)
from trading_platform.infrastructure.trading_candidate_notes.sqlite_repository import (
    SqliteTradingCandidateNoteRepository,
)
from trading_platform.infrastructure.trading_candidates.sqlite_repository import (
    SqliteTradingCandidateRepository,
)


def test_sqlite_candidate_notes_are_persistent_and_newest_first(tmp_path) -> None:
    database_path = tmp_path / "candidates.db"
    candidate_repository = SqliteTradingCandidateRepository(database_path)
    note_repository = SqliteTradingCandidateNoteRepository(database_path)
    observed_at = datetime(2026, 8, 3, 9, 0, tzinfo=UTC)
    candidate = TradingCandidate.create_new(
        candidate_id="00000000-0000-4000-8000-000000000001",
        symbol="AAPL",
        origin=TradingCandidateOrigin.SCANNER,
        observed_at=observed_at,
    )
    candidate_repository.add(candidate)
    older = TradingCandidateNote.create(
        note_id="00000000-0000-4000-8000-000000000010",
        candidate_id=candidate.candidate_id.value,
        text="Older",
        created_at=observed_at,
    )
    newer = TradingCandidateNote.create(
        note_id="00000000-0000-4000-8000-000000000011",
        candidate_id=candidate.candidate_id.value,
        text="Newer",
        created_at=observed_at + timedelta(minutes=1),
    )

    note_repository.add(older)
    note_repository.add(newer)

    loaded = note_repository.list_for_candidate(candidate.candidate_id.value)

    assert [note.text for note in loaded] == ["Newer", "Older"]
