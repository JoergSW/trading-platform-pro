from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta, timezone

import pytest
from PySide6.QtWidgets import QApplication, QLabel

from trading_platform.presentation.app.main import create_qt_application
from trading_platform.presentation.workspaces.market_workspace import (
    MarketWorkspaceData,
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

    assert widget.data == MarketWorkspaceData.unavailable()
    assert _label_text(widget, "marketWorkspaceState") == "UNAVAILABLE"
    assert _label_text(widget, "marketWorkspaceMarketStatus") == "UNAVAILABLE"
    assert _label_text(widget, "marketWorkspaceDataSource") == "NOT CONFIGURED"
    assert _label_text(widget, "marketWorkspaceLastUpdate") == "Never"
    assert "not estimated or reused" in _label_text(
        widget,
        "marketWorkspaceDetail",
    )

    widget.close()


def test_market_workspace_displays_no_data_without_fallback_values(
    qt_application: QApplication,
) -> None:
    widget = MarketWorkspaceWidget(MarketWorkspaceData.no_data("Test Feed"))

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
    data = MarketWorkspaceData.ready(
        market_status="OPEN",
        data_source="Test Feed",
        last_update=last_update,
    )
    widget = MarketWorkspaceWidget(data)

    assert widget.data.last_update is not None
    assert widget.data.last_update.astimezone(UTC).hour == 14
    assert _label_text(widget, "marketWorkspaceState") == "READY"
    assert _label_text(widget, "marketWorkspaceMarketStatus") == "OPEN"
    assert _label_text(widget, "marketWorkspaceDataSource") == "Test Feed"
    assert _label_text(widget, "marketWorkspaceLastUpdate") == "2026-07-12 14:45:00 UTC"

    widget.close()
