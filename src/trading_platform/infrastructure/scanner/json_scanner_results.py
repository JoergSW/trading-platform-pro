from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from trading_platform.application.scanner.scanner_results import (
    ScannerResult,
    ScannerResults,
    ScannerResultsState,
)

_STATE_FIELD = "state"
_SOURCE_FIELD = "source_name"
_RESULTS_FIELD = "results"
_SYMBOL_FIELD = "symbol"
_SIGNAL_FIELD = "signal"
_SCORE_FIELD = "score"
_OBSERVED_AT_FIELD = "observed_at"

_REQUIRED_STATE_FIELDS = {
    ScannerResultsState.READY: frozenset({_STATE_FIELD, _SOURCE_FIELD, _RESULTS_FIELD}),
    ScannerResultsState.NO_DATA: frozenset({_STATE_FIELD, _SOURCE_FIELD}),
    ScannerResultsState.UNAVAILABLE: frozenset({_STATE_FIELD, _SOURCE_FIELD}),
}
_RESULT_FIELDS = frozenset(
    {_SYMBOL_FIELD, _SIGNAL_FIELD, _SCORE_FIELD, _OBSERVED_AT_FIELD}
)


class JsonScannerResultsProvider:
    """Load validated read-only scanner results from an explicit JSON file."""

    def __init__(self, results_path: Path) -> None:
        self._results_path = results_path

    @property
    def results_path(self) -> Path:
        return self._results_path

    def load_results(self) -> ScannerResults:
        if not self._results_path.is_file():
            return self._unavailable(
                f"Configured JSON scanner results file was not found: "
                f"{self._results_path}"
            )

        try:
            payload = json.loads(self._results_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError) as exc:
            return self._unavailable(
                "Configured JSON scanner results file could not be read: "
                f"{type(exc).__name__}."
            )
        except JSONDecodeError:
            return self._unavailable(
                "Configured JSON scanner results file contains invalid JSON."
            )

        try:
            return _results_from_payload(payload)
        except (TypeError, ValueError) as exc:
            return self._unavailable(
                f"Configured JSON scanner results failed validation: {exc}"
            )

    def _unavailable(self, detail: str) -> ScannerResults:
        return ScannerResults.unavailable(
            source_name=f"JSON file: {self._results_path}",
            detail=detail,
        )


def _results_from_payload(payload: Any) -> ScannerResults:
    if not isinstance(payload, dict):
        raise TypeError("top-level JSON value must be an object")

    state = _read_state(payload)
    _validate_exact_fields(payload, _REQUIRED_STATE_FIELDS[state])
    source_name = _read_text(payload, _SOURCE_FIELD, max_length=200)

    if state is ScannerResultsState.READY:
        raw_results = payload[_RESULTS_FIELD]
        if not isinstance(raw_results, list):
            raise TypeError("results must be an array")
        if not raw_results:
            raise ValueError("READY results must contain at least one item")
        return ScannerResults.ready(
            source_name=source_name,
            results=tuple(
                _read_result(item, index) for index, item in enumerate(raw_results)
            ),
        )

    if state is ScannerResultsState.NO_DATA:
        return ScannerResults.no_data(source_name)

    return ScannerResults.unavailable(
        source_name=source_name,
        detail="The configured JSON source reports scanner results as unavailable.",
    )


def _read_state(payload: dict[str, Any]) -> ScannerResultsState:
    value = payload.get(_STATE_FIELD)
    if not isinstance(value, str):
        raise TypeError("state must be a string")

    try:
        return ScannerResultsState(value)
    except ValueError as exc:
        allowed = ", ".join(state.value for state in ScannerResultsState)
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


def _read_result(payload: Any, index: int) -> ScannerResult:
    field_prefix = f"results[{index}]"
    if not isinstance(payload, dict):
        raise TypeError(f"{field_prefix} must be an object")
    _validate_result_fields(payload, field_prefix)

    return ScannerResult(
        symbol=_read_text(payload, _SYMBOL_FIELD, max_length=32, prefix=field_prefix),
        signal=_read_text(payload, _SIGNAL_FIELD, max_length=64, prefix=field_prefix),
        score=_read_decimal(payload, _SCORE_FIELD, prefix=field_prefix),
        observed_at=_read_utc_datetime(
            payload,
            _OBSERVED_AT_FIELD,
            prefix=field_prefix,
        ),
    )


def _validate_result_fields(payload: dict[str, Any], field_prefix: str) -> None:
    actual_fields = set(payload)
    missing_fields = sorted(_RESULT_FIELDS - actual_fields)
    unexpected_fields = sorted(actual_fields - _RESULT_FIELDS)

    if missing_fields:
        raise ValueError(
            f"{field_prefix} missing required fields: {', '.join(missing_fields)}"
        )
    if unexpected_fields:
        raise ValueError(
            f"{field_prefix} has unexpected fields: {', '.join(unexpected_fields)}"
        )


def _read_text(
    payload: dict[str, Any],
    field_name: str,
    *,
    max_length: int,
    prefix: str | None = None,
) -> str:
    value = payload[field_name]
    qualified_name = f"{prefix}.{field_name}" if prefix else field_name
    if not isinstance(value, str):
        raise TypeError(f"{qualified_name} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{qualified_name} must be normalized non-blank text")
    if len(value) > max_length:
        raise ValueError(f"{qualified_name} must not exceed {max_length} characters")
    return value


def _read_decimal(
    payload: dict[str, Any],
    field_name: str,
    *,
    prefix: str,
) -> Decimal:
    value = payload[field_name]
    qualified_name = f"{prefix}.{field_name}"
    if not isinstance(value, str):
        raise TypeError(f"{qualified_name} must be a decimal string")
    if not value or value != value.strip():
        raise ValueError(f"{qualified_name} must be a normalized decimal string")

    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{qualified_name} must be a valid decimal string") from exc


def _read_utc_datetime(
    payload: dict[str, Any],
    field_name: str,
    *,
    prefix: str,
) -> datetime:
    value = _read_text(
        payload,
        field_name,
        max_length=64,
        prefix=prefix,
    )
    qualified_name = f"{prefix}.{field_name}"
    normalized_value = f"{value[:-1]}+00:00" if value.endswith("Z") else value

    try:
        observed_at = datetime.fromisoformat(normalized_value)
    except ValueError as exc:
        raise ValueError(f"{qualified_name} must be an ISO 8601 UTC timestamp") from exc

    if observed_at.tzinfo is None or observed_at.utcoffset() is None:
        raise ValueError(f"{qualified_name} must be timezone-aware")
    if observed_at.utcoffset() != timedelta(0):
        raise ValueError(f"{qualified_name} must use UTC")

    return observed_at.astimezone(UTC)
