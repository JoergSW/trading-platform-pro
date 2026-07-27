from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from trading_platform.domain.portfolio.portfolio_snapshot import (
    PortfolioAccount,
    PortfolioPosition,
    PortfolioSnapshot,
)


def _account() -> PortfolioAccount:
    return PortfolioAccount(
        account_reference="LOCAL-ACCOUNT",
        currency="USD",
        cash=Decimal("1000.00"),
        net_liquidation_value=Decimal("2500.00"),
        unrealized_pnl=Decimal("25.50"),
    )


def _position(symbol: str = "AAPL") -> PortfolioPosition:
    return PortfolioPosition(
        symbol=symbol,
        quantity=Decimal("10"),
        average_price=Decimal("180.25"),
        current_price=Decimal("190.10"),
        current_value=Decimal("1901.00"),
        unrealized_pnl=Decimal("98.50"),
    )


def test_portfolio_snapshot_preserves_exact_financial_values() -> None:
    observed_at = datetime(
        2026,
        7,
        27,
        12,
        15,
        tzinfo=timezone(timedelta(hours=2)),
    )
    position = _position()

    snapshot = PortfolioSnapshot(
        account=_account(),
        positions=(position,),
        source_name="Local Portfolio Export",
        observed_at=observed_at,
    )

    assert snapshot.observed_at == datetime(2026, 7, 27, 10, 15, tzinfo=UTC)
    assert snapshot.positions == (position,)
    assert snapshot.account.cash == Decimal("1000.00")
    assert snapshot.account.net_liquidation_value == Decimal("2500.00")
    assert snapshot.account.unrealized_pnl == Decimal("25.50")


def test_unavailable_financial_values_remain_none() -> None:
    account = PortfolioAccount("LOCAL-ACCOUNT", "USD")
    position = PortfolioPosition("AAPL", Decimal("10"))

    assert account.cash is None
    assert account.net_liquidation_value is None
    assert account.unrealized_pnl is None
    assert position.average_price is None
    assert position.current_price is None
    assert position.current_value is None
    assert position.unrealized_pnl is None


def test_known_zero_financial_values_remain_zero() -> None:
    account = PortfolioAccount(
        "LOCAL-ACCOUNT",
        "USD",
        cash=Decimal("0"),
        unrealized_pnl=Decimal("0"),
    )
    position = PortfolioPosition(
        "AAPL",
        Decimal("10"),
        current_value=Decimal("0"),
        unrealized_pnl=Decimal("0"),
    )

    assert account.cash == Decimal("0")
    assert account.unrealized_pnl == Decimal("0")
    assert position.current_value == Decimal("0")
    assert position.unrealized_pnl == Decimal("0")


def test_position_allows_short_quantity_and_signed_values() -> None:
    position = PortfolioPosition(
        "AAPL",
        Decimal("-10"),
        average_price=Decimal("180.25"),
        current_price=Decimal("190.10"),
        current_value=Decimal("-1901.00"),
        unrealized_pnl=Decimal("-98.50"),
    )

    assert position.quantity == Decimal("-10")
    assert position.current_value == Decimal("-1901.00")
    assert position.unrealized_pnl == Decimal("-98.50")


def test_position_rejects_zero_quantity() -> None:
    with pytest.raises(ValueError, match="quantity must not be zero"):
        PortfolioPosition("AAPL", Decimal("0"))


def test_portfolio_account_requires_normalized_currency() -> None:
    with pytest.raises(ValueError, match="three-letter ASCII"):
        PortfolioAccount("LOCAL-ACCOUNT", "US")

    with pytest.raises(ValueError, match="uppercase"):
        PortfolioAccount("LOCAL-ACCOUNT", "usd")


def test_prices_require_positive_finite_decimals_when_available() -> None:
    with pytest.raises(ValueError, match="average_price must be greater than zero"):
        PortfolioPosition("AAPL", Decimal("10"), average_price=Decimal("0"))

    with pytest.raises(ValueError, match="current_price must be finite"):
        PortfolioPosition("AAPL", Decimal("10"), current_price=Decimal("NaN"))


def test_snapshot_rejects_duplicate_symbols() -> None:
    with pytest.raises(ValueError, match="unique symbols"):
        PortfolioSnapshot(
            account=_account(),
            positions=(_position(), _position()),
            source_name="Local Portfolio Export",
            observed_at=datetime(2026, 7, 27, 10, 15, tzinfo=UTC),
        )


def test_snapshot_is_immutable() -> None:
    snapshot = PortfolioSnapshot(
        account=_account(),
        positions=(_position(),),
        source_name="Local Portfolio Export",
        observed_at=datetime(2026, 7, 27, 10, 15, tzinfo=UTC),
    )

    with pytest.raises(FrozenInstanceError):
        snapshot.source_name = "changed"
