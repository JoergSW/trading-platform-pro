from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from trading_platform.application.market_data.market_snapshot import (
    MarketSnapshot,
    MarketSnapshotMetrics,
)
from trading_platform.application.market_data.market_snapshot_history import (
    DEFAULT_MARKET_SNAPSHOT_HISTORY_LIMIT,
    MarketSnapshotHistory,
    MarketSnapshotHistoryEntry,
)
from trading_platform.application.market_data.market_snapshot_metric_deltas import (
    MarketSnapshotMetricDeltas,
)


def _ready_snapshot(
    observed_at: datetime,
    *,
    spx: str | None = None,
    vix: str | None = None,
    atm_straddle: str | None = None,
) -> MarketSnapshot:
    return MarketSnapshot.ready(
        market_status="OPEN",
        source_name="Test Feed",
        observed_at=observed_at,
        metrics=MarketSnapshotMetrics(
            spx_index_points=Decimal(spx) if spx is not None else None,
            vix_index_points=Decimal(vix) if vix is not None else None,
            atm_straddle_percent=(
                Decimal(atm_straddle) if atm_straddle is not None else None
            ),
        ),
    )


def test_history_defaults_to_twenty_entries_and_ignores_non_ready_snapshots() -> None:
    history = MarketSnapshotHistory()

    assert history.max_entries == DEFAULT_MARKET_SNAPSHOT_HISTORY_LIMIT
    assert history.record(MarketSnapshot.no_data("Test Feed")) is None
    assert history.record(MarketSnapshot.unavailable()) is None
    assert history.entries == ()


def test_first_ready_snapshot_has_no_metric_deltas() -> None:
    snapshot = _ready_snapshot(
        datetime(2026, 7, 13, 14, 30, tzinfo=UTC),
        spx="5633.91",
    )
    history = MarketSnapshotHistory()

    entry = history.record(snapshot)

    assert entry == MarketSnapshotHistoryEntry(
        snapshot=snapshot,
        metric_deltas=MarketSnapshotMetricDeltas(),
    )
    assert history.entries == (entry,)


def test_history_calculates_deltas_from_previous_recorded_ready_snapshot() -> None:
    first = _ready_snapshot(
        datetime(2026, 7, 13, 14, 30, tzinfo=UTC),
        spx="5633.91",
        vix="15.25",
        atm_straddle="0.82",
    )
    second = _ready_snapshot(
        datetime(2026, 7, 13, 14, 31, tzinfo=UTC),
        spx="5634.25",
        vix="14.75",
        atm_straddle="0.82",
    )
    history = MarketSnapshotHistory()
    history.record(first)

    entry = history.record(second)

    assert entry is not None
    assert entry.metric_deltas == MarketSnapshotMetricDeltas(
        spx_index_points=Decimal("0.34"),
        vix_index_points=Decimal("-0.50"),
        atm_straddle_percent=Decimal("0.00"),
    )
    assert tuple(item.snapshot for item in history.entries) == (second, first)


def test_history_does_not_duplicate_unchanged_snapshot_content() -> None:
    snapshot = _ready_snapshot(
        datetime(2026, 7, 13, 14, 30, tzinfo=UTC),
        spx="5633.91",
    )
    history = MarketSnapshotHistory()
    first_entry = history.record(snapshot)

    duplicate_entry = history.record(
        _ready_snapshot(
            datetime(2026, 7, 13, 14, 30, tzinfo=UTC),
            spx="5633.91",
        )
    )

    assert duplicate_entry is None
    assert history.entries == (first_entry,)


def test_history_keeps_only_the_newest_configured_number_of_entries() -> None:
    history = MarketSnapshotHistory(max_entries=2)
    start = datetime(2026, 7, 13, 14, 30, tzinfo=UTC)
    snapshots = [
        _ready_snapshot(start + timedelta(minutes=index), spx=str(5600 + index))
        for index in range(3)
    ]

    for snapshot in snapshots:
        history.record(snapshot)

    assert tuple(entry.snapshot for entry in history.entries) == (
        snapshots[2],
        snapshots[1],
    )


@pytest.mark.parametrize("invalid_limit", [0, -1])
def test_history_rejects_non_positive_limits(invalid_limit: int) -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        MarketSnapshotHistory(max_entries=invalid_limit)


def test_history_rejects_boolean_limit() -> None:
    with pytest.raises(TypeError, match="integer"):
        MarketSnapshotHistory(max_entries=True)
