from datetime import UTC, datetime

import pytest

from trading_platform.domain.trading_candidate_notes.trading_candidate_note import (
    MAX_TRADING_CANDIDATE_NOTE_LENGTH,
    TradingCandidateNote,
)


def test_candidate_note_normalizes_text() -> None:
    note = TradingCandidateNote.create(
        note_id="00000000-0000-4000-8000-000000000001",
        candidate_id="00000000-0000-4000-8000-000000000002",
        text="  Evidence confirmed.  ",
        created_at=datetime(2026, 8, 3, 9, 0, tzinfo=UTC),
    )

    assert note.text == "Evidence confirmed."


@pytest.mark.parametrize(
    "text",
    ["", "   ", "x" * (MAX_TRADING_CANDIDATE_NOTE_LENGTH + 1)],
)
def test_candidate_note_rejects_invalid_text(text: str) -> None:
    with pytest.raises(ValueError):
        TradingCandidateNote.create(
            note_id="00000000-0000-4000-8000-000000000001",
            candidate_id="00000000-0000-4000-8000-000000000002",
            text=text,
            created_at=datetime(2026, 8, 3, 9, 0, tzinfo=UTC),
        )
