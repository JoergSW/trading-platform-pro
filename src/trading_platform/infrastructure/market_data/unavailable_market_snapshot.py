from __future__ import annotations

from trading_platform.application.market_data.market_snapshot import MarketSnapshot


class UnavailableMarketSnapshotProvider:
    """Safe infrastructure adapter used until a market-data source is configured."""

    def load_snapshot(self) -> MarketSnapshot:
        return MarketSnapshot.unavailable()
