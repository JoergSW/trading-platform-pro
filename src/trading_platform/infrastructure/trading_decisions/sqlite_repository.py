from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from trading_platform.application.trading_decisions.trading_decisions import (
    TradingDecisionAlreadyExistsError,
)
from trading_platform.domain.trading_candidates.trading_candidate import CandidateId
from trading_platform.domain.trading_decisions.trading_decision import (
    DecisionId,
    TradingDecision,
    TradingDecisionStatus,
)

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS trading_decisions (
    decision_id TEXT PRIMARY KEY,
    candidate_id TEXT NOT NULL UNIQUE,
    symbol TEXT NOT NULL,
    status TEXT NOT NULL,
    rationale TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (candidate_id) REFERENCES trading_candidates(candidate_id)
)
"""


class SqliteTradingDecisionRepository:
    """SQLite implementation of the Trading Decision persistence port."""

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

    def find_by_candidate_id(self, candidate_id: str) -> TradingDecision | None:
        validated_id = CandidateId(candidate_id)
        with self._connect() as connection:
            self._initialize_schema(connection)
            row = connection.execute(
                """
                SELECT decision_id, candidate_id, symbol, status, rationale,
                       created_at, updated_at
                FROM trading_decisions
                WHERE candidate_id = ?
                """,
                (validated_id.value,),
            ).fetchone()
        if row is None:
            return None
        return self._decision_from_row(row)

    def add(self, decision: TradingDecision) -> None:
        if not isinstance(decision, TradingDecision):
            raise TypeError("decision must be a TradingDecision")
        try:
            with self._connect() as connection:
                self._initialize_schema(connection)
                connection.execute(
                    """
                    INSERT INTO trading_decisions (
                        decision_id,
                        candidate_id,
                        symbol,
                        status,
                        rationale,
                        created_at,
                        updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        decision.decision_id.value,
                        decision.candidate_id.value,
                        decision.symbol,
                        decision.status.value,
                        decision.rationale,
                        _serialize_datetime(decision.created_at),
                        _serialize_datetime(decision.updated_at),
                    ),
                )
        except sqlite3.IntegrityError as exc:
            raise TradingDecisionAlreadyExistsError(
                "A Trading Decision already exists for this candidate."
            ) from exc

    def _connect(self) -> sqlite3.Connection:
        parent = self._database_path.parent
        if not parent.exists():
            raise FileNotFoundError(
                "Trading Decision database parent directory does not exist."
            )
        if not parent.is_dir():
            raise NotADirectoryError(
                "Trading Decision database parent path is not a directory."
            )
        if self._database_path.exists() and not self._database_path.is_file():
            raise IsADirectoryError(
                "Trading Decision database path does not reference a file."
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
    def _decision_from_row(row: sqlite3.Row) -> TradingDecision:
        return TradingDecision(
            decision_id=DecisionId(row["decision_id"]),
            candidate_id=CandidateId(row["candidate_id"]),
            symbol=row["symbol"],
            status=TradingDecisionStatus(row["status"]),
            rationale=row["rationale"],
            created_at=_deserialize_datetime(row["created_at"]),
            updated_at=_deserialize_datetime(row["updated_at"]),
        )


def _serialize_datetime(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _deserialize_datetime(value: str) -> datetime:
    if not isinstance(value, str):
        raise TypeError("stored Trading Decision timestamp must be text")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
