from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from trading_platform.application.market_data.price_history import (
    PriceBar,
    PriceHistory,
    PriceHistoryService,
    PriceHistoryState,
)


def _bar(
    observed_at: datetime | None = None,
    *,
    open_price: str = "100.00",
    high_price: str = "103.00",
    low_price: str = "99.00",
    close_price: str = "102.00",
    volume: int = 1000,
) -> PriceBar:
    return PriceBar(
        observed_at=observed_at or datetime(2026, 7, 1, 20, tzinfo=UTC),
        open_price=Decimal(open_price),
        high_price=Decimal(high_price),
        low_price=Decimal(low_price),
        close_price=Decimal(close_price),
        volume=volume,
    )


def test_price_bar_normalizes_timestamp_to_utc_and_is_immutable() -> None:
    bar = _bar(
        datetime(
            2026,
            7,
            1,
            22,
            tzinfo=timezone(timedelta(hours=2)),
        )
    )

    assert bar.observed_at == datetime(2026, 7, 1, 20, tzinfo=UTC)
    with pytest.raises(FrozenInstanceError):
        bar.volume = 0  # type: ignore[misc]


def test_price_bar_rejects_invalid_ohlc_and_volume() -> None:
    with pytest.raises(ValueError, match="highest OHLC"):
        _bar(high_price="101.00", close_price="102.00")
    with pytest.raises(ValueError, match="lowest OHLC"):
        _bar(low_price="101.00", open_price="100.00")
    with pytest.raises(ValueError, match="must not be negative"):
        _bar(volume=-1)


def test_ready_price_history_requires_ordered_unique_bars() -> None:
    first = _bar(datetime(2026, 7, 2, 20, tzinfo=UTC))
    second = _bar(datetime(2026, 7, 1, 20, tzinfo=UTC))

    with pytest.raises(ValueError, match="ordered oldest first"):
        PriceHistory.ready("AAPL", "Test Feed", "1D", (first, second))
    with pytest.raises(ValueError, match="unique timestamps"):
        PriceHistory.ready("AAPL", "Test Feed", "1D", (first, first))


def test_price_history_states_preserve_unavailable_and_no_data() -> None:
    no_data = PriceHistory.no_data("AAPL", "Test Feed")
    unavailable = PriceHistory.unavailable("AAPL")
    error = PriceHistory.error("AAPL", "Controlled error.")

    assert no_data.state is PriceHistoryState.NO_DATA
    assert unavailable.state is PriceHistoryState.UNAVAILABLE
    assert error.state is PriceHistoryState.ERROR
    assert not no_data.bars
    assert not unavailable.bars
    assert not error.bars


def test_price_history_service_rejects_different_provider_symbol() -> None:
    class WrongSymbolProvider:
        def load_history(self, symbol: str) -> PriceHistory:
            return PriceHistory.no_data("MSFT", "Test Feed")

    with pytest.raises(ValueError, match="different symbol"):
        PriceHistoryService(WrongSymbolProvider()).load_history("AAPL")
