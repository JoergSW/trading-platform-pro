from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from trading_platform.application.scanner.scanner_results import ScannerResultsState
from trading_platform.infrastructure.scanner.json_scanner_results import (
    JsonScannerResultsProvider,
)


def _ready_payload() -> dict[str, object]:
    return {
        "state": "READY",
        "source_name": "Local Scanner",
        "results": [
            {
                "symbol": "AAPL",
                "signal": "BREAKOUT",
                "score": "94.5",
                "observed_at": "2026-07-13T14:00:00Z",
            },
            {
                "symbol": "MSFT",
                "signal": "MOMENTUM",
                "score": "88",
                "observed_at": "2026-07-13T14:01:00+00:00",
            },
        ],
    }


def _write(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_json_scanner_provider_loads_valid_ready_results(tmp_path: Path) -> None:
    results_path = tmp_path / "scanner-results.json"
    _write(results_path, _ready_payload())

    results = JsonScannerResultsProvider(results_path).load_results()

    assert results.state is ScannerResultsState.READY
    assert results.source_name == "Local Scanner"
    assert tuple(result.symbol for result in results.results) == ("AAPL", "MSFT")
    assert results.results[0].score == Decimal("94.5")
    assert results.results[0].observed_at == datetime(2026, 7, 13, 14, 0, tzinfo=UTC)


@pytest.mark.parametrize("state", ("NO DATA", "UNAVAILABLE"))
def test_json_scanner_provider_loads_explicit_empty_states(
    tmp_path: Path,
    state: str,
) -> None:
    results_path = tmp_path / "scanner-results.json"
    _write(
        results_path,
        {"state": state, "source_name": "Local Scanner"},
    )

    results = JsonScannerResultsProvider(results_path).load_results()

    assert results.state.value == state
    assert results.results == ()


def test_json_scanner_provider_returns_unavailable_for_missing_file(
    tmp_path: Path,
) -> None:
    results_path = tmp_path / "missing.json"

    results = JsonScannerResultsProvider(results_path).load_results()

    assert results.state is ScannerResultsState.UNAVAILABLE
    assert str(results_path) in (results.source_name or "")
    assert "not found" in results.detail


def test_json_scanner_provider_returns_unavailable_for_invalid_json(
    tmp_path: Path,
) -> None:
    results_path = tmp_path / "scanner-results.json"
    results_path.write_text("{invalid", encoding="utf-8")

    results = JsonScannerResultsProvider(results_path).load_results()

    assert results.state is ScannerResultsState.UNAVAILABLE
    assert "invalid JSON" in results.detail


@pytest.mark.parametrize(
    ("mutator", "message"),
    (
        (
            lambda payload: payload["results"][0].update({"score": 94.5}),  # type: ignore[index,union-attr]
            "decimal string",
        ),
        (
            lambda payload: payload["results"][0].update(  # type: ignore[index,union-attr]
                {"observed_at": "2026-07-13T16:00:00+02:00"}
            ),
            "must use UTC",
        ),
        (
            lambda payload: payload.update({"unexpected": True}),
            "unexpected fields",
        ),
        (
            lambda payload: payload["results"].append(  # type: ignore[union-attr]
                dict(payload["results"][0])  # type: ignore[index]
            ),
            "unique symbols",
        ),
    ),
)
def test_json_scanner_provider_rejects_invalid_payloads(
    tmp_path: Path,
    mutator: object,
    message: str,
) -> None:
    results_path = tmp_path / "scanner-results.json"
    payload = _ready_payload()
    mutator(payload)  # type: ignore[operator]
    _write(results_path, payload)

    results = JsonScannerResultsProvider(results_path).load_results()

    assert results.state is ScannerResultsState.UNAVAILABLE
    assert message in results.detail
