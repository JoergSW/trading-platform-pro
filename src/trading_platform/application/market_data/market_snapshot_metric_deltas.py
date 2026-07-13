from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from trading_platform.application.market_data.market_snapshot import (
    MarketSnapshot,
    MarketSnapshotState,
)


@dataclass(frozen=True, slots=True)
class MarketSnapshotMetricDeltas:
    """Exact metric changes between two successfully loaded READY snapshots."""

    spx_index_points: Decimal | None = None
    vix_index_points: Decimal | None = None
    atm_straddle_percent: Decimal | None = None

    def __post_init__(self) -> None:
        _validate_optional_decimal(self.spx_index_points, "spx_index_points")
        _validate_optional_decimal(self.vix_index_points, "vix_index_points")
        _validate_optional_decimal(
            self.atm_straddle_percent,
            "atm_straddle_percent",
        )


def calculate_market_snapshot_metric_deltas(
    previous: MarketSnapshot,
    current: MarketSnapshot,
) -> MarketSnapshotMetricDeltas:
    """Subtract the previous metric values from the current metric values."""

    _require_ready_snapshot(previous, "previous")
    _require_ready_snapshot(current, "current")

    return MarketSnapshotMetricDeltas(
        spx_index_points=_subtract_optional(
            current.metrics.spx_index_points,
            previous.metrics.spx_index_points,
        ),
        vix_index_points=_subtract_optional(
            current.metrics.vix_index_points,
            previous.metrics.vix_index_points,
        ),
        atm_straddle_percent=_subtract_optional(
            current.metrics.atm_straddle_percent,
            previous.metrics.atm_straddle_percent,
        ),
    )


def _require_ready_snapshot(snapshot: MarketSnapshot, field_name: str) -> None:
    if not isinstance(snapshot, MarketSnapshot):
        raise TypeError(f"{field_name} must be a MarketSnapshot")
    if snapshot.state is not MarketSnapshotState.READY:
        raise ValueError(f"{field_name} must be a READY snapshot")


def _subtract_optional(
    current: Decimal | None,
    previous: Decimal | None,
) -> Decimal | None:
    if current is None or previous is None:
        return None
    return current - previous


def _validate_optional_decimal(value: Decimal | None, field_name: str) -> None:
    if value is None:
        return
    if not isinstance(value, Decimal):
        raise TypeError(f"{field_name} must be Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
