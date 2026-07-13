from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from trading_platform.application.market_data.market_snapshot import (
    MarketSnapshotState,
)
from trading_platform.composition.composition_root import (
    create_market_snapshot_service,
)
from trading_platform.infrastructure.market_data.json_market_snapshot import (
    JsonMarketSnapshotProvider,
)


def _write_payload(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_json_provider_loads_ready_snapshot_with_utc_timestamp(
    tmp_path: Path,
) -> None:
    snapshot_path = tmp_path / "market-snapshot.json"
    _write_payload(
        snapshot_path,
        {
            "state": "READY",
            "market_status": "OPEN",
            "source_name": "Local Test Feed",
            "observed_at": "2026-07-12T18:15:00Z",
        },
    )

    snapshot = JsonMarketSnapshotProvider(snapshot_path).load_snapshot()

    assert snapshot.state is MarketSnapshotState.READY
    assert snapshot.market_status == "OPEN"
    assert snapshot.source_name == "Local Test Feed"
    assert snapshot.observed_at == datetime(2026, 7, 12, 18, 15, tzinfo=UTC)


def test_json_provider_accepts_explicit_utc_offset(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "market-snapshot.json"
    _write_payload(
        snapshot_path,
        {
            "state": "READY",
            "market_status": "CLOSED",
            "source_name": "Local Test Feed",
            "observed_at": "2026-07-12T18:15:00+00:00",
        },
    )

    snapshot = JsonMarketSnapshotProvider(snapshot_path).load_snapshot()

    assert snapshot.state is MarketSnapshotState.READY
    assert snapshot.observed_at == datetime(2026, 7, 12, 18, 15, tzinfo=UTC)


def test_json_provider_loads_no_data_snapshot(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "market-snapshot.json"
    _write_payload(
        snapshot_path,
        {
            "state": "NO DATA",
            "source_name": "Local Test Feed",
        },
    )

    snapshot = JsonMarketSnapshotProvider(snapshot_path).load_snapshot()

    assert snapshot.state is MarketSnapshotState.NO_DATA
    assert snapshot.source_name == "Local Test Feed"
    assert snapshot.market_status is None
    assert snapshot.observed_at is None


def test_json_provider_loads_explicit_unavailable_snapshot(
    tmp_path: Path,
) -> None:
    snapshot_path = tmp_path / "market-snapshot.json"
    _write_payload(
        snapshot_path,
        {
            "state": "UNAVAILABLE",
            "source_name": "Local Test Feed",
        },
    )

    snapshot = JsonMarketSnapshotProvider(snapshot_path).load_snapshot()

    assert snapshot.state is MarketSnapshotState.UNAVAILABLE
    assert snapshot.source_name == "Local Test Feed"
    assert snapshot.market_status is None
    assert snapshot.observed_at is None
    assert "reports market data as unavailable" in snapshot.detail


def test_json_provider_returns_unavailable_for_missing_file(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "missing.json"

    snapshot = JsonMarketSnapshotProvider(snapshot_path).load_snapshot()

    assert snapshot.state is MarketSnapshotState.UNAVAILABLE
    assert snapshot.source_name == f"JSON file: {snapshot_path}"
    assert "was not found" in snapshot.detail


def test_json_provider_returns_unavailable_for_malformed_json(
    tmp_path: Path,
) -> None:
    snapshot_path = tmp_path / "market-snapshot.json"
    snapshot_path.write_text("{invalid", encoding="utf-8")

    snapshot = JsonMarketSnapshotProvider(snapshot_path).load_snapshot()

    assert snapshot.state is MarketSnapshotState.UNAVAILABLE
    assert snapshot.source_name == f"JSON file: {snapshot_path}"
    assert snapshot.detail == (
        "Configured JSON market snapshot file contains invalid JSON."
    )


def test_json_provider_rejects_non_utc_timestamp(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "market-snapshot.json"
    _write_payload(
        snapshot_path,
        {
            "state": "READY",
            "market_status": "OPEN",
            "source_name": "Local Test Feed",
            "observed_at": "2026-07-12T20:15:00+02:00",
        },
    )

    snapshot = JsonMarketSnapshotProvider(snapshot_path).load_snapshot()

    assert snapshot.state is MarketSnapshotState.UNAVAILABLE
    assert snapshot.source_name == f"JSON file: {snapshot_path}"
    assert "observed_at must use UTC" in snapshot.detail


def test_json_provider_rejects_unexpected_fields(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "market-snapshot.json"
    _write_payload(
        snapshot_path,
        {
            "state": "NO DATA",
            "source_name": "Local Test Feed",
            "market_status": None,
        },
    )

    snapshot = JsonMarketSnapshotProvider(snapshot_path).load_snapshot()

    assert snapshot.state is MarketSnapshotState.UNAVAILABLE
    assert "unexpected fields: market_status" in snapshot.detail


def test_composition_uses_json_provider_only_for_explicit_path(
    tmp_path: Path,
) -> None:
    snapshot_path = tmp_path / "market-snapshot.json"
    _write_payload(
        snapshot_path,
        {
            "state": "NO DATA",
            "source_name": "Configured JSON Feed",
        },
    )

    snapshot = create_market_snapshot_service(snapshot_path).load_snapshot()

    assert snapshot.state is MarketSnapshotState.NO_DATA
    assert snapshot.source_name == "Configured JSON Feed"
