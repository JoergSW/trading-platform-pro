from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Protocol


class MarketSnapshotState(StrEnum):
    """Application-owned availability state for one market snapshot."""

    READY = "READY"
    NO_DATA = "NO DATA"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class MarketSnapshotMetrics:
    """Optional decimal market metrics with explicit units."""

    spx_index_points: Decimal | None = None
    vix_index_points: Decimal | None = None
    atm_straddle_percent: Decimal | None = None

    def __post_init__(self) -> None:
        _validate_decimal_metric(self.spx_index_points, "spx_index_points")
        _validate_decimal_metric(self.vix_index_points, "vix_index_points")
        _validate_decimal_metric(
            self.atm_straddle_percent,
            "atm_straddle_percent",
        )

    @property
    def has_values(self) -> bool:
        return any(
            value is not None
            for value in (
                self.spx_index_points,
                self.vix_index_points,
                self.atm_straddle_percent,
            )
        )


@dataclass(frozen=True, slots=True)
class MarketSnapshot:
    """Immutable, provider-independent market state for read-only presentation."""

    state: MarketSnapshotState
    market_status: str | None
    source_name: str | None
    observed_at: datetime | None
    detail: str
    metrics: MarketSnapshotMetrics = field(default_factory=MarketSnapshotMetrics)

    def __post_init__(self) -> None:
        if not isinstance(self.state, MarketSnapshotState):
            raise TypeError("state must be a MarketSnapshotState")
        if not isinstance(self.metrics, MarketSnapshotMetrics):
            raise TypeError("metrics must be MarketSnapshotMetrics")
        if not self.detail.strip():
            raise ValueError("detail must not be blank")

        if self.state is MarketSnapshotState.READY:
            _require_text(self.market_status, "market_status")
            _require_text(self.source_name, "source_name")
            if self.observed_at is None:
                raise ValueError("READY snapshots require observed_at")
            if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
                raise ValueError("observed_at must be timezone-aware")
            object.__setattr__(self, "observed_at", self.observed_at.astimezone(UTC))
            return

        if self.metrics.has_values:
            raise ValueError(f"{self.state.value} snapshots must not contain metrics")

        if self.state is MarketSnapshotState.NO_DATA:
            _require_text(self.source_name, "source_name")
            if self.market_status is not None:
                raise ValueError("NO DATA snapshots must not contain market_status")
            if self.observed_at is not None:
                raise ValueError("NO DATA snapshots must not contain observed_at")
            return

        if self.market_status is not None:
            raise ValueError("UNAVAILABLE snapshots must not contain market_status")
        if self.source_name is not None:
            _require_text(self.source_name, "source_name")
        if self.observed_at is not None:
            raise ValueError("UNAVAILABLE snapshots must not contain observed_at")

    @classmethod
    def unavailable(
        cls,
        source_name: str | None = None,
        detail: str | None = None,
    ) -> MarketSnapshot:
        return cls(
            state=MarketSnapshotState.UNAVAILABLE,
            market_status=None,
            source_name=source_name,
            observed_at=None,
            detail=(
                detail
                if detail is not None
                else (
                    "No market data source is configured. Market values are not "
                    "estimated or reused."
                )
            ),
        )

    @classmethod
    def no_data(cls, source_name: str) -> MarketSnapshot:
        return cls(
            state=MarketSnapshotState.NO_DATA,
            market_status=None,
            source_name=source_name,
            observed_at=None,
            detail=(
                "The configured source has not provided market state data. "
                "No fallback value is displayed."
            ),
        )

    @classmethod
    def ready(
        cls,
        market_status: str,
        source_name: str,
        observed_at: datetime,
        metrics: MarketSnapshotMetrics | None = None,
    ) -> MarketSnapshot:
        return cls(
            state=MarketSnapshotState.READY,
            market_status=market_status,
            source_name=source_name,
            observed_at=observed_at,
            detail="Market state data is available from the configured source.",
            metrics=metrics or MarketSnapshotMetrics(),
        )


class MarketSnapshotProvider(Protocol):
    """Application port for loading one provider-independent market snapshot."""

    def load_snapshot(self) -> MarketSnapshot:
        """Load the current read-only market snapshot."""
        ...


class MarketSnapshotService:
    """Application service coordinating snapshot loading through the port."""

    def __init__(self, provider: MarketSnapshotProvider) -> None:
        self._provider = provider

    def load_snapshot(self) -> MarketSnapshot:
        snapshot = self._provider.load_snapshot()
        if not isinstance(snapshot, MarketSnapshot):
            raise TypeError("Market snapshot provider returned an invalid result")
        return snapshot


def _require_text(value: str | None, field_name: str) -> None:
    if value is None or not value.strip():
        raise ValueError(f"{field_name} must not be blank")


def _validate_decimal_metric(value: Decimal | None, field_name: str) -> None:
    if value is None:
        return
    if not isinstance(value, Decimal):
        raise TypeError(f"{field_name} must be Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < Decimal("0"):
        raise ValueError(f"{field_name} must not be negative")
