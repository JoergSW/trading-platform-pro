from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from trading_platform.application.portfolio.portfolio_snapshot import (
    PortfolioSnapshotResult,
)
from trading_platform.domain.portfolio.portfolio_snapshot import (
    PortfolioAccount,
    PortfolioPosition,
    PortfolioSnapshot,
)

_SOURCE_FIELD = "source_name"
_OBSERVED_AT_FIELD = "observed_at"
_ACCOUNT_FIELD = "account"
_POSITIONS_FIELD = "positions"
_ACCOUNT_REFERENCE_FIELD = "account_reference"
_CURRENCY_FIELD = "currency"
_CASH_FIELD = "cash"
_NET_LIQUIDATION_VALUE_FIELD = "net_liquidation_value"
_UNREALIZED_PNL_FIELD = "unrealized_pnl"
_SYMBOL_FIELD = "symbol"
_QUANTITY_FIELD = "quantity"
_AVERAGE_PRICE_FIELD = "average_price"
_CURRENT_PRICE_FIELD = "current_price"
_CURRENT_VALUE_FIELD = "current_value"

_TOP_LEVEL_FIELDS = frozenset(
    {
        _SOURCE_FIELD,
        _OBSERVED_AT_FIELD,
        _ACCOUNT_FIELD,
        _POSITIONS_FIELD,
    }
)
_ACCOUNT_REQUIRED_FIELDS = frozenset({_ACCOUNT_REFERENCE_FIELD, _CURRENCY_FIELD})
_ACCOUNT_OPTIONAL_FIELDS = frozenset(
    {_CASH_FIELD, _NET_LIQUIDATION_VALUE_FIELD, _UNREALIZED_PNL_FIELD}
)
_POSITION_REQUIRED_FIELDS = frozenset({_SYMBOL_FIELD, _QUANTITY_FIELD})
_POSITION_OPTIONAL_FIELDS = frozenset(
    {
        _AVERAGE_PRICE_FIELD,
        _CURRENT_PRICE_FIELD,
        _CURRENT_VALUE_FIELD,
        _UNREALIZED_PNL_FIELD,
    }
)
_MAX_POSITIONS = 10_000


class JsonPortfolioSnapshotProvider:
    """Load one validated read-only portfolio snapshot from explicit JSON."""

    def __init__(self, snapshot_path: Path) -> None:
        self._snapshot_path = snapshot_path

    @property
    def snapshot_path(self) -> Path:
        return self._snapshot_path

    def load_snapshot(self) -> PortfolioSnapshotResult:
        source_fallback = f"JSON file: {self._snapshot_path}"
        if not self._snapshot_path.is_file():
            return PortfolioSnapshotResult.error(
                detail=(
                    "Configured JSON portfolio snapshot file was not found: "
                    f"{self._snapshot_path}"
                ),
                source_name=source_fallback,
            )

        try:
            payload = json.loads(self._snapshot_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError) as exc:
            return PortfolioSnapshotResult.error(
                detail=(
                    "Configured JSON portfolio snapshot file could not be read: "
                    f"{type(exc).__name__}."
                ),
                source_name=source_fallback,
            )
        except JSONDecodeError:
            return PortfolioSnapshotResult.error(
                detail="Configured JSON portfolio snapshot file contains invalid JSON.",
                source_name=source_fallback,
            )

        try:
            snapshot = _snapshot_from_payload(payload)
        except (TypeError, ValueError) as exc:
            return PortfolioSnapshotResult.error(
                detail=f"Configured JSON portfolio snapshot failed validation: {exc}",
                source_name=source_fallback,
            )

        if snapshot.positions:
            return PortfolioSnapshotResult.ready(snapshot)
        return PortfolioSnapshotResult.empty(snapshot)


def _snapshot_from_payload(payload: Any) -> PortfolioSnapshot:
    if not isinstance(payload, dict):
        raise TypeError("top-level JSON value must be an object")
    _validate_fields(payload, _TOP_LEVEL_FIELDS, frozenset(), "top-level object")

    raw_positions = payload[_POSITIONS_FIELD]
    if not isinstance(raw_positions, list):
        raise TypeError("positions must be an array")
    if len(raw_positions) > _MAX_POSITIONS:
        raise ValueError(f"positions must not contain more than {_MAX_POSITIONS} items")

    positions = tuple(
        sorted(
            (
                _read_position(raw_position, index)
                for index, raw_position in enumerate(raw_positions)
            ),
            key=lambda position: position.symbol,
        )
    )
    return PortfolioSnapshot(
        account=_read_account(payload[_ACCOUNT_FIELD]),
        positions=positions,
        source_name=_read_text(payload, _SOURCE_FIELD, max_length=200),
        observed_at=_read_utc_datetime(payload, _OBSERVED_AT_FIELD),
    )


def _read_account(payload: Any) -> PortfolioAccount:
    if not isinstance(payload, dict):
        raise TypeError("account must be an object")
    _validate_fields(
        payload,
        _ACCOUNT_REQUIRED_FIELDS,
        _ACCOUNT_OPTIONAL_FIELDS,
        "account",
    )
    return PortfolioAccount(
        account_reference=_read_text(
            payload,
            _ACCOUNT_REFERENCE_FIELD,
            max_length=128,
            prefix="account",
        ),
        currency=_read_text(
            payload,
            _CURRENCY_FIELD,
            max_length=3,
            prefix="account",
        ),
        cash=_read_optional_decimal(payload, _CASH_FIELD, "account"),
        net_liquidation_value=_read_optional_decimal(
            payload,
            _NET_LIQUIDATION_VALUE_FIELD,
            "account",
        ),
        unrealized_pnl=_read_optional_decimal(
            payload,
            _UNREALIZED_PNL_FIELD,
            "account",
        ),
    )


def _read_position(payload: Any, index: int) -> PortfolioPosition:
    prefix = f"positions[{index}]"
    if not isinstance(payload, dict):
        raise TypeError(f"{prefix} must be an object")
    _validate_fields(
        payload,
        _POSITION_REQUIRED_FIELDS,
        _POSITION_OPTIONAL_FIELDS,
        prefix,
    )
    return PortfolioPosition(
        symbol=_read_text(payload, _SYMBOL_FIELD, max_length=32, prefix=prefix),
        quantity=_read_decimal(payload, _QUANTITY_FIELD, prefix),
        average_price=_read_optional_decimal(payload, _AVERAGE_PRICE_FIELD, prefix),
        current_price=_read_optional_decimal(payload, _CURRENT_PRICE_FIELD, prefix),
        current_value=_read_optional_decimal(payload, _CURRENT_VALUE_FIELD, prefix),
        unrealized_pnl=_read_optional_decimal(payload, _UNREALIZED_PNL_FIELD, prefix),
    )


def _validate_fields(
    payload: dict[str, Any],
    required_fields: frozenset[str],
    optional_fields: frozenset[str],
    prefix: str,
) -> None:
    actual_fields = set(payload)
    missing_fields = sorted(required_fields - actual_fields)
    unexpected_fields = sorted(actual_fields - required_fields - optional_fields)
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


def _read_optional_decimal(
    payload: dict[str, Any],
    field_name: str,
    prefix: str,
) -> Decimal | None:
    if field_name not in payload:
        return None
    return _read_decimal(payload, field_name, prefix)


def _read_utc_datetime(payload: dict[str, Any], field_name: str) -> datetime:
    value = _read_text(payload, field_name, max_length=64)
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
