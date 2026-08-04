from __future__ import annotations

import sqlite3
from pathlib import Path

from trading_platform.application.trading_candidate_tags import (
    TradingCandidateTagRepository,
)
from trading_platform.domain.trading_candidate_tags import TradingCandidateTag
from trading_platform.domain.trading_candidates.trading_candidate import CandidateId

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS trading_candidate_tags (
    candidate_id TEXT NOT NULL,
    tag TEXT NOT NULL,
    normalized_key TEXT NOT NULL,
    PRIMARY KEY(candidate_id, normalized_key),
    FOREIGN KEY(candidate_id) REFERENCES trading_candidates(candidate_id)
)
"""


class SqliteTradingCandidateTagRepository(TradingCandidateTagRepository):
    """SQLite implementation of persistent Candidate Tags."""

    def __init__(self, database_path: Path, *, timeout_seconds: float = 5.0) -> None:
        if not isinstance(database_path, Path):
            raise TypeError("database_path must be a Path")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero")
        self._database_path = database_path
        self._timeout_seconds = timeout_seconds

    def list_for_candidate(
        self,
        candidate_id: str,
    ) -> tuple[TradingCandidateTag, ...]:
        validated_id = CandidateId(candidate_id)
        with self._connect() as connection:
            self._initialize_schema(connection)
            rows = connection.execute(
                """
                SELECT tag
                FROM trading_candidate_tags
                WHERE candidate_id = ?
                ORDER BY normalized_key ASC, tag ASC
                """,
                (validated_id.value,),
            ).fetchall()
        return tuple(TradingCandidateTag(row["tag"]) for row in rows)

    def add(self, candidate_id: str, tag: TradingCandidateTag) -> bool:
        validated_id = CandidateId(candidate_id)
        if not isinstance(tag, TradingCandidateTag):
            raise TypeError("tag must be a TradingCandidateTag")
        with self._connect() as connection:
            self._initialize_schema(connection)
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO trading_candidate_tags(
                    candidate_id, tag, normalized_key
                )
                VALUES (?, ?, ?)
                """,
                (validated_id.value, tag.value, tag.normalized_key),
            )
        return cursor.rowcount == 1

    def remove(self, candidate_id: str, tag: TradingCandidateTag) -> bool:
        validated_id = CandidateId(candidate_id)
        if not isinstance(tag, TradingCandidateTag):
            raise TypeError("tag must be a TradingCandidateTag")
        with self._connect() as connection:
            self._initialize_schema(connection)
            cursor = connection.execute(
                """
                DELETE FROM trading_candidate_tags
                WHERE candidate_id = ? AND normalized_key = ?
                """,
                (validated_id.value, tag.normalized_key),
            )
        return cursor.rowcount == 1

    def _connect(self) -> sqlite3.Connection:
        parent = self._database_path.parent
        if not parent.exists():
            raise FileNotFoundError(
                "Candidate Tags database parent directory does not exist."
            )
        if not parent.is_dir():
            raise NotADirectoryError(
                "Candidate Tags database parent path is not a directory."
            )
        if self._database_path.exists() and not self._database_path.is_file():
            raise IsADirectoryError(
                "Candidate Tags database path does not reference a file."
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
