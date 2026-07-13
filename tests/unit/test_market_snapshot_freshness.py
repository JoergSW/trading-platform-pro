from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import pytest

from trading_platform.application.market_data.market_snapshot_freshness import (
    MarketSnapshotFreshnessPolicy,
    MarketSnapshotFreshnessState,
)


def test_freshness_policy_classifies_explicit_boundaries() -> None:
    policy = MarketSnapshotFreshnessPolicy(fresh_seconds=60, stale_seconds=300)
    now = datetime(2026, 7, 13, 12, 0, tzinfo=UTC)

    fresh = policy.assess(now - timedelta(seconds=59), now)
    aging = policy.assess(now - timedelta(seconds=60), now)
    stale = policy.assess(now - timedelta(seconds=300), now)

    assert fresh.state is MarketSnapshotFreshnessState.FRESH
    assert fresh.age_seconds == 59
    assert aging.state is MarketSnapshotFreshnessState.AGING
    assert aging.age_seconds == 60
    assert stale.state is MarketSnapshotFreshnessState.STALE
    assert stale.age_seconds == 300


def test_freshness_policy_uses_utc_for_age_calculation() -> None:
    policy = MarketSnapshotFreshnessPolicy(fresh_seconds=60, stale_seconds=300)
    observed_at = datetime(
        2026,
        7,
        13,
        13,
        59,
        30,
        tzinfo=timezone(timedelta(hours=2)),
    )
    now = datetime(2026, 7, 13, 12, 0, tzinfo=UTC)

    result = policy.assess(observed_at, now)

    assert result.state is MarketSnapshotFreshnessState.FRESH
    assert result.age_seconds == 30


def test_freshness_policy_clamps_future_observation_age_to_zero() -> None:
    policy = MarketSnapshotFreshnessPolicy(fresh_seconds=60, stale_seconds=300)
    now = datetime(2026, 7, 13, 12, 0, tzinfo=UTC)

    result = policy.assess(now + timedelta(seconds=10), now)

    assert result.state is MarketSnapshotFreshnessState.FRESH
    assert result.age_seconds == 0


@pytest.mark.parametrize(
    ("fresh_seconds", "stale_seconds", "exception_type"),
    [
        (0, 300, ValueError),
        (60, 0, ValueError),
        (300, 300, ValueError),
        (301, 300, ValueError),
        (True, 300, TypeError),
    ],
)
def test_freshness_policy_rejects_invalid_thresholds(
    fresh_seconds: int,
    stale_seconds: int,
    exception_type: type[Exception],
) -> None:
    with pytest.raises(exception_type):
        MarketSnapshotFreshnessPolicy(
            fresh_seconds=fresh_seconds,
            stale_seconds=stale_seconds,
        )


def test_freshness_policy_requires_timezone_aware_datetimes() -> None:
    policy = MarketSnapshotFreshnessPolicy()

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        policy.assess(
            datetime(2026, 7, 13, 12, 0),
            datetime(2026, 7, 13, 12, 1, tzinfo=UTC),
        )
