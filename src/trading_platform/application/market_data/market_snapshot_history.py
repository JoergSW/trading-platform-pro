from __future__ import annotations

from dataclasses import dataclass

from trading_platform.application.market_data.market_snapshot import (
    MarketSnapshot,
    MarketSnapshotState,
)
from trading_platform.application.market_data.market_snapshot_metric_deltas import (
    MarketSnapshotMetricDeltas,
    calculate_market_snapshot_metric_deltas,
)

DEFAULT_MARKET_SNAPSHOT_HISTORY_LIMIT = 20


@dataclass(frozen=True, slots=True)
class MarketSnapshotHistoryEntry:
    """One successful READY snapshot and its change from the prior entry."""

    snapshot: MarketSnapshot
    metric_deltas: MarketSnapshotMetricDeltas

    def __post_init__(self) -> None:
        if not isinstance(self.snapshot, MarketSnapshot):
            raise TypeError("snapshot must be a MarketSnapshot")
        if self.snapshot.state is not MarketSnapshotState.READY:
            raise ValueError("snapshot history entries require READY snapshots")
        if not isinstance(self.metric_deltas, MarketSnapshotMetricDeltas):
            raise TypeError("metric_deltas must be MarketSnapshotMetricDeltas")


class MarketSnapshotHistory:
    """Bounded in-memory history of distinct successful READY snapshots."""

    def __init__(
        self,
        max_entries: int = DEFAULT_MARKET_SNAPSHOT_HISTORY_LIMIT,
    ) -> None:
        if isinstance(max_entries, bool) or not isinstance(max_entries, int):
            raise TypeError("max_entries must be an integer")
        if max_entries <= 0:
            raise ValueError("max_entries must be greater than zero")

        self._max_entries = max_entries
        self._entries: list[MarketSnapshotHistoryEntry] = []

    @property
    def max_entries(self) -> int:
        return self._max_entries

    @property
    def entries(self) -> tuple[MarketSnapshotHistoryEntry, ...]:
        """Return newest entries first."""

        return tuple(self._entries)

    def record(self, snapshot: MarketSnapshot) -> MarketSnapshotHistoryEntry | None:
        """Record a distinct READY snapshot and return the new entry."""

        if not isinstance(snapshot, MarketSnapshot):
            raise TypeError("snapshot must be a MarketSnapshot")
        if snapshot.state is not MarketSnapshotState.READY:
            return None
        if self._entries and _snapshots_have_same_content(
            self._entries[0].snapshot,
            snapshot,
        ):
            return None

        metric_deltas = MarketSnapshotMetricDeltas()
        if self._entries:
            metric_deltas = calculate_market_snapshot_metric_deltas(
                self._entries[0].snapshot,
                snapshot,
            )

        entry = MarketSnapshotHistoryEntry(
            snapshot=snapshot,
            metric_deltas=metric_deltas,
        )
        self._entries.insert(0, entry)
        del self._entries[self._max_entries :]
        return entry


def _snapshots_have_same_content(
    previous: MarketSnapshot,
    current: MarketSnapshot,
) -> bool:
    return (
        previous.state,
        previous.market_status,
        previous.source_name,
        previous.observed_at,
        previous.metrics,
    ) == (
        current.state,
        current.market_status,
        current.source_name,
        current.observed_at,
        current.metrics,
    )
