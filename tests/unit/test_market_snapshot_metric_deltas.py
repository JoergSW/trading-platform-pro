from datetime import UTC, datetime
from decimal import Decimal

import pytest

from trading_platform.application.market_data.market_snapshot import (
    MarketSnapshot,
    MarketSnapshotMetrics,
)
from trading_platform.application.market_data.market_snapshot_metric_deltas import (
    MarketSnapshotMetricDeltas,
    calculate_market_snapshot_metric_deltas,
)


def _ready_snapshot(
    *,
    spx: Decimal | None = None,
    vix: Decimal | None = None,
    atm_straddle: Decimal | None = None,
) -> MarketSnapshot:
    return MarketSnapshot.ready(
        market_status="OPEN",
        source_name="Test Feed",
        observed_at=datetime(2026, 7, 13, 14, 30, tzinfo=UTC),
        metrics=MarketSnapshotMetrics(
            spx_index_points=spx,
            vix_index_points=vix,
            atm_straddle_percent=atm_straddle,
        ),
    )


def test_calculates_positive_negative_and_zero_metric_deltas() -> None:
    previous = _ready_snapshot(
        spx=Decimal("5633.91"),
        vix=Decimal("15.25"),
        atm_straddle=Decimal("0.82"),
    )
    current = _ready_snapshot(
        spx=Decimal("5634.25"),
        vix=Decimal("14.75"),
        atm_straddle=Decimal("0.82"),
    )

    result = calculate_market_snapshot_metric_deltas(previous, current)

    assert result == MarketSnapshotMetricDeltas(
        spx_index_points=Decimal("0.34"),
        vix_index_points=Decimal("-0.50"),
        atm_straddle_percent=Decimal("0.00"),
    )


def test_missing_value_in_either_snapshot_keeps_delta_unavailable() -> None:
    previous = _ready_snapshot(
        spx=Decimal("5633.91"),
        vix=None,
        atm_straddle=Decimal("0.82"),
    )
    current = _ready_snapshot(
        spx=None,
        vix=Decimal("15.00"),
        atm_straddle=Decimal("0.90"),
    )

    result = calculate_market_snapshot_metric_deltas(previous, current)

    assert result.spx_index_points is None
    assert result.vix_index_points is None
    assert result.atm_straddle_percent == Decimal("0.08")


@pytest.mark.parametrize(
    ("previous", "current", "message"),
    (
        (MarketSnapshot.no_data("Test Feed"), _ready_snapshot(), "previous"),
        (_ready_snapshot(), MarketSnapshot.unavailable(), "current"),
    ),
)
def test_requires_two_ready_snapshots(
    previous: MarketSnapshot,
    current: MarketSnapshot,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        calculate_market_snapshot_metric_deltas(previous, current)


def test_metric_delta_contract_rejects_non_decimal_values() -> None:
    with pytest.raises(TypeError, match="spx_index_points must be Decimal"):
        MarketSnapshotMetricDeltas(spx_index_points=1)  # type: ignore[arg-type]


def test_metric_delta_contract_rejects_non_finite_values() -> None:
    with pytest.raises(ValueError, match="vix_index_points must be finite"):
        MarketSnapshotMetricDeltas(vix_index_points=Decimal("NaN"))
