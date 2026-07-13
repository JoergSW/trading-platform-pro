from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from trading_platform.application.market_data.market_snapshot import (
    MarketSnapshot,
    MarketSnapshotMetrics,
    MarketSnapshotState,
)

_STATE_FIELD = "state"
_SOURCE_FIELD = "source_name"
_STATUS_FIELD = "market_status"
_OBSERVED_AT_FIELD = "observed_at"
_METRICS_FIELD = "metrics"
_SPX_FIELD = "spx_index_points"
_VIX_FIELD = "vix_index_points"
_ATM_STRADDLE_FIELD = "atm_straddle_percent"

_REQUIRED_STATE_FIELDS = {
    MarketSnapshotState.READY: frozenset(
        {_STATE_FIELD, _SOURCE_FIELD, _STATUS_FIELD, _OBSERVED_AT_FIELD}
    ),
    MarketSnapshotState.NO_DATA: frozenset({_STATE_FIELD, _SOURCE_FIELD}),
    MarketSnapshotState.UNAVAILABLE: frozenset({_STATE_FIELD, _SOURCE_FIELD}),
}
_OPTIONAL_STATE_FIELDS = {
    MarketSnapshotState.READY: frozenset({_METRICS_FIELD}),
    MarketSnapshotState.NO_DATA: frozenset(),
    MarketSnapshotState.UNAVAILABLE: frozenset(),
}
_METRIC_FIELDS = frozenset({_SPX_FIELD, _VIX_FIELD, _ATM_STRADDLE_FIELD})


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
    _validate_fields(
        payload,
        _REQUIRED_STATE_FIELDS[state],
        _OPTIONAL_STATE_FIELDS[state],
    )
    source_name = _read_text(payload, _SOURCE_FIELD)

    if state is MarketSnapshotState.READY:
        return MarketSnapshot.ready(
            market_status=_read_text(payload, _STATUS_FIELD),
            source_name=source_name,
            observed_at=_read_utc_datetime(payload, _OBSERVED_AT_FIELD),
            metrics=_read_metrics(payload),
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


def _validate_fields(
    payload: dict[str, Any],
    required_fields: frozenset[str],
    optional_fields: frozenset[str],
) -> None:
    actual_fields = set(payload)
    missing_fields = sorted(required_fields - actual_fields)
    unexpected_fields = sorted(
        actual_fields - required_fields - optional_fields,
    )

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


def _read_metrics(payload: dict[str, Any]) -> MarketSnapshotMetrics:
    if _METRICS_FIELD not in payload:
        return MarketSnapshotMetrics()

    metrics_payload = payload[_METRICS_FIELD]
    if not isinstance(metrics_payload, dict):
        raise TypeError("metrics must be an object")

    unexpected_fields = sorted(set(metrics_payload) - _METRIC_FIELDS)
    if unexpected_fields:
        raise ValueError(f"unexpected metrics fields: {', '.join(unexpected_fields)}")

    return MarketSnapshotMetrics(
        spx_index_points=_read_optional_decimal(
            metrics_payload,
            _SPX_FIELD,
        ),
        vix_index_points=_read_optional_decimal(
            metrics_payload,
            _VIX_FIELD,
        ),
        atm_straddle_percent=_read_optional_decimal(
            metrics_payload,
            _ATM_STRADDLE_FIELD,
        ),
    )


def _read_optional_decimal(
    payload: dict[str, Any],
    field_name: str,
) -> Decimal | None:
    if field_name not in payload:
        return None

    value = payload[field_name]
    qualified_name = f"metrics.{field_name}"
    if not isinstance(value, str):
        raise TypeError(f"{qualified_name} must be a decimal string")
    if not value or value != value.strip():
        raise ValueError(f"{qualified_name} must be a normalized decimal string")

    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{qualified_name} must be a valid decimal string") from exc
