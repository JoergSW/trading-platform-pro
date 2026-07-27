from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from trading_platform.application.portfolio.portfolio_snapshot import (
    PortfolioSnapshotState,
)
from trading_platform.composition.composition_root import (
    create_portfolio_snapshot_service,
)
from trading_platform.infrastructure.portfolio.json_portfolio_snapshot import (
    JsonPortfolioSnapshotProvider,
)


def _write_payload(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _ready_payload() -> dict[str, object]:
    return {
        "source_name": "Local Portfolio Export",
        "observed_at": "2026-07-27T10:15:00Z",
        "account": {
            "account_reference": "LOCAL-ACCOUNT",
            "currency": "USD",
            "cash": "1000.00",
            "net_liquidation_value": "2500.00",
            "unrealized_pnl": "25.50",
        },
        "positions": [
            {
                "symbol": "MSFT",
                "quantity": "5",
            },
            {
                "symbol": "AAPL",
                "quantity": "10",
                "average_price": "180.25",
                "current_price": "190.10",
                "current_value": "1901.00",
                "unrealized_pnl": "98.50",
            },
        ],
    }


def test_json_provider_loads_exact_decimal_values_and_sorts_positions(
    tmp_path: Path,
) -> None:
    snapshot_path = tmp_path / "portfolio.json"
    _write_payload(snapshot_path, _ready_payload())

    result = JsonPortfolioSnapshotProvider(snapshot_path).load_snapshot()

    assert result.state is PortfolioSnapshotState.READY
    assert result.snapshot is not None
    assert result.snapshot.observed_at == datetime(2026, 7, 27, 10, 15, tzinfo=UTC)
    assert tuple(position.symbol for position in result.snapshot.positions) == (
        "AAPL",
        "MSFT",
    )
    assert result.snapshot.positions[1].average_price is None
    assert result.snapshot.positions[1].current_price is None
    assert result.snapshot.positions[1].current_value is None
    assert result.snapshot.positions[1].unrealized_pnl is None


def test_json_provider_returns_empty_for_valid_account_without_positions(
    tmp_path: Path,
) -> None:
    snapshot_path = tmp_path / "portfolio.json"
    payload = _ready_payload()
    payload["positions"] = []
    _write_payload(snapshot_path, payload)

    result = JsonPortfolioSnapshotProvider(snapshot_path).load_snapshot()

    assert result.state is PortfolioSnapshotState.EMPTY
    assert result.snapshot is not None
    assert result.snapshot.positions == ()
    assert result.snapshot.account.cash is not None


def test_json_provider_reports_missing_file_as_error(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "missing.json"

    result = JsonPortfolioSnapshotProvider(snapshot_path).load_snapshot()

    assert result.state is PortfolioSnapshotState.ERROR
    assert result.source_name == f"JSON file: {snapshot_path}"
    assert "was not found" in result.detail


def test_json_provider_reports_invalid_json_as_error(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "portfolio.json"
    snapshot_path.write_text("{invalid", encoding="utf-8")

    result = JsonPortfolioSnapshotProvider(snapshot_path).load_snapshot()

    assert result.state is PortfolioSnapshotState.ERROR
    assert "invalid JSON" in result.detail


def test_json_provider_rejects_numeric_financial_values(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "portfolio.json"
    payload = _ready_payload()
    account = payload["account"]
    assert isinstance(account, dict)
    account["cash"] = 1000.0
    _write_payload(snapshot_path, payload)

    result = JsonPortfolioSnapshotProvider(snapshot_path).load_snapshot()

    assert result.state is PortfolioSnapshotState.ERROR
    assert "account.cash must be a decimal string" in result.detail


def test_json_provider_rejects_null_instead_of_omitted_optional_value(
    tmp_path: Path,
) -> None:
    snapshot_path = tmp_path / "portfolio.json"
    payload = _ready_payload()
    positions = payload["positions"]
    assert isinstance(positions, list)
    first_position = positions[0]
    assert isinstance(first_position, dict)
    first_position["current_price"] = None
    _write_payload(snapshot_path, payload)

    result = JsonPortfolioSnapshotProvider(snapshot_path).load_snapshot()

    assert result.state is PortfolioSnapshotState.ERROR
    assert "positions[0].current_price must be a decimal string" in result.detail


def test_json_provider_rejects_non_utc_timestamp(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "portfolio.json"
    payload = _ready_payload()
    payload["observed_at"] = "2026-07-27T12:15:00+02:00"
    _write_payload(snapshot_path, payload)

    result = JsonPortfolioSnapshotProvider(snapshot_path).load_snapshot()

    assert result.state is PortfolioSnapshotState.ERROR
    assert "observed_at must use UTC" in result.detail


def test_json_provider_rejects_duplicate_symbols(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "portfolio.json"
    payload = _ready_payload()
    positions = payload["positions"]
    assert isinstance(positions, list)
    positions.append({"symbol": "AAPL", "quantity": "1"})
    _write_payload(snapshot_path, payload)

    result = JsonPortfolioSnapshotProvider(snapshot_path).load_snapshot()

    assert result.state is PortfolioSnapshotState.ERROR
    assert "unique symbols" in result.detail


def test_composition_is_unavailable_without_explicit_path() -> None:
    result = create_portfolio_snapshot_service().load_snapshot()

    assert result.state is PortfolioSnapshotState.UNAVAILABLE
    assert result.snapshot is None
