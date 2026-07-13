from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from trading_platform.application.scanner.scanner_results import (
    ScannerResult,
    ScannerResults,
    ScannerResultsService,
    ScannerResultsState,
)


class InvalidProvider:
    def load_results(self) -> object:
        return object()


def _result(
    symbol: str = "AAPL",
    *,
    score: Decimal = Decimal("94.5"),
) -> ScannerResult:
    return ScannerResult(
        symbol=symbol,
        signal="BREAKOUT",
        score=score,
        observed_at=datetime(
            2026,
            7,
            13,
            16,
            0,
            tzinfo=timezone(timedelta(hours=2)),
        ),
    )


def test_scanner_result_normalizes_timestamp_to_utc_and_is_immutable() -> None:
    result = _result()

    assert result.observed_at == datetime(2026, 7, 13, 14, 0, tzinfo=UTC)
    with pytest.raises(FrozenInstanceError):
        result.symbol = "MSFT"  # type: ignore[misc]


def test_ready_results_require_unique_symbols() -> None:
    with pytest.raises(ValueError, match="unique symbols"):
        ScannerResults.ready(
            "Test Scanner",
            (_result(), _result()),
        )


def test_ready_results_preserve_order_and_state() -> None:
    first = _result("AAPL")
    second = _result("MSFT", score=Decimal("88"))

    results = ScannerResults.ready("Test Scanner", (first, second))

    assert results.state is ScannerResultsState.READY
    assert results.source_name == "Test Scanner"
    assert results.results == (first, second)


def test_no_data_and_unavailable_results_are_explicitly_empty() -> None:
    no_data = ScannerResults.no_data("Test Scanner")
    unavailable = ScannerResults.unavailable()

    assert no_data.state is ScannerResultsState.NO_DATA
    assert no_data.results == ()
    assert unavailable.state is ScannerResultsState.UNAVAILABLE
    assert unavailable.source_name is None
    assert unavailable.results == ()


@pytest.mark.parametrize(
    ("symbol", "message"),
    (
        ("aapl", "uppercase"),
        ("AAPL US", "unsupported"),
        (" AAPL", "normalized"),
    ),
)
def test_scanner_result_rejects_invalid_symbols(symbol: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        _result(symbol)


@pytest.mark.parametrize("score", (Decimal("-0.1"), Decimal("100.1")))
def test_scanner_result_rejects_scores_outside_zero_to_one_hundred(
    score: Decimal,
) -> None:
    with pytest.raises(ValueError, match="between 0 and 100"):
        _result(score=score)


def test_scanner_results_service_rejects_invalid_provider_return() -> None:
    service = ScannerResultsService(InvalidProvider())  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="invalid result"):
        service.load_results()
