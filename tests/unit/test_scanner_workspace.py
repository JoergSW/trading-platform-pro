from __future__ import annotations

import os
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QTableWidget

from trading_platform.application.scanner.scanner_results import (
    ScannerResult,
    ScannerResults,
    ScannerResultsService,
)
from trading_platform.presentation.app.main import create_qt_application
from trading_platform.presentation.workspaces.scanner_workspace import (
    ScannerWorkspaceWidget,
)


@pytest.fixture(scope="module")
def qt_application() -> QApplication:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    return create_qt_application([])


class SequenceScannerResultsProvider:
    def __init__(self, *results: ScannerResults) -> None:
        self._results = results
        self.load_count = 0

    def load_results(self) -> ScannerResults:
        if not self._results:
            raise RuntimeError("No scanner results configured for test provider")
        index = min(self.load_count, len(self._results) - 1)
        self.load_count += 1
        return self._results[index]


class FailingScannerResultsProvider:
    def load_results(self) -> ScannerResults:
        raise RuntimeError("controlled scanner refresh failure")


def _label_text(widget: ScannerWorkspaceWidget, object_name: str) -> str:
    label = widget.findChild(QLabel, object_name)
    assert label is not None
    return label.text()


def _ready_results(
    *,
    source_name: str = "Local Scanner",
    first_score: str = "94.5",
    first_observed_at: datetime | None = None,
) -> ScannerResults:
    observed_at = first_observed_at or datetime(2026, 7, 13, 14, 0, tzinfo=UTC)
    return ScannerResults.ready(
        source_name,
        (
            ScannerResult(
                symbol="AAPL",
                signal="BREAKOUT",
                score=Decimal(first_score),
                observed_at=observed_at,
            ),
            ScannerResult(
                symbol="MSFT",
                signal="MOMENTUM",
                score=Decimal("88"),
                observed_at=datetime(2026, 7, 13, 14, 1, tzinfo=UTC),
            ),
        ),
    )


def _refresh_and_wait(widget: ScannerWorkspaceWidget) -> None:
    event_loop = QEventLoop()
    widget.refresh_finished.connect(event_loop.quit)
    widget.refresh_results()
    QTimer.singleShot(2_000, event_loop.quit)
    event_loop.exec()
    assert widget.wait_for_refresh()


def test_scanner_workspace_defaults_to_unavailable(
    qt_application: QApplication,
) -> None:
    widget = ScannerWorkspaceWidget()
    table = widget.findChild(QTableWidget, "scannerWorkspaceTable")
    refresh_button = widget.findChild(QPushButton, "scannerWorkspaceRefreshButton")

    assert widget.results == ScannerResults.unavailable()
    assert _label_text(widget, "scannerWorkspaceState") == "UNAVAILABLE"
    assert _label_text(widget, "scannerWorkspaceDataSource") == "NOT CONFIGURED"
    assert _label_text(widget, "scannerWorkspaceResultCount") == "0"
    assert _label_text(widget, "scannerWorkspaceRefreshStatus") == "NOT CONFIGURED"
    assert _label_text(widget, "scannerWorkspaceEmpty") == (
        "Scanner results are unavailable."
    )
    assert refresh_button is not None
    assert not refresh_button.isEnabled()
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


def test_manual_refresh_updates_scanner_results(
    qt_application: QApplication,
) -> None:
    updated_results = _ready_results(
        source_name="Refreshed Scanner",
        first_score="96.25",
        first_observed_at=datetime(2026, 7, 13, 14, 5, tzinfo=UTC),
    )
    provider = SequenceScannerResultsProvider(updated_results)
    widget = ScannerWorkspaceWidget(
        ScannerResults.no_data("Initial Scanner"),
        results_service=ScannerResultsService(provider),
    )

    _refresh_and_wait(widget)

    assert provider.load_count == 1
    assert widget.results is updated_results
    assert _label_text(widget, "scannerWorkspaceState") == "READY"
    assert _label_text(widget, "scannerWorkspaceDataSource") == "Refreshed Scanner"
    assert _label_text(widget, "scannerWorkspaceResultCount") == "2"
    assert _label_text(widget, "scannerWorkspaceRefreshStatus") == "UPDATED"
    table = widget.findChild(QTableWidget, "scannerWorkspaceTable")
    assert table is not None
    assert table.item(0, 2).text() == "96.25"

    widget.close()


def test_manual_refresh_reports_unchanged_results(
    qt_application: QApplication,
) -> None:
    initial_results = _ready_results()
    reloaded_results = _ready_results()
    widget = ScannerWorkspaceWidget(
        initial_results,
        results_service=ScannerResultsService(
            SequenceScannerResultsProvider(reloaded_results)
        ),
    )

    _refresh_and_wait(widget)

    refresh_status = widget.findChild(QLabel, "scannerWorkspaceRefreshStatus")
    assert widget.results is reloaded_results
    assert _label_text(widget, "scannerWorkspaceRefreshStatus") == "UNCHANGED"
    assert refresh_status is not None
    assert refresh_status.property("refreshState") == "unchanged"

    widget.close()


def test_refresh_exposes_loading_state_and_ignores_duplicate_action(
    qt_application: QApplication,
) -> None:
    provider = SequenceScannerResultsProvider(ScannerResults.no_data("Scanner"))
    widget = ScannerWorkspaceWidget(
        ScannerResults.unavailable(),
        results_service=ScannerResultsService(provider),
    )
    refresh_button = widget.findChild(QPushButton, "scannerWorkspaceRefreshButton")
    event_loop = QEventLoop()
    widget.refresh_finished.connect(event_loop.quit)

    assert refresh_button is not None
    widget.refresh_results()
    widget.refresh_results()

    assert widget.is_refreshing
    assert not refresh_button.isEnabled()
    assert _label_text(widget, "scannerWorkspaceRefreshStatus") == "REFRESHING"

    QTimer.singleShot(2_000, event_loop.quit)
    event_loop.exec()

    assert widget.wait_for_refresh()
    assert provider.load_count == 1
    assert refresh_button.isEnabled()
    assert _label_text(widget, "scannerWorkspaceRefreshStatus") == "UPDATED"

    widget.close()


def test_unavailable_refresh_without_previous_results_updates_error_state(
    qt_application: QApplication,
) -> None:
    unavailable_results = ScannerResults.unavailable(
        source_name="JSON file: temp/scanner-results.json",
        detail="Configured JSON scanner results file was not found.",
    )
    widget = ScannerWorkspaceWidget(
        ScannerResults.unavailable(),
        results_service=ScannerResultsService(
            SequenceScannerResultsProvider(unavailable_results)
        ),
    )

    _refresh_and_wait(widget)

    assert widget.results is unavailable_results
    assert _label_text(widget, "scannerWorkspaceState") == "UNAVAILABLE"
    assert _label_text(widget, "scannerWorkspaceRefreshStatus") == "ERROR"
    assert "was not found" in _label_text(widget, "scannerWorkspaceDetail")

    widget.close()


def test_unavailable_refresh_retains_previous_results_as_stale(
    qt_application: QApplication,
) -> None:
    initial_results = _ready_results()
    unavailable_results = ScannerResults.unavailable(
        source_name="JSON file: temp/scanner-results.json",
        detail="Configured JSON scanner results file contains invalid JSON.",
    )
    widget = ScannerWorkspaceWidget(
        initial_results,
        results_service=ScannerResultsService(
            SequenceScannerResultsProvider(unavailable_results)
        ),
    )

    _refresh_and_wait(widget)

    assert widget.results is initial_results
    assert _label_text(widget, "scannerWorkspaceState") == "STALE"
    assert _label_text(widget, "scannerWorkspaceDataSource") == "Local Scanner"
    assert _label_text(widget, "scannerWorkspaceResultCount") == "2"
    assert _label_text(widget, "scannerWorkspaceRefreshStatus") == "ERROR"
    assert "Previous results retained and may be stale" in _label_text(
        widget,
        "scannerWorkspaceDetail",
    )
    table = widget.findChild(QTableWidget, "scannerWorkspaceTable")
    assert table is not None
    assert table.rowCount() == 2

    widget.close()


def test_refresh_exception_retains_previous_results_as_stale(
    qt_application: QApplication,
) -> None:
    initial_results = ScannerResults.no_data("Initial Scanner")
    widget = ScannerWorkspaceWidget(
        initial_results,
        results_service=ScannerResultsService(FailingScannerResultsProvider()),
    )

    _refresh_and_wait(widget)

    assert widget.results is initial_results
    assert _label_text(widget, "scannerWorkspaceState") == "STALE"
    assert _label_text(widget, "scannerWorkspaceRefreshStatus") == "ERROR"
    assert "RuntimeError" in _label_text(widget, "scannerWorkspaceDetail")

    widget.close()


def test_auto_refresh_timer_uses_explicit_interval(
    qt_application: QApplication,
) -> None:
    widget = ScannerWorkspaceWidget(
        ScannerResults.no_data("Initial Scanner"),
        results_service=ScannerResultsService(
            SequenceScannerResultsProvider(ScannerResults.no_data("Updated Scanner"))
        ),
        auto_refresh_seconds=5,
    )
    timer = widget.findChild(QTimer, "scannerResultsAutoRefreshTimer")

    assert widget.auto_refresh_seconds == 5
    assert timer is not None
    assert timer.isActive()
    assert timer.interval() == 5_000
    assert _label_text(widget, "scannerWorkspaceRefreshStatus") == "AUTO 5s"

    widget.close()


def test_auto_refresh_requires_scanner_results_service(
    qt_application: QApplication,
) -> None:
    with pytest.raises(ValueError, match="scanner results service"):
        ScannerWorkspaceWidget(auto_refresh_seconds=5)
