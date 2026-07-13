from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication, QLabel, QPushButton

from trading_platform.application.market_data.market_snapshot import (
    MarketSnapshot,
    MarketSnapshotMetrics,
    MarketSnapshotService,
)
from trading_platform.presentation.app.main import create_qt_application
from trading_platform.presentation.workspaces.market_workspace import (
    MarketWorkspaceWidget,
)


@pytest.fixture(scope="module")
def qt_application() -> QApplication:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    return create_qt_application([])


class SequenceSnapshotProvider:
    def __init__(self, *snapshots: MarketSnapshot) -> None:
        self._snapshots = list(snapshots)
        self.load_count = 0

    def load_snapshot(self) -> MarketSnapshot:
        self.load_count += 1
        if not self._snapshots:
            raise RuntimeError("No test snapshot remains.")
        return self._snapshots.pop(0)


class FailingSnapshotProvider:
    def load_snapshot(self) -> MarketSnapshot:
        raise RuntimeError("controlled refresh failure")


class MutableNowProvider:
    def __init__(self, current: datetime) -> None:
        self.current = current

    def __call__(self) -> datetime:
        return self.current


def _label_text(widget: MarketWorkspaceWidget, object_name: str) -> str:
    label = widget.findChild(QLabel, object_name)
    assert label is not None
    return label.text()


def _refresh_and_wait(
    widget: MarketWorkspaceWidget,
    timeout_ms: int = 2_000,
) -> None:
    event_loop = QEventLoop()
    completed = False

    def finish() -> None:
        nonlocal completed
        completed = True
        event_loop.quit()

    widget.refresh_finished.connect(finish)
    widget.refresh_snapshot()
    QTimer.singleShot(timeout_ms, event_loop.quit)
    event_loop.exec()

    assert completed
    assert widget.wait_for_refresh()


def test_market_workspace_defaults_to_explicit_unavailable_state(
    qt_application: QApplication,
) -> None:
    widget = MarketWorkspaceWidget()

    refresh_button = widget.findChild(QPushButton, "marketWorkspaceRefreshButton")

    assert widget.snapshot == MarketSnapshot.unavailable()
    assert _label_text(widget, "marketWorkspaceState") == "UNAVAILABLE"
    assert _label_text(widget, "marketWorkspaceMarketStatus") == "UNAVAILABLE"
    assert _label_text(widget, "marketWorkspaceDataSource") == "NOT CONFIGURED"
    assert _label_text(widget, "marketWorkspaceLastUpdate") == "Never"
    assert _label_text(widget, "marketWorkspaceSpx") == "NO DATA"
    assert _label_text(widget, "marketWorkspaceVix") == "NO DATA"
    assert _label_text(widget, "marketWorkspaceAtmStraddle") == "NO DATA"
    assert _label_text(widget, "marketWorkspaceSpxDelta") == "NO DATA"
    assert _label_text(widget, "marketWorkspaceVixDelta") == "NO DATA"
    assert _label_text(widget, "marketWorkspaceAtmStraddleDelta") == "NO DATA"
    assert _label_text(widget, "marketWorkspaceSnapshotAge") == "Not available"
    assert _label_text(widget, "marketWorkspaceFreshness") == "NOT AVAILABLE"
    assert _label_text(widget, "marketWorkspaceRefreshStatus") == "NOT CONFIGURED"
    assert refresh_button is not None
    assert not refresh_button.isEnabled()
    assert "not estimated or reused" in _label_text(
        widget,
        "marketWorkspaceDetail",
    )

    widget.close()


def test_market_workspace_displays_configured_unavailable_source(
    qt_application: QApplication,
) -> None:
    snapshot = MarketSnapshot.unavailable(
        source_name="JSON file: temp/market-snapshot.json",
        detail="Configured JSON market snapshot file contains invalid JSON.",
    )
    widget = MarketWorkspaceWidget(snapshot)

    assert _label_text(widget, "marketWorkspaceState") == "UNAVAILABLE"
    assert _label_text(widget, "marketWorkspaceMarketStatus") == "UNAVAILABLE"
    assert (
        _label_text(widget, "marketWorkspaceDataSource")
        == "JSON file: temp/market-snapshot.json"
    )
    assert _label_text(widget, "marketWorkspaceLastUpdate") == "Never"
    assert "invalid JSON" in _label_text(widget, "marketWorkspaceDetail")

    widget.close()


def test_market_workspace_displays_no_data_without_fallback_values(
    qt_application: QApplication,
) -> None:
    widget = MarketWorkspaceWidget(MarketSnapshot.no_data("Test Feed"))

    assert _label_text(widget, "marketWorkspaceState") == "NO DATA"
    assert _label_text(widget, "marketWorkspaceMarketStatus") == "NO DATA"
    assert _label_text(widget, "marketWorkspaceDataSource") == "Test Feed"
    assert _label_text(widget, "marketWorkspaceLastUpdate") == "Never"
    assert _label_text(widget, "marketWorkspaceSpx") == "NO DATA"
    assert _label_text(widget, "marketWorkspaceVix") == "NO DATA"
    assert _label_text(widget, "marketWorkspaceAtmStraddle") == "NO DATA"
    assert _label_text(widget, "marketWorkspaceSpxDelta") == "NO DATA"
    assert _label_text(widget, "marketWorkspaceVixDelta") == "NO DATA"
    assert _label_text(widget, "marketWorkspaceAtmStraddleDelta") == "NO DATA"
    assert "No fallback value" in _label_text(widget, "marketWorkspaceDetail")

    widget.close()


def test_market_workspace_displays_ready_data_with_utc_timestamp(
    qt_application: QApplication,
) -> None:
    last_update = datetime(
        2026,
        7,
        12,
        16,
        45,
        tzinfo=timezone(timedelta(hours=2)),
    )
    snapshot = MarketSnapshot.ready(
        market_status="OPEN",
        source_name="Test Feed",
        observed_at=last_update,
        metrics=MarketSnapshotMetrics(
            spx_index_points=Decimal("5633.91"),
            vix_index_points=Decimal("15.25"),
            atm_straddle_percent=Decimal("0.82"),
        ),
    )
    widget = MarketWorkspaceWidget(
        snapshot,
        now_provider=lambda: datetime(2026, 7, 12, 14, 45, 45, tzinfo=UTC),
    )

    assert widget.snapshot.observed_at is not None
    assert widget.snapshot.observed_at.tzinfo is UTC
    assert widget.snapshot.observed_at.hour == 14
    assert _label_text(widget, "marketWorkspaceState") == "READY"
    assert _label_text(widget, "marketWorkspaceMarketStatus") == "OPEN"
    assert _label_text(widget, "marketWorkspaceDataSource") == "Test Feed"
    assert _label_text(widget, "marketWorkspaceLastUpdate") == (
        "2026-07-12 14:45:00 UTC"
    )
    assert _label_text(widget, "marketWorkspaceSpx") == "5633.91 index points"
    assert _label_text(widget, "marketWorkspaceVix") == "15.25 index points"
    assert _label_text(widget, "marketWorkspaceAtmStraddle") == "0.82%"
    assert _label_text(widget, "marketWorkspaceSpxDelta") == "NO DATA"
    assert _label_text(widget, "marketWorkspaceVixDelta") == "NO DATA"
    assert _label_text(widget, "marketWorkspaceAtmStraddleDelta") == "NO DATA"
    assert _label_text(widget, "marketWorkspaceSnapshotAge") == "45s"
    assert _label_text(widget, "marketWorkspaceFreshness") == "FRESH"

    widget.close()


def test_market_workspace_displays_missing_ready_metrics_as_no_data(
    qt_application: QApplication,
) -> None:
    widget = MarketWorkspaceWidget(
        MarketSnapshot.ready(
            market_status="OPEN",
            source_name="Test Feed",
            observed_at=datetime(2026, 7, 13, 12, 0, tzinfo=UTC),
            metrics=MarketSnapshotMetrics(
                spx_index_points=Decimal("5633.91"),
            ),
        ),
        now_provider=lambda: datetime(2026, 7, 13, 12, 0, tzinfo=UTC),
    )

    assert _label_text(widget, "marketWorkspaceSpx") == "5633.91 index points"
    assert _label_text(widget, "marketWorkspaceVix") == "NO DATA"
    assert _label_text(widget, "marketWorkspaceAtmStraddle") == "NO DATA"

    widget.close()


def test_market_workspace_updates_freshness_without_reloading_snapshot(
    qt_application: QApplication,
) -> None:
    observed_at = datetime(2026, 7, 13, 12, 0, tzinfo=UTC)
    now_provider = MutableNowProvider(observed_at + timedelta(seconds=30))
    widget = MarketWorkspaceWidget(
        MarketSnapshot.ready(
            market_status="OPEN",
            source_name="Test Feed",
            observed_at=observed_at,
        ),
        fresh_seconds=60,
        stale_seconds=120,
        now_provider=now_provider,
    )
    freshness_label = widget.findChild(QLabel, "marketWorkspaceFreshness")
    freshness_timer = widget.findChild(QTimer, "marketSnapshotFreshnessTimer")

    assert freshness_label is not None
    assert freshness_label.text() == "FRESH"
    assert freshness_label.property("freshnessState") == "fresh"
    assert _label_text(widget, "marketWorkspaceSnapshotAge") == "30s"
    assert freshness_timer is not None
    assert freshness_timer.isActive()
    assert freshness_timer.interval() == 1_000

    now_provider.current = observed_at + timedelta(seconds=90)
    widget.update_freshness()

    assert freshness_label.text() == "AGING"
    assert freshness_label.property("freshnessState") == "aging"
    assert _label_text(widget, "marketWorkspaceSnapshotAge") == "1m 30s"

    now_provider.current = observed_at + timedelta(seconds=120)
    widget.update_freshness()

    assert freshness_label.text() == "STALE"
    assert freshness_label.property("freshnessState") == "stale"
    assert _label_text(widget, "marketWorkspaceSnapshotAge") == "2m 00s"

    widget.close()


def test_manual_refresh_updates_snapshot(
    qt_application: QApplication,
) -> None:
    updated_snapshot = MarketSnapshot.ready(
        market_status="CLOSED",
        source_name="Refreshed Feed",
        observed_at=datetime(2026, 7, 13, 18, 30, tzinfo=UTC),
    )
    provider = SequenceSnapshotProvider(updated_snapshot)
    widget = MarketWorkspaceWidget(
        MarketSnapshot.no_data("Initial Feed"),
        snapshot_service=MarketSnapshotService(provider),
    )

    _refresh_and_wait(widget)

    assert provider.load_count == 1
    assert widget.snapshot is updated_snapshot
    assert _label_text(widget, "marketWorkspaceState") == "READY"
    assert _label_text(widget, "marketWorkspaceMarketStatus") == "CLOSED"
    assert _label_text(widget, "marketWorkspaceDataSource") == "Refreshed Feed"
    assert _label_text(widget, "marketWorkspaceRefreshStatus") == "UPDATED"

    widget.close()


def test_manual_refresh_reports_unchanged_snapshot(
    qt_application: QApplication,
) -> None:
    initial_snapshot = MarketSnapshot.ready(
        market_status="OPEN",
        source_name="Test Feed",
        observed_at=datetime(2026, 7, 13, 14, 30, tzinfo=UTC),
    )
    reloaded_snapshot = MarketSnapshot.ready(
        market_status="OPEN",
        source_name="Test Feed",
        observed_at=datetime(2026, 7, 13, 14, 30, tzinfo=UTC),
    )
    widget = MarketWorkspaceWidget(
        initial_snapshot,
        snapshot_service=MarketSnapshotService(
            SequenceSnapshotProvider(reloaded_snapshot)
        ),
    )

    _refresh_and_wait(widget)

    refresh_status = widget.findChild(
        QLabel,
        "marketWorkspaceRefreshStatus",
    )
    assert widget.snapshot is reloaded_snapshot
    assert _label_text(widget, "marketWorkspaceRefreshStatus") == "UNCHANGED"
    assert refresh_status is not None
    assert refresh_status.property("refreshState") == "unchanged"

    widget.close()


def test_changed_metric_reports_updated_snapshot(
    qt_application: QApplication,
) -> None:
    observed_at = datetime(2026, 7, 13, 14, 30, tzinfo=UTC)
    initial_snapshot = MarketSnapshot.ready(
        market_status="OPEN",
        source_name="Test Feed",
        observed_at=observed_at,
        metrics=MarketSnapshotMetrics(
            spx_index_points=Decimal("5633.91"),
        ),
    )
    updated_snapshot = MarketSnapshot.ready(
        market_status="OPEN",
        source_name="Test Feed",
        observed_at=observed_at,
        metrics=MarketSnapshotMetrics(
            spx_index_points=Decimal("5634.25"),
        ),
    )
    widget = MarketWorkspaceWidget(
        initial_snapshot,
        snapshot_service=MarketSnapshotService(
            SequenceSnapshotProvider(updated_snapshot)
        ),
    )

    _refresh_and_wait(widget)

    assert widget.snapshot is updated_snapshot
    assert _label_text(widget, "marketWorkspaceRefreshStatus") == "UPDATED"
    assert _label_text(widget, "marketWorkspaceSpx") == "5634.25 index points"
    assert _label_text(widget, "marketWorkspaceSpxDelta") == "+0.34 index points"
    assert _label_text(widget, "marketWorkspaceVixDelta") == "NO DATA"
    assert _label_text(widget, "marketWorkspaceAtmStraddleDelta") == "NO DATA"

    widget.close()


def test_metric_deltas_show_positive_negative_and_unchanged_directions(
    qt_application: QApplication,
) -> None:
    observed_at = datetime(2026, 7, 13, 14, 30, tzinfo=UTC)
    initial_snapshot = MarketSnapshot.ready(
        market_status="OPEN",
        source_name="Test Feed",
        observed_at=observed_at,
        metrics=MarketSnapshotMetrics(
            spx_index_points=Decimal("5633.91"),
            vix_index_points=Decimal("15.25"),
            atm_straddle_percent=Decimal("0.82"),
        ),
    )
    updated_snapshot = MarketSnapshot.ready(
        market_status="OPEN",
        source_name="Test Feed",
        observed_at=observed_at + timedelta(seconds=30),
        metrics=MarketSnapshotMetrics(
            spx_index_points=Decimal("5634.25"),
            vix_index_points=Decimal("14.75"),
            atm_straddle_percent=Decimal("0.82"),
        ),
    )
    widget = MarketWorkspaceWidget(
        initial_snapshot,
        snapshot_service=MarketSnapshotService(
            SequenceSnapshotProvider(updated_snapshot)
        ),
    )

    _refresh_and_wait(widget)

    spx_delta = widget.findChild(QLabel, "marketWorkspaceSpxDelta")
    vix_delta = widget.findChild(QLabel, "marketWorkspaceVixDelta")
    atm_delta = widget.findChild(QLabel, "marketWorkspaceAtmStraddleDelta")

    assert spx_delta is not None
    assert spx_delta.text() == "+0.34 index points"
    assert spx_delta.property("metricDeltaDirection") == "positive"
    assert vix_delta is not None
    assert vix_delta.text() == "-0.50 index points"
    assert vix_delta.property("metricDeltaDirection") == "negative"
    assert atm_delta is not None
    assert atm_delta.text() == "0.00% (UNCHANGED)"
    assert atm_delta.property("metricDeltaDirection") == "unchanged"

    widget.close()


def test_metric_delta_requires_values_in_both_successful_snapshots(
    qt_application: QApplication,
) -> None:
    observed_at = datetime(2026, 7, 13, 14, 30, tzinfo=UTC)
    initial_snapshot = MarketSnapshot.ready(
        market_status="OPEN",
        source_name="Test Feed",
        observed_at=observed_at,
        metrics=MarketSnapshotMetrics(
            spx_index_points=Decimal("5633.91"),
        ),
    )
    updated_snapshot = MarketSnapshot.ready(
        market_status="OPEN",
        source_name="Test Feed",
        observed_at=observed_at + timedelta(seconds=30),
        metrics=MarketSnapshotMetrics(
            vix_index_points=Decimal("15.00"),
        ),
    )
    widget = MarketWorkspaceWidget(
        initial_snapshot,
        snapshot_service=MarketSnapshotService(
            SequenceSnapshotProvider(updated_snapshot)
        ),
    )

    _refresh_and_wait(widget)

    assert _label_text(widget, "marketWorkspaceSpxDelta") == "NO DATA"
    assert _label_text(widget, "marketWorkspaceVixDelta") == "NO DATA"
    assert _label_text(widget, "marketWorkspaceAtmStraddleDelta") == "NO DATA"

    widget.close()


def test_changed_observation_time_reports_updated_snapshot(
    qt_application: QApplication,
) -> None:
    initial_snapshot = MarketSnapshot.ready(
        market_status="OPEN",
        source_name="Test Feed",
        observed_at=datetime(2026, 7, 13, 14, 30, tzinfo=UTC),
    )
    updated_snapshot = MarketSnapshot.ready(
        market_status="OPEN",
        source_name="Test Feed",
        observed_at=datetime(2026, 7, 13, 14, 31, tzinfo=UTC),
    )
    widget = MarketWorkspaceWidget(
        initial_snapshot,
        snapshot_service=MarketSnapshotService(
            SequenceSnapshotProvider(updated_snapshot)
        ),
    )

    _refresh_and_wait(widget)

    assert widget.snapshot is updated_snapshot
    assert _label_text(widget, "marketWorkspaceRefreshStatus") == "UPDATED"
    assert _label_text(widget, "marketWorkspaceLastUpdate") == (
        "2026-07-13 14:31:00 UTC"
    )

    widget.close()


def test_refresh_exposes_loading_state_and_ignores_duplicate_action(
    qt_application: QApplication,
) -> None:
    provider = SequenceSnapshotProvider(MarketSnapshot.no_data("Test Feed"))
    widget = MarketWorkspaceWidget(
        MarketSnapshot.unavailable(),
        snapshot_service=MarketSnapshotService(provider),
    )
    refresh_button = widget.findChild(QPushButton, "marketWorkspaceRefreshButton")

    assert refresh_button is not None
    widget.refresh_snapshot()
    widget.refresh_snapshot()

    assert widget.is_refreshing
    assert not refresh_button.isEnabled()
    assert _label_text(widget, "marketWorkspaceRefreshStatus") == "REFRESHING"

    event_loop = QEventLoop()
    widget.refresh_finished.connect(event_loop.quit)
    QTimer.singleShot(2_000, event_loop.quit)
    event_loop.exec()

    assert widget.wait_for_refresh()
    assert provider.load_count == 1
    assert refresh_button.isEnabled()
    assert _label_text(widget, "marketWorkspaceRefreshStatus") == "UPDATED"

    widget.close()


def test_unavailable_refresh_without_previous_data_updates_error_state(
    qt_application: QApplication,
) -> None:
    unavailable_snapshot = MarketSnapshot.unavailable(
        source_name="JSON file: temp/market-snapshot.json",
        detail="Configured JSON market snapshot file was not found.",
    )
    widget = MarketWorkspaceWidget(
        MarketSnapshot.unavailable(),
        snapshot_service=MarketSnapshotService(
            SequenceSnapshotProvider(unavailable_snapshot)
        ),
    )

    _refresh_and_wait(widget)

    assert widget.snapshot is unavailable_snapshot
    assert _label_text(widget, "marketWorkspaceState") == "UNAVAILABLE"
    assert _label_text(widget, "marketWorkspaceRefreshStatus") == "ERROR"
    assert "was not found" in _label_text(widget, "marketWorkspaceDetail")

    widget.close()


def test_unavailable_refresh_retains_previous_snapshot_as_stale(
    qt_application: QApplication,
) -> None:
    initial_snapshot = MarketSnapshot.ready(
        market_status="OPEN",
        source_name="Initial Feed",
        observed_at=datetime(2026, 7, 13, 14, 30, tzinfo=UTC),
    )
    unavailable_snapshot = MarketSnapshot.unavailable(
        source_name="JSON file: temp/market-snapshot.json",
        detail="Configured JSON market snapshot file contains invalid JSON.",
    )
    widget = MarketWorkspaceWidget(
        initial_snapshot,
        snapshot_service=MarketSnapshotService(
            SequenceSnapshotProvider(unavailable_snapshot)
        ),
    )

    _refresh_and_wait(widget)

    assert widget.snapshot is initial_snapshot
    assert _label_text(widget, "marketWorkspaceState") == "STALE"
    assert _label_text(widget, "marketWorkspaceMarketStatus") == "OPEN"
    assert _label_text(widget, "marketWorkspaceDataSource") == "Initial Feed"
    assert _label_text(widget, "marketWorkspaceLastUpdate") == (
        "2026-07-13 14:30:00 UTC"
    )
    assert _label_text(widget, "marketWorkspaceRefreshStatus") == "ERROR"
    assert "Previous snapshot retained and may be stale" in _label_text(
        widget,
        "marketWorkspaceDetail",
    )

    widget.close()


def test_refresh_exception_retains_previous_snapshot_as_stale(
    qt_application: QApplication,
) -> None:
    initial_snapshot = MarketSnapshot.no_data("Initial Feed")
    widget = MarketWorkspaceWidget(
        initial_snapshot,
        snapshot_service=MarketSnapshotService(FailingSnapshotProvider()),
    )

    _refresh_and_wait(widget)

    assert widget.snapshot is initial_snapshot
    assert _label_text(widget, "marketWorkspaceState") == "STALE"
    assert _label_text(widget, "marketWorkspaceRefreshStatus") == "ERROR"
    assert "RuntimeError" in _label_text(widget, "marketWorkspaceDetail")

    widget.close()


def test_auto_refresh_timer_uses_explicit_interval(
    qt_application: QApplication,
) -> None:
    widget = MarketWorkspaceWidget(
        MarketSnapshot.no_data("Initial Feed"),
        snapshot_service=MarketSnapshotService(
            SequenceSnapshotProvider(MarketSnapshot.no_data("Updated Feed"))
        ),
        auto_refresh_seconds=5,
    )
    timer = widget.findChild(QTimer, "marketSnapshotAutoRefreshTimer")

    assert widget.auto_refresh_seconds == 5
    assert timer is not None
    assert timer.isActive()
    assert timer.interval() == 5_000
    assert _label_text(widget, "marketWorkspaceRefreshStatus") == "AUTO 5s"

    widget.close()
