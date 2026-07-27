from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from trading_platform.domain.portfolio.portfolio_snapshot import (
    PortfolioAccount,
    PortfolioPosition,
    PortfolioSnapshot,
)
from trading_platform.domain.risk.portfolio_exposure import (
    PortfolioExposureCompleteness,
    calculate_portfolio_exposure,
)


def _snapshot(
    positions: tuple[PortfolioPosition, ...],
) -> PortfolioSnapshot:
    return PortfolioSnapshot(
        account=PortfolioAccount("LOCAL-ACCOUNT", "USD"),
        positions=positions,
        source_name="Local Portfolio Export",
        observed_at=datetime(2026, 7, 27, 10, 15, tzinfo=UTC),
    )


def test_exposure_uses_only_source_provided_current_values() -> None:
    snapshot = _snapshot(
        (
            PortfolioPosition(
                "AAPL",
                Decimal("10"),
                current_value=Decimal("1900.00"),
            ),
            PortfolioPosition(
                "SPY",
                Decimal("-2"),
                current_value=Decimal("-500.00"),
            ),
        )
    )

    summary = calculate_portfolio_exposure(snapshot)

    assert summary.long_exposure == Decimal("1900.00")
    assert summary.short_exposure == Decimal("500.00")
    assert summary.gross_exposure == Decimal("2400.00")
    assert summary.net_exposure == Decimal("1400.00")
    assert summary.largest_position_symbol == "AAPL"
    assert summary.largest_position_value == Decimal("1900.00")
    assert summary.largest_position_concentration_pct == Decimal(
        "79.16666666666666666666666667"
    )
    assert summary.valued_position_count == 2
    assert summary.total_position_count == 2
    assert summary.completeness is PortfolioExposureCompleteness.COMPLETE
    assert summary.source_name == snapshot.source_name
    assert summary.observed_at == snapshot.observed_at


def test_incomplete_exposure_excludes_missing_values_without_reconstruction() -> None:
    snapshot = _snapshot(
        (
            PortfolioPosition(
                "AAPL",
                Decimal("10"),
                current_price=Decimal("190.00"),
                current_value=Decimal("1900.00"),
            ),
            PortfolioPosition(
                "MSFT",
                Decimal("5"),
                current_price=Decimal("450.00"),
            ),
        )
    )

    summary = calculate_portfolio_exposure(snapshot)

    assert summary.long_exposure == Decimal("1900.00")
    assert summary.short_exposure == Decimal("0")
    assert summary.gross_exposure == Decimal("1900.00")
    assert summary.net_exposure == Decimal("1900.00")
    assert summary.valued_position_count == 1
    assert summary.total_position_count == 2
    assert summary.completeness is PortfolioExposureCompleteness.INCOMPLETE


def test_empty_portfolio_has_known_zero_exposure() -> None:
    summary = calculate_portfolio_exposure(_snapshot(()))

    assert summary.long_exposure == Decimal("0")
    assert summary.short_exposure == Decimal("0")
    assert summary.gross_exposure == Decimal("0")
    assert summary.net_exposure == Decimal("0")
    assert summary.largest_position_symbol is None
    assert summary.largest_position_value is None
    assert summary.largest_position_concentration_pct == Decimal("0")
    assert summary.valued_position_count == 0
    assert summary.total_position_count == 0
    assert summary.completeness is PortfolioExposureCompleteness.COMPLETE


def test_zero_valued_positions_do_not_create_a_largest_position() -> None:
    summary = calculate_portfolio_exposure(
        _snapshot(
            (
                PortfolioPosition(
                    "AAPL",
                    Decimal("10"),
                    current_value=Decimal("0"),
                ),
            )
        )
    )

    assert summary.gross_exposure == Decimal("0")
    assert summary.largest_position_symbol is None
    assert summary.largest_position_value is None
    assert summary.largest_position_concentration_pct == Decimal("0")
