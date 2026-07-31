from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from trading_platform.domain.portfolio.portfolio_pnl import (
    PortfolioPnlCompleteness,
    calculate_portfolio_pnl,
)
from trading_platform.domain.portfolio.portfolio_snapshot import (
    PortfolioAccount,
    PortfolioPosition,
    PortfolioSnapshot,
)


def _snapshot(
    positions: tuple[PortfolioPosition, ...],
    *,
    account_unrealized_pnl: Decimal | None = None,
) -> PortfolioSnapshot:
    return PortfolioSnapshot(
        account=PortfolioAccount(
            "LOCAL-ACCOUNT",
            "USD",
            unrealized_pnl=account_unrealized_pnl,
        ),
        positions=positions,
        source_name="Local Portfolio Export",
        observed_at=datetime(2026, 7, 31, 7, 15, tzinfo=UTC),
    )


def test_pnl_uses_only_source_provided_position_unrealized_pnl() -> None:
    snapshot = _snapshot(
        (
            PortfolioPosition(
                "AAPL",
                Decimal("10"),
                unrealized_pnl=Decimal("98.50"),
            ),
            PortfolioPosition(
                "SPY",
                Decimal("-2"),
                unrealized_pnl=Decimal("-40.25"),
            ),
            PortfolioPosition(
                "MSFT",
                Decimal("5"),
                unrealized_pnl=Decimal("0"),
            ),
        ),
        account_unrealized_pnl=Decimal("999.00"),
    )

    summary = calculate_portfolio_pnl(snapshot)

    assert summary.positive_unrealized_pnl == Decimal("98.50")
    assert summary.negative_unrealized_pnl == Decimal("40.25")
    assert summary.net_unrealized_pnl == Decimal("58.25")
    assert summary.largest_winner_symbol == "AAPL"
    assert summary.largest_winner_value == Decimal("98.50")
    assert summary.largest_loser_symbol == "SPY"
    assert summary.largest_loser_value == Decimal("-40.25")
    assert summary.reported_position_count == 3
    assert summary.total_position_count == 3
    assert summary.completeness is PortfolioPnlCompleteness.COMPLETE
    assert summary.source_name == snapshot.source_name
    assert summary.observed_at == snapshot.observed_at


def test_incomplete_pnl_excludes_missing_values_without_reconstruction() -> None:
    snapshot = _snapshot(
        (
            PortfolioPosition(
                "AAPL",
                Decimal("10"),
                average_price=Decimal("180.00"),
                current_price=Decimal("190.00"),
                current_value=Decimal("1900.00"),
                unrealized_pnl=Decimal("100.00"),
            ),
            PortfolioPosition(
                "MSFT",
                Decimal("5"),
                average_price=Decimal("400.00"),
                current_price=Decimal("450.00"),
                current_value=Decimal("2250.00"),
            ),
        )
    )

    summary = calculate_portfolio_pnl(snapshot)

    assert summary.positive_unrealized_pnl == Decimal("100.00")
    assert summary.negative_unrealized_pnl == Decimal("0")
    assert summary.net_unrealized_pnl == Decimal("100.00")
    assert summary.largest_winner_symbol == "AAPL"
    assert summary.largest_loser_symbol is None
    assert summary.reported_position_count == 1
    assert summary.total_position_count == 2
    assert summary.completeness is PortfolioPnlCompleteness.INCOMPLETE


def test_empty_portfolio_has_known_zero_position_pnl() -> None:
    summary = calculate_portfolio_pnl(_snapshot(()))

    assert summary.positive_unrealized_pnl == Decimal("0")
    assert summary.negative_unrealized_pnl == Decimal("0")
    assert summary.net_unrealized_pnl == Decimal("0")
    assert summary.largest_winner_symbol is None
    assert summary.largest_winner_value is None
    assert summary.largest_loser_symbol is None
    assert summary.largest_loser_value is None
    assert summary.reported_position_count == 0
    assert summary.total_position_count == 0
    assert summary.completeness is PortfolioPnlCompleteness.COMPLETE


def test_zero_position_pnl_is_reported_without_winner_or_loser() -> None:
    summary = calculate_portfolio_pnl(
        _snapshot(
            (
                PortfolioPosition(
                    "AAPL",
                    Decimal("10"),
                    unrealized_pnl=Decimal("0"),
                ),
            )
        )
    )

    assert summary.positive_unrealized_pnl == Decimal("0")
    assert summary.negative_unrealized_pnl == Decimal("0")
    assert summary.net_unrealized_pnl == Decimal("0")
    assert summary.largest_winner_symbol is None
    assert summary.largest_loser_symbol is None
    assert summary.reported_position_count == 1
    assert summary.completeness is PortfolioPnlCompleteness.COMPLETE
