from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta, timezone

import pytest
from PySide6.QtWidgets import QApplication, QLabel

from trading_platform.application.market_data.market_snapshot import MarketSnapshot
from trading_platform.presentation.app.main import create_qt_application
from trading_platform.presentation.workspaces.market_workspace import (
    MarketWorkspaceWidget,
)


@pytest.fixture(scope="module")
def qt_application() -> QApplication:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    return create_qt_application([])


def _label_text(widget: MarketWorkspaceWidget, object_name: str) -> str:
    label = widget.findChild(QLabel, object_name)
    assert label is not None
    return label.text()


def test_market_workspace_defaults_to_explicit_unavailable_state(
    qt_application: QApplication,
) -> None:
    widget = MarketWorkspaceWidget()

    assert widget.snapshot == MarketSnapshot.unavailable()
    assert _label_text(widget, "marketWorkspaceState") == "UNAVAILABLE"
    assert _label_text(widget, "marketWorkspaceMarketStatus") == "UNAVAILABLE"
    assert _label_text(widget, "marketWorkspaceDataSource") == "NOT CONFIGURED"
    assert _label_text(widget, "marketWorkspaceLastUpdate") == "Never"
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
    )
    widget = MarketWorkspaceWidget(snapshot)

    assert widget.snapshot.observed_at is not None
    assert widget.snapshot.observed_at.tzinfo is UTC
    assert widget.snapshot.observed_at.hour == 14
    assert _label_text(widget, "marketWorkspaceState") == "READY"
    assert _label_text(widget, "marketWorkspaceMarketStatus") == "OPEN"
    assert _label_text(widget, "marketWorkspaceDataSource") == "Test Feed"
    assert _label_text(widget, "marketWorkspaceLastUpdate") == "2026-07-12 14:45:00 UTC"

    widget.close()
