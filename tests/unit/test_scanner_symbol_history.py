from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from trading_platform.application.scanner.scanner_result_changes import (
    ScannerResultChange,
    ScannerResultChangeState,
)
from trading_platform.application.scanner.scanner_results import ScannerResult
from trading_platform.application.scanner.scanner_symbol_history import (
    DEFAULT_SCANNER_SYMBOL_HISTORY_LIMIT,
    ScannerSymbolHistory,
    ScannerSymbolHistoryEntry,
)


def _result(
    symbol: str,
    *,
    score: str = "90",
    observed_at: datetime | None = None,
) -> ScannerResult:
    return ScannerResult(
        symbol=symbol,
        signal="MOMENTUM",
        score=Decimal(score),
        observed_at=observed_at or datetime(2026, 7, 14, 12, 0, tzinfo=UTC),
    )


def _change(
    result: ScannerResult,
    state: ScannerResultChangeState,
    previous_result: ScannerResult | None = None,
) -> ScannerResultChange:
    return ScannerResultChange(
        result=result,
        state=state,
        previous_result=previous_result,
    )


def test_history_defaults_to_twenty_entries_per_symbol() -> None:
    history = ScannerSymbolHistory()

    assert history.max_entries_per_symbol == DEFAULT_SCANNER_SYMBOL_HISTORY_LIMIT
    assert history.entries_for("AAPL") == ()


def test_history_records_each_symbol_independently_newest_first() -> None:
    first_aapl = _result("AAPL", score="90")
    second_aapl = _result(
        "AAPL",
        score="92",
        observed_at=datetime(2026, 7, 14, 12, 1, tzinfo=UTC),
    )
    msft = _result("MSFT", score="88")
    history = ScannerSymbolHistory()

    first_entries = history.record_changes(
        (
            _change(first_aapl, ScannerResultChangeState.NEW),
            _change(msft, ScannerResultChangeState.NEW),
        )
    )
    second_entries = history.record_changes(
        (
            _change(
                second_aapl,
                ScannerResultChangeState.CHANGED,
                first_aapl,
            ),
        )
    )

    assert first_entries == (
        ScannerSymbolHistoryEntry(first_aapl, ScannerResultChangeState.NEW),
        ScannerSymbolHistoryEntry(msft, ScannerResultChangeState.NEW),
    )
    assert second_entries == (
        ScannerSymbolHistoryEntry(second_aapl, ScannerResultChangeState.CHANGED),
    )
    assert history.entries_for("AAPL") == (
        second_entries[0],
        first_entries[0],
    )
    assert history.entries_for("MSFT") == (first_entries[1],)


def test_history_records_unchanged_successful_updates() -> None:
    result = _result("AAPL")
    history = ScannerSymbolHistory()
    history.record_changes((_change(result, ScannerResultChangeState.NEW),))

    history.record_changes(
        (
            _change(
                result,
                ScannerResultChangeState.UNCHANGED,
                result,
            ),
        )
    )

    assert tuple(entry.change_state for entry in history.entries_for("AAPL")) == (
        ScannerResultChangeState.UNCHANGED,
        ScannerResultChangeState.NEW,
    )


def test_history_keeps_only_configured_entries_per_symbol() -> None:
    history = ScannerSymbolHistory(max_entries_per_symbol=2)
    start = datetime(2026, 7, 14, 12, 0, tzinfo=UTC)
    results = [
        _result(
            "AAPL",
            score=str(90 + index),
            observed_at=start + timedelta(minutes=index),
        )
        for index in range(3)
    ]

    history.record_changes((_change(results[0], ScannerResultChangeState.NEW),))
    history.record_changes(
        (
            _change(
                results[1],
                ScannerResultChangeState.CHANGED,
                results[0],
            ),
        )
    )
    history.record_changes(
        (
            _change(
                results[2],
                ScannerResultChangeState.CHANGED,
                results[1],
            ),
        )
    )

    assert tuple(entry.result for entry in history.entries_for("AAPL")) == (
        results[2],
        results[1],
    )


def test_history_rejects_duplicate_symbols_in_one_update() -> None:
    result = _result("AAPL")
    history = ScannerSymbolHistory()

    with pytest.raises(ValueError, match="unique symbols"):
        history.record_changes(
            (
                _change(result, ScannerResultChangeState.NEW),
                _change(result, ScannerResultChangeState.NEW),
            )
        )


@pytest.mark.parametrize("invalid_limit", [0, -1])
def test_history_rejects_non_positive_limits(invalid_limit: int) -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        ScannerSymbolHistory(max_entries_per_symbol=invalid_limit)


def test_history_rejects_boolean_limit() -> None:
    with pytest.raises(TypeError, match="integer"):
        ScannerSymbolHistory(max_entries_per_symbol=True)
