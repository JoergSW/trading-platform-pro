from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from trading_platform.application.market_data.price_history import PriceHistoryState
from trading_platform.composition.composition_root import create_price_history_service
from trading_platform.infrastructure.market_data.json_price_history import (
    JsonPriceHistoryProvider,
)


def _bar_payload() -> dict[str, object]:
    return {
        "observed_at": "2026-07-01T20:00:00Z",
        "open": "100.00",
        "high": "103.00",
        "low": "99.00",
        "close": "102.00",
        "volume": 1000,
    }


def _payload(*, symbol: str = "AAPL", bars: list[object] | None = None) -> object:
    return {
        "source_name": "Local History",
        "timeframe": "1D",
        "series": [
            {
                "symbol": symbol,
                "bars": [_bar_payload()] if bars is None else bars,
            }
        ],
    }


def _write_payload(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_json_provider_loads_selected_ready_series(tmp_path: Path) -> None:
    history_path = tmp_path / "price-history.json"
    _write_payload(history_path, _payload())

    history = JsonPriceHistoryProvider(history_path).load_history("AAPL")

    assert history.state is PriceHistoryState.READY
    assert history.symbol == "AAPL"
    assert history.source_name == "Local History"
    assert history.timeframe == "1D"
    assert len(history.bars) == 1
    assert history.bars[0].observed_at == datetime(2026, 7, 1, 20, tzinfo=UTC)
    assert history.bars[0].close_price == Decimal("102.00")
    assert history.bars[0].volume == 1000


def test_json_provider_returns_no_data_for_missing_or_empty_symbol(
    tmp_path: Path,
) -> None:
    history_path = tmp_path / "price-history.json"
    _write_payload(history_path, _payload(bars=[]))
    provider = JsonPriceHistoryProvider(history_path)

    empty_history = provider.load_history("AAPL")
    missing_history = provider.load_history("MSFT")

    assert empty_history.state is PriceHistoryState.NO_DATA
    assert missing_history.state is PriceHistoryState.NO_DATA
    assert empty_history.source_name == "Local History"
    assert missing_history.symbol == "MSFT"


def test_json_provider_distinguishes_unavailable_and_error(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.json"
    unavailable = JsonPriceHistoryProvider(missing_path).load_history("AAPL")

    invalid_path = tmp_path / "invalid.json"
    invalid_path.write_text("{invalid", encoding="utf-8")
    error = JsonPriceHistoryProvider(invalid_path).load_history("AAPL")

    assert unavailable.state is PriceHistoryState.UNAVAILABLE
    assert "was not found" in unavailable.detail
    assert error.state is PriceHistoryState.ERROR
    assert "invalid JSON" in error.detail


def test_json_provider_rejects_invalid_payload_values(tmp_path: Path) -> None:
    history_path = tmp_path / "price-history.json"
    invalid_bar = _bar_payload()
    invalid_bar["close"] = 102.0
    _write_payload(history_path, _payload(bars=[invalid_bar]))

    history = JsonPriceHistoryProvider(history_path).load_history("AAPL")

    assert history.state is PriceHistoryState.ERROR
    assert "close must be a decimal string" in history.detail


def test_json_provider_rejects_duplicate_symbols_and_non_utc_time(
    tmp_path: Path,
) -> None:
    history_path = tmp_path / "price-history.json"
    payload = _payload()
    assert isinstance(payload, dict)
    payload["series"] = [payload["series"][0], payload["series"][0]]
    _write_payload(history_path, payload)

    duplicate = JsonPriceHistoryProvider(history_path).load_history("AAPL")
    assert duplicate.state is PriceHistoryState.ERROR
    assert "duplicate symbol" in duplicate.detail

    non_utc = _bar_payload()
    non_utc["observed_at"] = "2026-07-01T22:00:00+02:00"
    _write_payload(history_path, _payload(bars=[non_utc]))

    timestamp_error = JsonPriceHistoryProvider(history_path).load_history("AAPL")
    assert timestamp_error.state is PriceHistoryState.ERROR
    assert "must use UTC" in timestamp_error.detail


def test_composition_uses_json_provider_only_for_explicit_path(
    tmp_path: Path,
) -> None:
    history_path = tmp_path / "price-history.json"
    _write_payload(history_path, _payload())

    configured = create_price_history_service(history_path).load_history("AAPL")
    unavailable = create_price_history_service().load_history("AAPL")

    assert configured.state is PriceHistoryState.READY
    assert unavailable.state is PriceHistoryState.UNAVAILABLE
