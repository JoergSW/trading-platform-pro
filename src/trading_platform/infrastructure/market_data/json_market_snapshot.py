from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from trading_platform.application.market_data.market_snapshot import (
    MarketSnapshot,
    MarketSnapshotState,
)

_STATE_FIELD = "state"
_SOURCE_FIELD = "source_name"
_STATUS_FIELD = "market_status"
_OBSERVED_AT_FIELD = "observed_at"

_STATE_FIELDS = {
    MarketSnapshotState.READY: frozenset(
        {_STATE_FIELD, _SOURCE_FIELD, _STATUS_FIELD, _OBSERVED_AT_FIELD}
    ),
    MarketSnapshotState.NO_DATA: frozenset({_STATE_FIELD, _SOURCE_FIELD}),
    MarketSnapshotState.UNAVAILABLE: frozenset({_STATE_FIELD, _SOURCE_FIELD}),
}


class JsonMarketSnapshotProvider:
    """Load one validated read-only market snapshot from an explicit JSON file."""

    def __init__(self, snapshot_path: Path) -> None:
        self._snapshot_path = snapshot_path

    @property
    def snapshot_path(self) -> Path:
        return self._snapshot_path

    def load_snapshot(self) -> MarketSnapshot:
        if not self._snapshot_path.is_file():
            return self._unavailable(
                f"Configured JSON market snapshot file was not found: "
                f"{self._snapshot_path}"
            )

        try:
            payload = json.loads(self._snapshot_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError) as exc:
            return self._unavailable(
                "Configured JSON market snapshot file could not be read: "
                f"{type(exc).__name__}."
            )
        except JSONDecodeError:
            return self._unavailable(
                "Configured JSON market snapshot file contains invalid JSON."
            )

        try:
            return _snapshot_from_payload(payload)
        except (TypeError, ValueError) as exc:
            return self._unavailable(
                f"Configured JSON market snapshot failed validation: {exc}"
            )

    def _unavailable(self, detail: str) -> MarketSnapshot:
        return MarketSnapshot.unavailable(
            source_name=f"JSON file: {self._snapshot_path}",
            detail=detail,
        )


def _snapshot_from_payload(payload: Any) -> MarketSnapshot:
    if not isinstance(payload, dict):
        raise TypeError("top-level JSON value must be an object")

    state = _read_state(payload)
    _validate_exact_fields(payload, _STATE_FIELDS[state])
    source_name = _read_text(payload, _SOURCE_FIELD)

    if state is MarketSnapshotState.READY:
        return MarketSnapshot.ready(
            market_status=_read_text(payload, _STATUS_FIELD),
            source_name=source_name,
            observed_at=_read_utc_datetime(payload, _OBSERVED_AT_FIELD),
        )

    if state is MarketSnapshotState.NO_DATA:
        return MarketSnapshot.no_data(source_name)

    return MarketSnapshot.unavailable(
        source_name=source_name,
        detail="The configured JSON source reports market data as unavailable.",
    )


def _read_state(payload: dict[str, Any]) -> MarketSnapshotState:
    value = payload.get(_STATE_FIELD)
    if not isinstance(value, str):
        raise TypeError("state must be a string")

    try:
        return MarketSnapshotState(value)
    except ValueError as exc:
        allowed = ", ".join(state.value for state in MarketSnapshotState)
        raise ValueError(f"state must be one of: {allowed}") from exc


def _validate_exact_fields(
    payload: dict[str, Any],
    expected_fields: frozenset[str],
) -> None:
    actual_fields = set(payload)
    missing_fields = sorted(expected_fields - actual_fields)
    unexpected_fields = sorted(actual_fields - expected_fields)

    if missing_fields:
        raise ValueError(f"missing required fields: {', '.join(missing_fields)}")
    if unexpected_fields:
        raise ValueError(f"unexpected fields: {', '.join(unexpected_fields)}")


def _read_text(payload: dict[str, Any], field_name: str) -> str:
    value = payload[field_name]
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must not be blank")
    return value


def _read_utc_datetime(payload: dict[str, Any], field_name: str) -> datetime:
    value = _read_text(payload, field_name)
    normalized_value = f"{value[:-1]}+00:00" if value.endswith("Z") else value

    try:
        observed_at = datetime.fromisoformat(normalized_value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO 8601 UTC timestamp") from exc

    if observed_at.tzinfo is None or observed_at.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if observed_at.utcoffset() != timedelta(0):
        raise ValueError(f"{field_name} must use UTC")

    return observed_at.astimezone(UTC)
