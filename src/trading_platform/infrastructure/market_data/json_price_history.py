from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from trading_platform.application.instruments.instrument_context import (
    validate_instrument_symbol,
)
from trading_platform.application.market_data.price_history import (
    PriceBar,
    PriceHistory,
)

_SOURCE_FIELD = "source_name"
_TIMEFRAME_FIELD = "timeframe"
_SERIES_FIELD = "series"
_SYMBOL_FIELD = "symbol"
_BARS_FIELD = "bars"
_OBSERVED_AT_FIELD = "observed_at"
_OPEN_FIELD = "open"
_HIGH_FIELD = "high"
_LOW_FIELD = "low"
_CLOSE_FIELD = "close"
_VOLUME_FIELD = "volume"

_TOP_LEVEL_FIELDS = frozenset({_SOURCE_FIELD, _TIMEFRAME_FIELD, _SERIES_FIELD})
_SERIES_FIELDS = frozenset({_SYMBOL_FIELD, _BARS_FIELD})
_BAR_FIELDS = frozenset(
    {
        _OBSERVED_AT_FIELD,
        _OPEN_FIELD,
        _HIGH_FIELD,
        _LOW_FIELD,
        _CLOSE_FIELD,
        _VOLUME_FIELD,
    }
)
_MAX_SERIES = 1_000
_MAX_BARS_PER_SERIES = 5_000


class JsonPriceHistoryProvider:
    """Load validated historical OHLCV data from one explicit local JSON file."""

    def __init__(self, history_path: Path) -> None:
        self._history_path = history_path

    @property
    def history_path(self) -> Path:
        return self._history_path

    def load_history(self, symbol: str) -> PriceHistory:
        normalized_symbol = validate_instrument_symbol(symbol)
        source_fallback = f"JSON file: {self._history_path}"

        if not self._history_path.is_file():
            return PriceHistory.unavailable(
                normalized_symbol,
                source_name=source_fallback,
                detail=(
                    "Configured JSON price-history file was not found: "
                    f"{self._history_path}"
                ),
            )

        try:
            payload = json.loads(self._history_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError) as exc:
            return PriceHistory.unavailable(
                normalized_symbol,
                source_name=source_fallback,
                detail=(
                    "Configured JSON price-history file could not be read: "
                    f"{type(exc).__name__}."
                ),
            )
        except JSONDecodeError:
            return PriceHistory.error(
                normalized_symbol,
                source_name=source_fallback,
                detail="Configured JSON price-history file contains invalid JSON.",
            )

        try:
            source_name, timeframe, series = _history_from_payload(payload)
        except (TypeError, ValueError) as exc:
            return PriceHistory.error(
                normalized_symbol,
                source_name=source_fallback,
                detail=f"Configured JSON price history failed validation: {exc}",
            )

        bars = series.get(normalized_symbol)
        if not bars:
            return PriceHistory.no_data(
                normalized_symbol,
                source_name=source_name,
                timeframe=timeframe,
            )

        return PriceHistory.ready(
            normalized_symbol,
            source_name=source_name,
            timeframe=timeframe,
            bars=bars,
        )


def _history_from_payload(
    payload: Any,
) -> tuple[str, str, dict[str, tuple[PriceBar, ...]]]:
    if not isinstance(payload, dict):
        raise TypeError("top-level JSON value must be an object")
    _validate_exact_fields(payload, _TOP_LEVEL_FIELDS, "top-level object")

    source_name = _read_text(payload, _SOURCE_FIELD, max_length=200)
    timeframe = _read_text(payload, _TIMEFRAME_FIELD, max_length=16)
    raw_series = payload[_SERIES_FIELD]
    if not isinstance(raw_series, list):
        raise TypeError("series must be an array")
    if len(raw_series) > _MAX_SERIES:
        raise ValueError(f"series must not contain more than {_MAX_SERIES} items")

    result: dict[str, tuple[PriceBar, ...]] = {}
    for index, raw_item in enumerate(raw_series):
        prefix = f"series[{index}]"
        if not isinstance(raw_item, dict):
            raise TypeError(f"{prefix} must be an object")
        _validate_exact_fields(raw_item, _SERIES_FIELDS, prefix)
        symbol = _read_text(raw_item, _SYMBOL_FIELD, max_length=32, prefix=prefix)
        validate_instrument_symbol(symbol)
        if symbol in result:
            raise ValueError(f"series contains duplicate symbol: {symbol}")
        result[symbol] = _read_bars(raw_item[_BARS_FIELD], prefix)

    return source_name, timeframe, result


def _read_bars(payload: Any, series_prefix: str) -> tuple[PriceBar, ...]:
    if not isinstance(payload, list):
        raise TypeError(f"{series_prefix}.bars must be an array")
    if len(payload) > _MAX_BARS_PER_SERIES:
        raise ValueError(
            f"{series_prefix}.bars must not contain more than "
            f"{_MAX_BARS_PER_SERIES} items"
        )

    bars: list[PriceBar] = []
    for index, raw_bar in enumerate(payload):
        prefix = f"{series_prefix}.bars[{index}]"
        if not isinstance(raw_bar, dict):
            raise TypeError(f"{prefix} must be an object")
        _validate_exact_fields(raw_bar, _BAR_FIELDS, prefix)
        bars.append(
            PriceBar(
                observed_at=_read_utc_datetime(raw_bar, prefix),
                open_price=_read_decimal(raw_bar, _OPEN_FIELD, prefix),
                high_price=_read_decimal(raw_bar, _HIGH_FIELD, prefix),
                low_price=_read_decimal(raw_bar, _LOW_FIELD, prefix),
                close_price=_read_decimal(raw_bar, _CLOSE_FIELD, prefix),
                volume=_read_volume(raw_bar, prefix),
            )
        )
    return tuple(bars)


def _validate_exact_fields(
    payload: dict[str, Any],
    expected_fields: frozenset[str],
    prefix: str,
) -> None:
    actual_fields = set(payload)
    missing_fields = sorted(expected_fields - actual_fields)
    unexpected_fields = sorted(actual_fields - expected_fields)
    if missing_fields:
        raise ValueError(
            f"{prefix} missing required fields: {', '.join(missing_fields)}"
        )
    if unexpected_fields:
        raise ValueError(
            f"{prefix} has unexpected fields: {', '.join(unexpected_fields)}"
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


def _read_volume(payload: dict[str, Any], prefix: str) -> int:
    value = payload[_VOLUME_FIELD]
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{prefix}.volume must be an integer")
    return value


def _read_utc_datetime(payload: dict[str, Any], prefix: str) -> datetime:
    value = _read_text(
        payload,
        _OBSERVED_AT_FIELD,
        max_length=64,
        prefix=prefix,
    )
    normalized_value = f"{value[:-1]}+00:00" if value.endswith("Z") else value
    try:
        observed_at = datetime.fromisoformat(normalized_value)
    except ValueError as exc:
        raise ValueError(
            f"{prefix}.observed_at must be an ISO 8601 UTC timestamp"
        ) from exc
    if observed_at.tzinfo is None or observed_at.utcoffset() is None:
        raise ValueError(f"{prefix}.observed_at must be timezone-aware")
    if observed_at.utcoffset() != timedelta(0):
        raise ValueError(f"{prefix}.observed_at must use UTC")
    return observed_at.astimezone(UTC)
