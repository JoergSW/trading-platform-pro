from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from trading_platform.application.scanner.scanner_result_changes import (
    ScannerResultChange,
    ScannerResultChangeState,
    calculate_scanner_result_changes,
)
from trading_platform.application.scanner.scanner_results import (
    ScannerResult,
    ScannerResults,
)


def _result(
    symbol: str,
    *,
    signal: str = "BREAKOUT",
    score: str = "90",
    minute: int = 0,
) -> ScannerResult:
    return ScannerResult(
        symbol=symbol,
        signal=signal,
        score=Decimal(score),
        observed_at=datetime(2026, 7, 14, 12, minute, tzinfo=UTC),
    )


def test_first_ready_result_set_marks_every_current_row_new() -> None:
    current = ScannerResults.ready(
        "Scanner",
        (_result("AAPL"), _result("MSFT", signal="MOMENTUM")),
    )

    changes = calculate_scanner_result_changes(None, current)

    assert tuple(change.state for change in changes) == (
        ScannerResultChangeState.NEW,
        ScannerResultChangeState.NEW,
    )
    assert all(change.previous_result is None for change in changes)


def test_compares_new_changed_and_unchanged_rows_by_symbol() -> None:
    previous_aapl = _result("AAPL", score="90")
    previous_msft = _result("MSFT", signal="MOMENTUM", score="88", minute=1)
    previous_removed = _result("TSLA", signal="REVERSAL", score="80", minute=2)
    current_aapl = _result("AAPL", score="95")
    current_msft = _result("MSFT", signal="MOMENTUM", score="88", minute=1)
    current_nvda = _result("NVDA", signal="MOMENTUM", score="92", minute=3)
    previous = ScannerResults.ready(
        "Scanner",
        (previous_aapl, previous_msft, previous_removed),
    )
    current = ScannerResults.ready(
        "Scanner",
        (current_aapl, current_msft, current_nvda),
    )

    changes = calculate_scanner_result_changes(previous, current)

    assert changes == (
        ScannerResultChange(
            result=current_aapl,
            state=ScannerResultChangeState.CHANGED,
            previous_result=previous_aapl,
        ),
        ScannerResultChange(
            result=current_msft,
            state=ScannerResultChangeState.UNCHANGED,
            previous_result=previous_msft,
        ),
        ScannerResultChange(
            result=current_nvda,
            state=ScannerResultChangeState.NEW,
        ),
    )
    assert all(change.result.symbol != "TSLA" for change in changes)


@pytest.mark.parametrize(
    "changed_result",
    (
        _result("AAPL", signal="REVERSAL"),
        _result("AAPL", score="91"),
        _result("AAPL", minute=1),
    ),
)
def test_detects_signal_score_and_observation_time_changes(
    changed_result: ScannerResult,
) -> None:
    previous = ScannerResults.ready("Scanner", (_result("AAPL"),))
    current = ScannerResults.ready("Scanner", (changed_result,))

    (change,) = calculate_scanner_result_changes(previous, current)

    assert change.state is ScannerResultChangeState.CHANGED


def test_requires_current_ready_results() -> None:
    with pytest.raises(ValueError, match="current must be READY"):
        calculate_scanner_result_changes(None, ScannerResults.no_data("Scanner"))


def test_requires_previous_ready_results_when_supplied() -> None:
    current = ScannerResults.ready("Scanner", (_result("AAPL"),))

    with pytest.raises(ValueError, match="previous must be READY"):
        calculate_scanner_result_changes(ScannerResults.unavailable(), current)
