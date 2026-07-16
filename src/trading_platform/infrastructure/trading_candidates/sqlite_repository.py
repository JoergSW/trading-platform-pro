from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from trading_platform.application.trading_candidates.trading_candidates import (
    TradingCandidateAlreadyExistsError,
    TradingCandidateConcurrentUpdateError,
    TradingCandidateNotFoundError,
)
from trading_platform.domain.instruments.instrument_symbol import (
    validate_instrument_symbol,
)
from trading_platform.domain.trading_candidates.trading_candidate import (
    CandidateId,
    TradingCandidate,
    TradingCandidateOrigin,
    TradingCandidateStatus,
)

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS trading_candidates (
    candidate_id TEXT PRIMARY KEY,
    symbol TEXT NOT NULL UNIQUE,
    origin TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""


class SqliteTradingCandidateRepository:
    """SQLite implementation of the Trading Candidate persistence port."""

    def __init__(self, database_path: Path, *, timeout_seconds: float = 1.0) -> None:
        if not isinstance(database_path, Path):
            raise TypeError("database_path must be a Path")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero")
        self._database_path = database_path
        self._timeout_seconds = timeout_seconds

    @property
    def database_path(self) -> Path:
        return self._database_path

    def list_candidates(self) -> tuple[TradingCandidate, ...]:
        with self._connect() as connection:
            self._initialize_schema(connection)
            rows = connection.execute(
                """
                SELECT candidate_id, symbol, origin, status, created_at, updated_at
                FROM trading_candidates
                ORDER BY created_at ASC, candidate_id ASC
                """
            ).fetchall()
        return tuple(self._candidate_from_row(row) for row in rows)

    def find_by_symbol(self, symbol: str) -> TradingCandidate | None:
        validated_symbol = validate_instrument_symbol(symbol)
        with self._connect() as connection:
            self._initialize_schema(connection)
            row = connection.execute(
                """
                SELECT candidate_id, symbol, origin, status, created_at, updated_at
                FROM trading_candidates
                WHERE symbol = ?
                """,
                (validated_symbol,),
            ).fetchone()
        if row is None:
            return None
        return self._candidate_from_row(row)

    def find_by_id(self, candidate_id: str) -> TradingCandidate | None:
        validated_id = CandidateId(candidate_id)
        with self._connect() as connection:
            self._initialize_schema(connection)
            row = connection.execute(
                """
                SELECT candidate_id, symbol, origin, status, created_at, updated_at
                FROM trading_candidates
                WHERE candidate_id = ?
                """,
                (validated_id.value,),
            ).fetchone()
        if row is None:
            return None
        return self._candidate_from_row(row)

    def add(self, candidate: TradingCandidate) -> None:
        if not isinstance(candidate, TradingCandidate):
            raise TypeError("candidate must be a TradingCandidate")
        try:
            with self._connect() as connection:
                self._initialize_schema(connection)
                connection.execute(
                    """
                    INSERT INTO trading_candidates (
                        candidate_id,
                        symbol,
                        origin,
                        status,
                        created_at,
                        updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        candidate.candidate_id.value,
                        candidate.symbol,
                        candidate.origin.value,
                        candidate.status.value,
                        _serialize_datetime(candidate.created_at),
                        _serialize_datetime(candidate.updated_at),
                    ),
                )
        except sqlite3.IntegrityError as exc:
            raise TradingCandidateAlreadyExistsError(
                f"Trading Candidate for {candidate.symbol} already exists."
            ) from exc

    def update_status(
        self,
        candidate: TradingCandidate,
        *,
        expected_status: TradingCandidateStatus,
    ) -> None:
        if not isinstance(candidate, TradingCandidate):
            raise TypeError("candidate must be a TradingCandidate")
        if not isinstance(expected_status, TradingCandidateStatus):
            raise TypeError("expected_status must be a TradingCandidateStatus")

        with self._connect() as connection:
            self._initialize_schema(connection)
            cursor = connection.execute(
                """
                UPDATE trading_candidates
                SET status = ?, updated_at = ?
                WHERE candidate_id = ? AND status = ?
                """,
                (
                    candidate.status.value,
                    _serialize_datetime(candidate.updated_at),
                    candidate.candidate_id.value,
                    expected_status.value,
                ),
            )
            if cursor.rowcount == 1:
                return
            exists = connection.execute(
                """
                SELECT 1
                FROM trading_candidates
                WHERE candidate_id = ?
                """,
                (candidate.candidate_id.value,),
            ).fetchone()

        if exists is None:
            raise TradingCandidateNotFoundError(
                f"Trading Candidate {candidate.candidate_id.value} does not exist."
            )
        raise TradingCandidateConcurrentUpdateError(
            f"Trading Candidate {candidate.candidate_id.value} changed concurrently."
        )

    def _connect(self) -> sqlite3.Connection:
        parent = self._database_path.parent
        if not parent.exists():
            raise FileNotFoundError(
                "Trading Candidate database parent directory does not exist."
            )
        if not parent.is_dir():
            raise NotADirectoryError(
                "Trading Candidate database parent path is not a directory."
            )
        if self._database_path.exists() and not self._database_path.is_file():
            raise IsADirectoryError(
                "Trading Candidate database path does not reference a file."
            )

        connection = sqlite3.connect(
            self._database_path,
            timeout=self._timeout_seconds,
        )
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _initialize_schema(connection: sqlite3.Connection) -> None:
        connection.execute(_CREATE_TABLE_SQL)

    @staticmethod
    def _candidate_from_row(row: sqlite3.Row) -> TradingCandidate:
        return TradingCandidate(
            candidate_id=CandidateId(row["candidate_id"]),
            symbol=row["symbol"],
            origin=TradingCandidateOrigin(row["origin"]),
            status=TradingCandidateStatus(row["status"]),
            created_at=_deserialize_datetime(row["created_at"]),
            updated_at=_deserialize_datetime(row["updated_at"]),
        )


def _serialize_datetime(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _deserialize_datetime(value: str) -> datetime:
    if not isinstance(value, str):
        raise TypeError("stored Trading Candidate timestamp must be text")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
