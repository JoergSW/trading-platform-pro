from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from trading_platform.domain.instruments.instrument_symbol import (
    validate_instrument_symbol,
)


@dataclass(frozen=True, slots=True)
class PortfolioAccount:
    """Provider-independent account context for one portfolio observation."""

    account_reference: str
    currency: str
    cash: Decimal | None = None
    net_liquidation_value: Decimal | None = None
    unrealized_pnl: Decimal | None = None

    def __post_init__(self) -> None:
        _require_normalized_text(
            self.account_reference,
            "account_reference",
            max_length=128,
        )
        _validate_currency(self.currency)
        _validate_optional_decimal(self.cash, "cash")
        _validate_optional_decimal(
            self.net_liquidation_value,
            "net_liquidation_value",
        )
        _validate_optional_decimal(self.unrealized_pnl, "unrealized_pnl")


@dataclass(frozen=True, slots=True)
class PortfolioPosition:
    """One immutable read-only position contained in a portfolio snapshot."""

    symbol: str
    quantity: Decimal
    average_price: Decimal | None = None
    current_price: Decimal | None = None
    current_value: Decimal | None = None
    unrealized_pnl: Decimal | None = None

    def __post_init__(self) -> None:
        validate_instrument_symbol(self.symbol)
        _validate_decimal(self.quantity, "quantity")
        if self.quantity == Decimal("0"):
            raise ValueError("quantity must not be zero")
        _validate_optional_positive_decimal(self.average_price, "average_price")
        _validate_optional_positive_decimal(self.current_price, "current_price")
        _validate_optional_decimal(self.current_value, "current_value")
        _validate_optional_decimal(self.unrealized_pnl, "unrealized_pnl")


@dataclass(frozen=True, slots=True)
class PortfolioSnapshot:
    """One immutable account and position observation from a named source."""

    account: PortfolioAccount
    positions: tuple[PortfolioPosition, ...]
    source_name: str
    observed_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.account, PortfolioAccount):
            raise TypeError("account must be PortfolioAccount")
        if not isinstance(self.positions, tuple):
            raise TypeError("positions must be a tuple")
        if not all(
            isinstance(position, PortfolioPosition) for position in self.positions
        ):
            raise TypeError("positions must contain only PortfolioPosition values")
        _require_normalized_text(self.source_name, "source_name", max_length=200)
        _require_aware_datetime(self.observed_at, "observed_at")
        object.__setattr__(self, "observed_at", self.observed_at.astimezone(UTC))

        symbols = tuple(position.symbol for position in self.positions)
        if len(symbols) != len(set(symbols)):
            raise ValueError("positions must contain unique symbols")


def _validate_currency(value: str) -> None:
    _require_normalized_text(value, "currency", max_length=3)
    if len(value) != 3 or not value.isascii() or not value.isalpha():
        raise ValueError("currency must be a three-letter ASCII code")
    if value != value.upper():
        raise ValueError("currency must use uppercase characters")


def _validate_decimal(value: Decimal, field_name: str) -> None:
    if not isinstance(value, Decimal):
        raise TypeError(f"{field_name} must be Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _validate_optional_decimal(value: Decimal | None, field_name: str) -> None:
    if value is not None:
        _validate_decimal(value, field_name)


def _validate_optional_positive_decimal(
    value: Decimal | None,
    field_name: str,
) -> None:
    if value is None:
        return
    _validate_decimal(value, field_name)
    if value <= Decimal("0"):
        raise ValueError(f"{field_name} must be greater than zero")


def _require_aware_datetime(value: datetime, field_name: str) -> None:
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")


def _require_normalized_text(
    value: str,
    field_name: str,
    *,
    max_length: int,
) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{field_name} must be normalized non-blank text")
    if len(value) > max_length:
        raise ValueError(f"{field_name} must not exceed {max_length} characters")
