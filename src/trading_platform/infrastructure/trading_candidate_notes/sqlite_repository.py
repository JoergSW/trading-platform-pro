from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from trading_platform.application.trading_candidate_notes import (
    TradingCandidateNoteRepository,
)
from trading_platform.domain.trading_candidate_notes.trading_candidate_note import (
    NoteId,
    TradingCandidateNote,
)
from trading_platform.domain.trading_candidates.trading_candidate import CandidateId

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS trading_candidate_notes (
    note_id TEXT PRIMARY KEY,
    candidate_id TEXT NOT NULL,
    text TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(candidate_id) REFERENCES trading_candidates(candidate_id)
)
"""


class SqliteTradingCandidateNoteRepository(TradingCandidateNoteRepository):
    def __init__(self, database_path: Path, *, timeout_seconds: float = 5.0) -> None:
        self._database_path = Path(database_path)
        self._timeout_seconds = timeout_seconds

    def list_for_candidate(
        self,
        candidate_id: str,
    ) -> tuple[TradingCandidateNote, ...]:
        CandidateId(candidate_id)
        with self._connect() as connection:
            self._initialize_schema(connection)
            rows = connection.execute(
                """
                SELECT note_id, candidate_id, text, created_at
                FROM trading_candidate_notes
                WHERE candidate_id = ?
                ORDER BY created_at DESC, note_id ASC
                """,
                (candidate_id,),
            ).fetchall()
        return tuple(self._from_row(row) for row in rows)

    def add(self, note: TradingCandidateNote) -> None:
        if not isinstance(note, TradingCandidateNote):
            raise TypeError("note must be a TradingCandidateNote")
        with self._connect() as connection:
            self._initialize_schema(connection)
            connection.execute(
                """
                INSERT INTO trading_candidate_notes(
                    note_id, candidate_id, text, created_at
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    note.note_id.value,
                    note.candidate_id.value,
                    note.text,
                    _serialize_datetime(note.created_at),
                ),
            )

    def _connect(self) -> sqlite3.Connection:
        parent = self._database_path.parent
        if not parent.exists():
            raise FileNotFoundError(
                "Candidate Notes database parent directory does not exist."
            )
        connection = sqlite3.connect(
            self._database_path,
            timeout=self._timeout_seconds,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @staticmethod
    def _initialize_schema(connection: sqlite3.Connection) -> None:
        connection.execute(_CREATE_TABLE_SQL)

    @staticmethod
    def _from_row(row: sqlite3.Row) -> TradingCandidateNote:
        return TradingCandidateNote(
            note_id=NoteId(row["note_id"]),
            candidate_id=CandidateId(row["candidate_id"]),
            text=row["text"],
            created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")),
        )


def _serialize_datetime(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")
