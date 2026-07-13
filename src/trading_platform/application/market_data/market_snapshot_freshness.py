from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

DEFAULT_MARKET_SNAPSHOT_FRESH_SECONDS = 60
DEFAULT_MARKET_SNAPSHOT_STALE_SECONDS = 300


class MarketSnapshotFreshnessState(StrEnum):
    """Application-owned freshness state derived from one observation time."""

    FRESH = "FRESH"
    AGING = "AGING"
    STALE = "STALE"


@dataclass(frozen=True, slots=True)
class MarketSnapshotFreshness:
    """Immutable freshness result for read-only presentation."""

    state: MarketSnapshotFreshnessState
    age_seconds: int


@dataclass(frozen=True, slots=True)
class MarketSnapshotFreshnessPolicy:
    """Classify snapshot age with explicit UTC-based thresholds."""

    fresh_seconds: int = DEFAULT_MARKET_SNAPSHOT_FRESH_SECONDS
    stale_seconds: int = DEFAULT_MARKET_SNAPSHOT_STALE_SECONDS

    def __post_init__(self) -> None:
        _require_positive_int(self.fresh_seconds, "fresh_seconds")
        _require_positive_int(self.stale_seconds, "stale_seconds")
        if self.fresh_seconds >= self.stale_seconds:
            raise ValueError("fresh_seconds must be less than stale_seconds")

    def assess(
        self,
        observed_at: datetime,
        now: datetime,
    ) -> MarketSnapshotFreshness:
        observed_utc = _require_aware_datetime(observed_at, "observed_at")
        now_utc = _require_aware_datetime(now, "now")
        age_seconds = max(0, int((now_utc - observed_utc).total_seconds()))

        if age_seconds < self.fresh_seconds:
            state = MarketSnapshotFreshnessState.FRESH
        elif age_seconds < self.stale_seconds:
            state = MarketSnapshotFreshnessState.AGING
        else:
            state = MarketSnapshotFreshnessState.STALE

        return MarketSnapshotFreshness(state=state, age_seconds=age_seconds)


def _require_positive_int(value: int, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value <= 0:
        raise ValueError(f"{field_name} must be greater than zero")


def _require_aware_datetime(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)
