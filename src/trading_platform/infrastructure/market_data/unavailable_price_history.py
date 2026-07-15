from __future__ import annotations

from trading_platform.application.market_data.price_history import PriceHistory


class UnavailablePriceHistoryProvider:
    """Safe read-only adapter used until a history source is configured."""

    def load_history(self, symbol: str) -> PriceHistory:
        return PriceHistory.unavailable(symbol)
