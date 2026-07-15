from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Protocol

from trading_platform.application.instruments.instrument_context import (
    validate_instrument_symbol,
)

DEFAULT_PRICE_HISTORY_TIMEFRAME = "1D"


class PriceHistoryState(StrEnum):
    """Application-owned availability state for historical price data."""

    READY = "READY"
    NO_DATA = "NO DATA"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


@dataclass(frozen=True, slots=True)
class PriceBar:
    """One immutable provider-independent UTC OHLCV bar."""

    observed_at: datetime
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: int

    def __post_init__(self) -> None:
        if not isinstance(self.observed_at, datetime):
            raise TypeError("observed_at must be datetime")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise ValueError("observed_at must be timezone-aware")
        object.__setattr__(self, "observed_at", self.observed_at.astimezone(UTC))

        for field_name, value in (
            ("open_price", self.open_price),
            ("high_price", self.high_price),
            ("low_price", self.low_price),
            ("close_price", self.close_price),
        ):
            _validate_price(value, field_name)

        if self.high_price < max(
            self.open_price,
            self.low_price,
            self.close_price,
        ):
            raise ValueError("high_price must be the highest OHLC value")
        if self.low_price > min(
            self.open_price,
            self.high_price,
            self.close_price,
        ):
            raise ValueError("low_price must be the lowest OHLC value")
        if isinstance(self.volume, bool) or not isinstance(self.volume, int):
            raise TypeError("volume must be an integer")
        if self.volume < 0:
            raise ValueError("volume must not be negative")


@dataclass(frozen=True, slots=True)
class PriceHistory:
    """Immutable historical price result for one selected instrument."""

    state: PriceHistoryState
    symbol: str
    timeframe: str
    source_name: str | None
    bars: tuple[PriceBar, ...]
    detail: str

    def __post_init__(self) -> None:
        if not isinstance(self.state, PriceHistoryState):
            raise TypeError("state must be a PriceHistoryState")
        validate_instrument_symbol(self.symbol)
        _require_normalized_text(self.timeframe, "timeframe", max_length=16)
        if not isinstance(self.bars, tuple):
            raise TypeError("bars must be a tuple")
        if not all(isinstance(bar, PriceBar) for bar in self.bars):
            raise TypeError("bars must contain only PriceBar values")
        _require_normalized_text(self.detail, "detail", max_length=1_000)

        if self.state is PriceHistoryState.READY:
            _require_normalized_text(self.source_name, "source_name", max_length=200)
            if not self.bars:
                raise ValueError("READY price history requires at least one bar")
            timestamps = tuple(bar.observed_at for bar in self.bars)
            if timestamps != tuple(sorted(timestamps)):
                raise ValueError("READY price bars must be ordered oldest first")
            if len(timestamps) != len(set(timestamps)):
                raise ValueError("READY price bars require unique timestamps")
            return

        if self.bars:
            raise ValueError(f"{self.state.value} price history must not contain bars")

        if self.state is PriceHistoryState.NO_DATA:
            _require_normalized_text(self.source_name, "source_name", max_length=200)
        elif self.source_name is not None:
            _require_normalized_text(self.source_name, "source_name", max_length=200)

    @classmethod
    def ready(
        cls,
        symbol: str,
        source_name: str,
        timeframe: str,
        bars: tuple[PriceBar, ...],
    ) -> PriceHistory:
        return cls(
            state=PriceHistoryState.READY,
            symbol=symbol,
            timeframe=timeframe,
            source_name=source_name,
            bars=bars,
            detail="Validated historical OHLCV data is available.",
        )

    @classmethod
    def no_data(
        cls,
        symbol: str,
        source_name: str,
        timeframe: str = DEFAULT_PRICE_HISTORY_TIMEFRAME,
    ) -> PriceHistory:
        return cls(
            state=PriceHistoryState.NO_DATA,
            symbol=symbol,
            timeframe=timeframe,
            source_name=source_name,
            bars=(),
            detail=(
                "The configured source contains no historical price data for the "
                "selected instrument. No fallback values are displayed."
            ),
        )

    @classmethod
    def unavailable(
        cls,
        symbol: str,
        source_name: str | None = None,
        timeframe: str = DEFAULT_PRICE_HISTORY_TIMEFRAME,
        detail: str | None = None,
    ) -> PriceHistory:
        return cls(
            state=PriceHistoryState.UNAVAILABLE,
            symbol=symbol,
            timeframe=timeframe,
            source_name=source_name,
            bars=(),
            detail=(
                detail
                if detail is not None
                else (
                    "No historical price source is configured. Price and volume "
                    "values are not estimated or reused."
                )
            ),
        )

    @classmethod
    def error(
        cls,
        symbol: str,
        detail: str,
        source_name: str | None = None,
        timeframe: str = DEFAULT_PRICE_HISTORY_TIMEFRAME,
    ) -> PriceHistory:
        return cls(
            state=PriceHistoryState.ERROR,
            symbol=symbol,
            timeframe=timeframe,
            source_name=source_name,
            bars=(),
            detail=detail,
        )


class PriceHistoryProvider(Protocol):
    """Application port for loading historical price data by Symbol."""

    def load_history(self, symbol: str) -> PriceHistory:
        """Load the current read-only history for one normalized Symbol."""
        ...


class PriceHistoryService:
    """Coordinate validated price-history loading through the Application port."""

    def __init__(self, provider: PriceHistoryProvider) -> None:
        self._provider = provider

    def load_history(self, symbol: str) -> PriceHistory:
        normalized_symbol = validate_instrument_symbol(symbol)
        history = self._provider.load_history(normalized_symbol)
        if not isinstance(history, PriceHistory):
            raise TypeError("Price history provider returned an invalid result")
        if history.symbol != normalized_symbol:
            raise ValueError("Price history provider returned a different symbol")
        return history


def _validate_price(value: Decimal, field_name: str) -> None:
    if not isinstance(value, Decimal):
        raise TypeError(f"{field_name} must be Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value <= Decimal("0"):
        raise ValueError(f"{field_name} must be greater than zero")


def _require_normalized_text(
    value: str | None,
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
