from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Protocol

from trading_platform.domain.portfolio.portfolio_snapshot import PortfolioSnapshot

DEFAULT_PORTFOLIO_SNAPSHOT_STALE_SECONDS = 300


class PortfolioSnapshotState(StrEnum):
    """Application-owned availability state for the Portfolio workspace."""

    UNAVAILABLE = "UNAVAILABLE"
    LOADING = "LOADING"
    EMPTY = "EMPTY"
    READY = "READY"
    STALE = "STALE"
    ERROR = "ERROR"


@dataclass(frozen=True, slots=True)
class PortfolioSnapshotResult:
    """Application result for one read-only portfolio snapshot load."""

    state: PortfolioSnapshotState
    snapshot: PortfolioSnapshot | None
    source_name: str | None
    detail: str

    def __post_init__(self) -> None:
        if not isinstance(self.state, PortfolioSnapshotState):
            raise TypeError("state must be a PortfolioSnapshotState")
        _require_normalized_text(self.detail, "detail", max_length=1_000)
        if self.source_name is not None:
            _require_normalized_text(
                self.source_name,
                "source_name",
                max_length=300,
            )

        if self.state in {
            PortfolioSnapshotState.READY,
            PortfolioSnapshotState.EMPTY,
            PortfolioSnapshotState.STALE,
        }:
            if not isinstance(self.snapshot, PortfolioSnapshot):
                raise TypeError(f"{self.state.value} requires a PortfolioSnapshot")
            if self.source_name != self.snapshot.source_name:
                raise ValueError("source_name must match the PortfolioSnapshot source")
            if (
                self.state is PortfolioSnapshotState.READY
                and not self.snapshot.positions
            ):
                raise ValueError("READY requires at least one position")
            if self.state is PortfolioSnapshotState.EMPTY and self.snapshot.positions:
                raise ValueError("EMPTY must not contain positions")
            return

        if self.snapshot is not None:
            raise ValueError(f"{self.state.value} must not contain a snapshot")

    @classmethod
    def unavailable(
        cls,
        source_name: str | None = None,
        detail: str | None = None,
    ) -> PortfolioSnapshotResult:
        return cls(
            state=PortfolioSnapshotState.UNAVAILABLE,
            snapshot=None,
            source_name=source_name,
            detail=(
                detail
                if detail is not None
                else (
                    "No portfolio snapshot source is configured. Financial values "
                    "are not estimated, calculated or reused."
                )
            ),
        )

    @classmethod
    def loading(cls, source_name: str | None = None) -> PortfolioSnapshotResult:
        return cls(
            state=PortfolioSnapshotState.LOADING,
            snapshot=None,
            source_name=source_name,
            detail="Loading the configured read-only portfolio snapshot.",
        )

    @classmethod
    def empty(cls, snapshot: PortfolioSnapshot) -> PortfolioSnapshotResult:
        return cls(
            state=PortfolioSnapshotState.EMPTY,
            snapshot=snapshot,
            source_name=snapshot.source_name,
            detail=(
                "The configured source contains valid account context and no current "
                "positions."
            ),
        )

    @classmethod
    def ready(cls, snapshot: PortfolioSnapshot) -> PortfolioSnapshotResult:
        return cls(
            state=PortfolioSnapshotState.READY,
            snapshot=snapshot,
            source_name=snapshot.source_name,
            detail="Validated portfolio and position data is available.",
        )

    @classmethod
    def stale(
        cls,
        snapshot: PortfolioSnapshot,
        *,
        age_seconds: int,
    ) -> PortfolioSnapshotResult:
        if isinstance(age_seconds, bool) or not isinstance(age_seconds, int):
            raise TypeError("age_seconds must be an integer")
        if age_seconds < 0:
            raise ValueError("age_seconds must not be negative")
        return cls(
            state=PortfolioSnapshotState.STALE,
            snapshot=snapshot,
            source_name=snapshot.source_name,
            detail=(
                "The portfolio snapshot is stale "
                f"({age_seconds} seconds old). Values remain source-provided and "
                "are not recalculated."
            ),
        )

    @classmethod
    def error(
        cls,
        detail: str,
        source_name: str | None = None,
    ) -> PortfolioSnapshotResult:
        return cls(
            state=PortfolioSnapshotState.ERROR,
            snapshot=None,
            source_name=source_name,
            detail=detail,
        )


class PortfolioSnapshotProvider(Protocol):
    """Application port for one provider-independent portfolio snapshot."""

    def load_snapshot(self) -> PortfolioSnapshotResult:
        """Load the current read-only portfolio snapshot result."""
        ...


class PortfolioSnapshotClock(Protocol):
    """Application port for deterministic UTC freshness assessment."""

    def now_utc(self) -> datetime:
        """Return the current timezone-aware UTC time."""
        ...


class PortfolioSnapshotService:
    """Load and classify one read-only portfolio snapshot."""

    def __init__(
        self,
        provider: PortfolioSnapshotProvider,
        clock: PortfolioSnapshotClock,
        *,
        stale_after_seconds: int = DEFAULT_PORTFOLIO_SNAPSHOT_STALE_SECONDS,
    ) -> None:
        if isinstance(stale_after_seconds, bool) or not isinstance(
            stale_after_seconds,
            int,
        ):
            raise TypeError("stale_after_seconds must be an integer")
        if stale_after_seconds <= 0:
            raise ValueError("stale_after_seconds must be greater than zero")
        self._provider = provider
        self._clock = clock
        self._stale_after_seconds = stale_after_seconds

    def load_snapshot(self) -> PortfolioSnapshotResult:
        result = self._provider.load_snapshot()
        if not isinstance(result, PortfolioSnapshotResult):
            raise TypeError("Portfolio snapshot provider returned an invalid result")
        if result.state not in {
            PortfolioSnapshotState.READY,
            PortfolioSnapshotState.EMPTY,
        }:
            return result

        snapshot = result.snapshot
        if snapshot is None:
            raise RuntimeError("Validated portfolio result is missing its snapshot")
        now = _require_aware_datetime(self._clock.now_utc(), "clock result")
        age_seconds = max(0, int((now - snapshot.observed_at).total_seconds()))
        if age_seconds >= self._stale_after_seconds:
            return PortfolioSnapshotResult.stale(
                snapshot,
                age_seconds=age_seconds,
            )
        return result


def _require_aware_datetime(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_normalized_text(
    value: str,
    field_name: str,
    *,
    max_length: int,
) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{field_name} must be normalized non-blank text")
    if len(value) > max_length:
        raise ValueError(f"{field_name} must not exceed {max_length} characters")
