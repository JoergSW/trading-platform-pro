from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from trading_platform.application.portfolio.portfolio_snapshot import (
    PortfolioSnapshotResult,
    PortfolioSnapshotService,
    PortfolioSnapshotState,
)
from trading_platform.domain.portfolio.portfolio_snapshot import (
    PortfolioAccount,
    PortfolioPosition,
    PortfolioSnapshot,
)


class FixedClock:
    def __init__(self, now: datetime) -> None:
        self.now = now

    def now_utc(self) -> datetime:
        return self.now


class StaticProvider:
    def __init__(self, result: PortfolioSnapshotResult) -> None:
        self.result = result
        self.load_count = 0

    def load_snapshot(self) -> PortfolioSnapshotResult:
        self.load_count += 1
        return self.result


class InvalidProvider:
    def load_snapshot(self) -> object:
        return object()


def _snapshot(*, positions: bool = True) -> PortfolioSnapshot:
    position_values = (
        (
            PortfolioPosition(
                "AAPL",
                Decimal("10"),
                current_value=Decimal("1901.00"),
            ),
        )
        if positions
        else ()
    )
    return PortfolioSnapshot(
        account=PortfolioAccount("LOCAL-ACCOUNT", "USD"),
        positions=position_values,
        source_name="Local Portfolio Export",
        observed_at=datetime(2026, 7, 27, 10, 0, tzinfo=UTC),
    )


def test_service_preserves_fresh_ready_snapshot() -> None:
    result = PortfolioSnapshotResult.ready(_snapshot())
    provider = StaticProvider(result)
    service = PortfolioSnapshotService(
        provider,
        FixedClock(datetime(2026, 7, 27, 10, 4, 59, tzinfo=UTC)),
    )

    assert service.load_snapshot() is result
    assert provider.load_count == 1


def test_service_classifies_snapshot_stale_at_threshold() -> None:
    snapshot = _snapshot()
    service = PortfolioSnapshotService(
        StaticProvider(PortfolioSnapshotResult.ready(snapshot)),
        FixedClock(snapshot.observed_at + timedelta(seconds=300)),
    )

    result = service.load_snapshot()

    assert result.state is PortfolioSnapshotState.STALE
    assert result.snapshot is snapshot
    assert "300 seconds old" in result.detail


def test_service_classifies_empty_snapshot_stale_without_inventing_positions() -> None:
    snapshot = _snapshot(positions=False)
    service = PortfolioSnapshotService(
        StaticProvider(PortfolioSnapshotResult.empty(snapshot)),
        FixedClock(snapshot.observed_at + timedelta(seconds=301)),
    )

    result = service.load_snapshot()

    assert result.state is PortfolioSnapshotState.STALE
    assert result.snapshot is snapshot
    assert result.snapshot.positions == ()


def test_service_does_not_modify_unavailable_or_error_results() -> None:
    now = datetime(2026, 7, 27, 10, 0, tzinfo=UTC)
    unavailable = PortfolioSnapshotResult.unavailable()
    error = PortfolioSnapshotResult.error("Controlled error.")

    assert (
        PortfolioSnapshotService(
            StaticProvider(unavailable), FixedClock(now)
        ).load_snapshot()
        is unavailable
    )
    assert (
        PortfolioSnapshotService(StaticProvider(error), FixedClock(now)).load_snapshot()
        is error
    )


def test_service_rejects_invalid_provider_result() -> None:
    service = PortfolioSnapshotService(
        InvalidProvider(),  # type: ignore[arg-type]
        FixedClock(datetime(2026, 7, 27, 10, 0, tzinfo=UTC)),
    )

    with pytest.raises(TypeError, match="invalid result"):
        service.load_snapshot()


def test_result_state_invariants_are_explicit() -> None:
    snapshot = _snapshot()

    with pytest.raises(ValueError, match="EMPTY must not contain positions"):
        PortfolioSnapshotResult(
            state=PortfolioSnapshotState.EMPTY,
            snapshot=snapshot,
            source_name=snapshot.source_name,
            detail="Invalid empty result.",
        )

    with pytest.raises(ValueError, match="must not contain a snapshot"):
        PortfolioSnapshotResult(
            state=PortfolioSnapshotState.ERROR,
            snapshot=snapshot,
            source_name=snapshot.source_name,
            detail="Invalid error result.",
        )
