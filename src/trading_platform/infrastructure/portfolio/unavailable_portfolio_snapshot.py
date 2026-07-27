from __future__ import annotations

from trading_platform.application.portfolio.portfolio_snapshot import (
    PortfolioSnapshotResult,
)


class UnavailablePortfolioSnapshotProvider:
    """Safe adapter used when no portfolio source is explicitly configured."""

    def load_snapshot(self) -> PortfolioSnapshotResult:
        return PortfolioSnapshotResult.unavailable()
