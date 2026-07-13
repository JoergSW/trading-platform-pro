from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta, timezone

import pytest

from trading_platform.application.market_data.market_snapshot import (
    MarketSnapshot,
    MarketSnapshotService,
    MarketSnapshotState,
)
from trading_platform.composition.composition_root import (
    create_market_snapshot_service,
)


class RecordingMarketSnapshotProvider:
    def __init__(self, snapshot: MarketSnapshot) -> None:
        self.snapshot = snapshot
        self.load_count = 0

    def load_snapshot(self) -> MarketSnapshot:
        self.load_count += 1
        return self.snapshot


class InvalidMarketSnapshotProvider:
    def load_snapshot(self) -> object:
        return object()


def test_unavailable_snapshot_preserves_missing_data_as_unavailable() -> None:
    snapshot = MarketSnapshot.unavailable()

    assert snapshot.state is MarketSnapshotState.UNAVAILABLE
    assert snapshot.market_status is None
    assert snapshot.source_name is None
    assert snapshot.observed_at is None
    assert "not estimated or reused" in snapshot.detail


def test_unavailable_snapshot_can_identify_a_configured_source() -> None:
    snapshot = MarketSnapshot.unavailable(
        source_name="Configured Test Feed",
        detail="Configured source is temporarily unavailable.",
    )

    assert snapshot.state is MarketSnapshotState.UNAVAILABLE
    assert snapshot.source_name == "Configured Test Feed"
    assert snapshot.detail == "Configured source is temporarily unavailable."

    with pytest.raises(ValueError, match="source_name must not be blank"):
        MarketSnapshot.unavailable(source_name="   ")

    with pytest.raises(ValueError, match="detail must not be blank"):
        MarketSnapshot.unavailable(detail="   ")


def test_no_data_snapshot_requires_a_known_source() -> None:
    snapshot = MarketSnapshot.no_data("Test Feed")

    assert snapshot.state is MarketSnapshotState.NO_DATA
    assert snapshot.market_status is None
    assert snapshot.source_name == "Test Feed"
    assert snapshot.observed_at is None

    with pytest.raises(ValueError, match="source_name must not be blank"):
        MarketSnapshot.no_data("   ")


def test_ready_snapshot_normalizes_observed_timestamp_to_utc() -> None:
    snapshot = MarketSnapshot.ready(
        market_status="OPEN",
        source_name="Test Feed",
        observed_at=datetime(
            2026,
            7,
            12,
            16,
            45,
            tzinfo=timezone(timedelta(hours=2)),
        ),
    )

    assert snapshot.state is MarketSnapshotState.READY
    assert snapshot.observed_at == datetime(2026, 7, 12, 14, 45, tzinfo=UTC)
    assert snapshot.observed_at is not None
    assert snapshot.observed_at.tzinfo is UTC


def test_ready_snapshot_rejects_naive_timestamp() -> None:
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        MarketSnapshot.ready(
            market_status="OPEN",
            source_name="Test Feed",
            observed_at=datetime(2026, 7, 12, 14, 45),
        )


def test_snapshot_is_immutable() -> None:
    snapshot = MarketSnapshot.unavailable()

    with pytest.raises(FrozenInstanceError):
        snapshot.detail = "changed"


def test_market_snapshot_service_delegates_to_application_port() -> None:
    expected_snapshot = MarketSnapshot.no_data("Test Feed")
    provider = RecordingMarketSnapshotProvider(expected_snapshot)
    service = MarketSnapshotService(provider)

    assert service.load_snapshot() is expected_snapshot
    assert provider.load_count == 1


def test_market_snapshot_service_rejects_invalid_provider_result() -> None:
    service = MarketSnapshotService(InvalidMarketSnapshotProvider())  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="invalid result"):
        service.load_snapshot()


def test_composed_market_snapshot_service_is_safely_unavailable() -> None:
    snapshot = create_market_snapshot_service().load_snapshot()

    assert snapshot == MarketSnapshot.unavailable()
