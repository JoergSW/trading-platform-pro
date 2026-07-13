from __future__ import annotations

import os
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from PySide6.QtWidgets import QApplication, QLabel, QTableWidget

from trading_platform.application.scanner.scanner_results import (
    ScannerResult,
    ScannerResults,
)
from trading_platform.presentation.app.main import create_qt_application
from trading_platform.presentation.workspaces.scanner_workspace import (
    ScannerWorkspaceWidget,
)


@pytest.fixture(scope="module")
def qt_application() -> QApplication:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    return create_qt_application([])


def _label_text(widget: ScannerWorkspaceWidget, object_name: str) -> str:
    label = widget.findChild(QLabel, object_name)
    assert label is not None
    return label.text()


def _ready_results() -> ScannerResults:
    return ScannerResults.ready(
        "Local Scanner",
        (
            ScannerResult(
                symbol="AAPL",
                signal="BREAKOUT",
                score=Decimal("94.5"),
                observed_at=datetime(2026, 7, 13, 14, 0, tzinfo=UTC),
            ),
            ScannerResult(
                symbol="MSFT",
                signal="MOMENTUM",
                score=Decimal("88"),
                observed_at=datetime(2026, 7, 13, 14, 1, tzinfo=UTC),
            ),
        ),
    )


def test_scanner_workspace_defaults_to_unavailable(
    qt_application: QApplication,
) -> None:
    widget = ScannerWorkspaceWidget()
    table = widget.findChild(QTableWidget, "scannerWorkspaceTable")

    assert widget.results == ScannerResults.unavailable()
    assert _label_text(widget, "scannerWorkspaceState") == "UNAVAILABLE"
    assert _label_text(widget, "scannerWorkspaceDataSource") == "NOT CONFIGURED"
    assert _label_text(widget, "scannerWorkspaceResultCount") == "0"
    assert _label_text(widget, "scannerWorkspaceEmpty") == (
        "Scanner results are unavailable."
    )
    assert table is not None
    assert table.rowCount() == 0
    assert not table.isVisible()

    widget.close()


def test_scanner_workspace_renders_ready_rows(
    qt_application: QApplication,
) -> None:
    widget = ScannerWorkspaceWidget(_ready_results())
    table = widget.findChild(QTableWidget, "scannerWorkspaceTable")

    assert _label_text(widget, "scannerWorkspaceState") == "READY"
    assert _label_text(widget, "scannerWorkspaceDataSource") == "Local Scanner"
    assert _label_text(widget, "scannerWorkspaceResultCount") == "2"
    assert table is not None
    assert table.rowCount() == 2
    assert table.item(0, 0).text() == "AAPL"
    assert table.item(0, 1).text() == "BREAKOUT"
    assert table.item(0, 2).text() == "94.5"
    assert table.item(0, 3).text() == "2026-07-13 14:00:00 UTC"
    assert table.item(1, 0).text() == "MSFT"

    widget.close()


def test_scanner_workspace_renders_no_data_without_rows(
    qt_application: QApplication,
) -> None:
    widget = ScannerWorkspaceWidget(ScannerResults.no_data("Local Scanner"))
    table = widget.findChild(QTableWidget, "scannerWorkspaceTable")

    assert _label_text(widget, "scannerWorkspaceState") == "NO DATA"
    assert _label_text(widget, "scannerWorkspaceResultCount") == "0"
    assert _label_text(widget, "scannerWorkspaceEmpty") == (
        "The configured source returned no scanner candidates."
    )
    assert table is not None
    assert table.rowCount() == 0

    widget.close()
