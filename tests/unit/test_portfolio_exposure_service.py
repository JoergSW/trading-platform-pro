from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from trading_platform.application.portfolio.portfolio_snapshot import (
    PortfolioSnapshotResult,
    PortfolioSnapshotState,
)
from trading_platform.application.risk.portfolio_exposure import (
    PortfolioExposureState,
    summarize_portfolio_exposure,
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
        account=PortfolioAccount("LOCAL-ACCOUNT", "USD"),
        positions=positions,
        source_name="Local Portfolio Export",
        observed_at=datetime(2026, 7, 27, 10, 15, tzinfo=UTC),
    )


def test_application_reports_complete_exposure_and_preserves_snapshot_state() -> None:
    snapshot = _snapshot(
        (
            PortfolioPosition(
                "AAPL",
                Decimal("10"),
                current_value=Decimal("1900.00"),
            ),
        )
    )

    result = summarize_portfolio_exposure(
        PortfolioSnapshotResult.stale(snapshot, age_seconds=301)
    )

    assert result.state is PortfolioExposureState.COMPLETE
    assert result.snapshot_state is PortfolioSnapshotState.STALE
    assert result.summary is not None
    assert result.summary.gross_exposure == Decimal("1900.00")
    assert result.source_name == snapshot.source_name


def test_application_reports_incomplete_coverage_explicitly() -> None:
    snapshot = _snapshot(
        (
            PortfolioPosition(
                "AAPL",
                Decimal("10"),
                current_value=Decimal("1900.00"),
            ),
            PortfolioPosition("MSFT", Decimal("5")),
        )
    )

    result = summarize_portfolio_exposure(PortfolioSnapshotResult.ready(snapshot))

    assert result.state is PortfolioExposureState.INCOMPLETE
    assert result.summary is not None
    assert result.summary.valued_position_count == 1
    assert result.summary.total_position_count == 2
    assert "1 of 2" in result.detail
    assert "not estimated" in result.detail


def test_application_reports_known_zero_for_empty_portfolio() -> None:
    snapshot = _snapshot(())

    result = summarize_portfolio_exposure(PortfolioSnapshotResult.empty(snapshot))

    assert result.state is PortfolioExposureState.COMPLETE
    assert result.snapshot_state is PortfolioSnapshotState.EMPTY
    assert result.summary is not None
    assert result.summary.gross_exposure == Decimal("0")
    assert "known zero" in result.detail


def test_application_preserves_unavailable_loading_and_error_boundaries() -> None:
    unavailable = summarize_portfolio_exposure(PortfolioSnapshotResult.unavailable())
    loading = summarize_portfolio_exposure(PortfolioSnapshotResult.loading())
    error = summarize_portfolio_exposure(
        PortfolioSnapshotResult.error("Controlled Portfolio failure.")
    )

    assert unavailable.state is PortfolioExposureState.UNAVAILABLE
    assert unavailable.summary is None
    assert loading.state is PortfolioExposureState.LOADING
    assert loading.summary is None
    assert error.state is PortfolioExposureState.ERROR
    assert error.summary is None
