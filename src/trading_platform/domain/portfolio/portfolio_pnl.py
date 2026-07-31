from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum

from trading_platform.domain.instruments.instrument_symbol import (
    validate_instrument_symbol,
)
from trading_platform.domain.portfolio.portfolio_snapshot import PortfolioSnapshot


class PortfolioPnlCompleteness(StrEnum):
    """Whether every current Portfolio position provides unrealized P&L."""

    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"


@dataclass(frozen=True, slots=True)
class PortfolioPnlSummary:
    """Exact position P&L summary derived only from supplied unrealized P&L."""

    currency: str
    positive_unrealized_pnl: Decimal
    negative_unrealized_pnl: Decimal
    net_unrealized_pnl: Decimal
    largest_winner_symbol: str | None
    largest_winner_value: Decimal | None
    largest_loser_symbol: str | None
    largest_loser_value: Decimal | None
    reported_position_count: int
    total_position_count: int
    completeness: PortfolioPnlCompleteness
    source_name: str
    observed_at: datetime

    def __post_init__(self) -> None:
        _validate_currency(self.currency)
        _validate_non_negative_decimal(
            self.positive_unrealized_pnl,
            "positive_unrealized_pnl",
        )
        _validate_non_negative_decimal(
            self.negative_unrealized_pnl,
            "negative_unrealized_pnl",
        )
        _validate_decimal(self.net_unrealized_pnl, "net_unrealized_pnl")
        if (
            self.net_unrealized_pnl
            != self.positive_unrealized_pnl - self.negative_unrealized_pnl
        ):
            raise ValueError(
                "net_unrealized_pnl must equal positive minus negative P&L"
            )

        _validate_count(self.reported_position_count, "reported_position_count")
        _validate_count(self.total_position_count, "total_position_count")
        if self.reported_position_count > self.total_position_count:
            raise ValueError(
                "reported_position_count must not exceed total_position_count"
            )
        if not isinstance(self.completeness, PortfolioPnlCompleteness):
            raise TypeError("completeness must be PortfolioPnlCompleteness")
        expected_completeness = (
            PortfolioPnlCompleteness.COMPLETE
            if self.reported_position_count == self.total_position_count
            else PortfolioPnlCompleteness.INCOMPLETE
        )
        if self.completeness is not expected_completeness:
            raise ValueError("completeness must match P&L coverage")

        self._validate_winner()
        self._validate_loser()
        _require_normalized_text(self.source_name, "source_name", max_length=200)
        _require_aware_datetime(self.observed_at, "observed_at")
        object.__setattr__(self, "observed_at", self.observed_at.astimezone(UTC))

    def _validate_winner(self) -> None:
        if self.largest_winner_symbol is None:
            if self.largest_winner_value is not None:
                raise ValueError("largest_winner_value requires largest_winner_symbol")
            if self.positive_unrealized_pnl != Decimal("0"):
                raise ValueError("positive P&L requires a largest winner")
            return

        validate_instrument_symbol(self.largest_winner_symbol)
        if self.largest_winner_value is None:
            raise ValueError("largest_winner_symbol requires largest_winner_value")
        _validate_decimal(self.largest_winner_value, "largest_winner_value")
        if self.largest_winner_value <= Decimal("0"):
            raise ValueError("largest_winner_value must be greater than zero")
        if self.largest_winner_value > self.positive_unrealized_pnl:
            raise ValueError("largest_winner_value must not exceed positive P&L")

    def _validate_loser(self) -> None:
        if self.largest_loser_symbol is None:
            if self.largest_loser_value is not None:
                raise ValueError("largest_loser_value requires largest_loser_symbol")
            if self.negative_unrealized_pnl != Decimal("0"):
                raise ValueError("negative P&L requires a largest loser")
            return

        validate_instrument_symbol(self.largest_loser_symbol)
        if self.largest_loser_value is None:
            raise ValueError("largest_loser_symbol requires largest_loser_value")
        _validate_decimal(self.largest_loser_value, "largest_loser_value")
        if self.largest_loser_value >= Decimal("0"):
            raise ValueError("largest_loser_value must be less than zero")
        if abs(self.largest_loser_value) > self.negative_unrealized_pnl:
            raise ValueError("largest_loser_value must not exceed negative P&L")


def calculate_portfolio_pnl(snapshot: PortfolioSnapshot) -> PortfolioPnlSummary:
    """Calculate position P&L without deriving or reconciling missing values."""
    if not isinstance(snapshot, PortfolioSnapshot):
        raise TypeError("snapshot must be PortfolioSnapshot")

    reported_positions = tuple(
        position
        for position in snapshot.positions
        if position.unrealized_pnl is not None
    )
    pnl_values = tuple(
        position.unrealized_pnl
        for position in reported_positions
        if position.unrealized_pnl is not None
    )
    positive_unrealized_pnl = sum(
        (value for value in pnl_values if value > Decimal("0")),
        Decimal("0"),
    )
    negative_unrealized_pnl = sum(
        (-value for value in pnl_values if value < Decimal("0")),
        Decimal("0"),
    )
    net_unrealized_pnl = positive_unrealized_pnl - negative_unrealized_pnl

    winning_positions = tuple(
        position
        for position in reported_positions
        if position.unrealized_pnl is not None
        and position.unrealized_pnl > Decimal("0")
    )
    losing_positions = tuple(
        position
        for position in reported_positions
        if position.unrealized_pnl is not None
        and position.unrealized_pnl < Decimal("0")
    )
    largest_winner = (
        max(winning_positions, key=lambda position: position.unrealized_pnl)
        if winning_positions
        else None
    )
    largest_loser = (
        min(losing_positions, key=lambda position: position.unrealized_pnl)
        if losing_positions
        else None
    )

    reported_position_count = len(reported_positions)
    total_position_count = len(snapshot.positions)
    completeness = (
        PortfolioPnlCompleteness.COMPLETE
        if reported_position_count == total_position_count
        else PortfolioPnlCompleteness.INCOMPLETE
    )

    return PortfolioPnlSummary(
        currency=snapshot.account.currency,
        positive_unrealized_pnl=positive_unrealized_pnl,
        negative_unrealized_pnl=negative_unrealized_pnl,
        net_unrealized_pnl=net_unrealized_pnl,
        largest_winner_symbol=(
            largest_winner.symbol if largest_winner is not None else None
        ),
        largest_winner_value=(
            largest_winner.unrealized_pnl if largest_winner is not None else None
        ),
        largest_loser_symbol=(
            largest_loser.symbol if largest_loser is not None else None
        ),
        largest_loser_value=(
            largest_loser.unrealized_pnl if largest_loser is not None else None
        ),
        reported_position_count=reported_position_count,
        total_position_count=total_position_count,
        completeness=completeness,
        source_name=snapshot.source_name,
        observed_at=snapshot.observed_at,
    )


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


def _validate_non_negative_decimal(value: Decimal, field_name: str) -> None:
    _validate_decimal(value, field_name)
    if value < Decimal("0"):
        raise ValueError(f"{field_name} must not be negative")


def _validate_count(value: int, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must not be negative")


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
