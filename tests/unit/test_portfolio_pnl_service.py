from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from trading_platform.application.portfolio.portfolio_pnl import (
    PortfolioPnlState,
    summarize_portfolio_pnl,
)
from trading_platform.application.portfolio.portfolio_snapshot import (
    PortfolioSnapshotResult,
    PortfolioSnapshotState,
)
from trading_platform.domain.portfolio.portfolio_snapshot import (
    PortfolioAccount,
    PortfolioPosition,
    PortfolioSnapshot,
)


def _snapshot(
    positions: tuple[PortfolioPosition, ...],
) -> PortfolioSnapshot:
    return PortfolioSnapshot(
        account=PortfolioAccount(
            "LOCAL-ACCOUNT",
            "USD",
            unrealized_pnl=Decimal("500.00"),
        ),
        positions=positions,
        source_name="Local Portfolio Export",
        observed_at=datetime(2026, 7, 31, 7, 15, tzinfo=UTC),
    )


def test_application_reports_complete_pnl_and_preserves_stale_snapshot_state() -> None:
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
        )
    )

    result = summarize_portfolio_pnl(
        PortfolioSnapshotResult.stale(snapshot, age_seconds=301)
    )

    assert result.state is PortfolioPnlState.COMPLETE
    assert result.snapshot_state is PortfolioSnapshotState.STALE
    assert result.summary is not None
    assert result.summary.net_unrealized_pnl == Decimal("58.25")
    assert result.source_name == snapshot.source_name
    assert "Account Unrealized P&L remains a separate source field" in result.detail


def test_application_reports_incomplete_pnl_coverage_explicitly() -> None:
    snapshot = _snapshot(
        (
            PortfolioPosition(
                "AAPL",
                Decimal("10"),
                unrealized_pnl=Decimal("98.50"),
            ),
            PortfolioPosition(
                "MSFT",
                Decimal("5"),
                current_price=Decimal("450.00"),
                current_value=Decimal("2250.00"),
            ),
        )
    )

    result = summarize_portfolio_pnl(PortfolioSnapshotResult.ready(snapshot))

    assert result.state is PortfolioPnlState.INCOMPLETE
    assert result.summary is not None
    assert result.summary.reported_position_count == 1
    assert result.summary.total_position_count == 2
    assert "1 of 2" in result.detail
    assert "not estimated" in result.detail
    assert "not estimated or reconciled" in result.detail


def test_application_reports_known_zero_pnl_for_empty_portfolio() -> None:
    snapshot = _snapshot(())

    result = summarize_portfolio_pnl(PortfolioSnapshotResult.empty(snapshot))

    assert result.state is PortfolioPnlState.COMPLETE
    assert result.snapshot_state is PortfolioSnapshotState.EMPTY
    assert result.summary is not None
    assert result.summary.net_unrealized_pnl == Decimal("0")
    assert "known zero" in result.detail


def test_application_maps_snapshot_unavailability_loading_and_error() -> None:
    unavailable = summarize_portfolio_pnl(PortfolioSnapshotResult.unavailable())
    loading = summarize_portfolio_pnl(PortfolioSnapshotResult.loading("Local Export"))
    error = summarize_portfolio_pnl(
        PortfolioSnapshotResult.error("Controlled failure.", "Local Export")
    )

    assert unavailable.state is PortfolioPnlState.UNAVAILABLE
    assert unavailable.summary is None
    assert loading.state is PortfolioPnlState.LOADING
    assert loading.summary is None
    assert error.state is PortfolioPnlState.ERROR
    assert error.summary is None
