from __future__ import annotations

import os
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
)

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
    assert _label_text(widget, "scannerWorkspaceVisibleResultCount") == "0 of 0"
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
    assert _label_text(widget, "scannerWorkspaceVisibleResultCount") == "2 of 2"
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
    assert _label_text(widget, "scannerWorkspaceVisibleResultCount") == "0 of 0"
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


def test_scanner_workspace_filters_symbol_without_mutating_source_results(
    qt_application: QApplication,
) -> None:
    results = _ready_results()
    widget = ScannerWorkspaceWidget(results)
    symbol_filter = widget.findChild(QLineEdit, "scannerWorkspaceSymbolFilter")
    table = widget.findChild(QTableWidget, "scannerWorkspaceTable")

    assert symbol_filter is not None
    assert table is not None
    symbol_filter.setText("aap")

    assert widget.results is results
    assert len(widget.results.results) == 2
    assert _label_text(widget, "scannerWorkspaceResultCount") == "2"
    assert _label_text(widget, "scannerWorkspaceVisibleResultCount") == "1 of 2"
    assert table.rowCount() == 1
    assert table.item(0, 0).text() == "AAPL"

    widget.close()


def test_scanner_workspace_filters_signal_and_minimum_score(
    qt_application: QApplication,
) -> None:
    widget = ScannerWorkspaceWidget(_ready_results())
    signal_filter = widget.findChild(QComboBox, "scannerWorkspaceSignalFilter")
    minimum_score = widget.findChild(
        QLineEdit,
        "scannerWorkspaceMinimumScoreFilter",
    )
    clear_button = widget.findChild(
        QPushButton,
        "scannerWorkspaceClearFiltersButton",
    )
    table = widget.findChild(QTableWidget, "scannerWorkspaceTable")

    assert signal_filter is not None
    assert minimum_score is not None
    assert clear_button is not None
    assert table is not None

    signal_filter.setCurrentText("BREAKOUT")
    minimum_score.setText("95")

    assert _label_text(widget, "scannerWorkspaceVisibleResultCount") == "0 of 2"
    assert _label_text(widget, "scannerWorkspaceEmpty") == (
        "No scanner candidates match the active filters."
    )
    assert table.rowCount() == 0
    assert clear_button.isEnabled()

    clear_button.click()

    assert signal_filter.currentData() is None
    assert minimum_score.text() == ""
    assert _label_text(widget, "scannerWorkspaceVisibleResultCount") == "2 of 2"
    assert table.rowCount() == 2
    assert not clear_button.isEnabled()

    widget.close()


def test_scanner_workspace_sorts_all_columns_from_table_headers(
    qt_application: QApplication,
) -> None:
    results = ScannerResults.ready(
        "Local Scanner",
        (
            ScannerResult(
                symbol="NVDA",
                signal="REVERSAL",
                score=Decimal("91"),
                observed_at=datetime(2026, 7, 13, 13, 59, tzinfo=UTC),
            ),
            ScannerResult(
                symbol="MSFT",
                signal="MOMENTUM",
                score=Decimal("88"),
                observed_at=datetime(2026, 7, 13, 14, 1, tzinfo=UTC),
            ),
            ScannerResult(
                symbol="AAPL",
                signal="BREAKOUT",
                score=Decimal("94.5"),
                observed_at=datetime(2026, 7, 13, 14, 0, tzinfo=UTC),
            ),
        ),
    )
    widget = ScannerWorkspaceWidget(results)
    table = widget.findChild(QTableWidget, "scannerWorkspaceTable")

    assert table is not None
    header = table.horizontalHeader()
    assert isinstance(header, QHeaderView)

    header.sectionClicked.emit(0)
    assert [table.item(row, 0).text() for row in range(3)] == [
        "AAPL",
        "MSFT",
        "NVDA",
    ]

    header.sectionClicked.emit(1)
    assert [table.item(row, 1).text() for row in range(3)] == [
        "BREAKOUT",
        "MOMENTUM",
        "REVERSAL",
    ]

    header.sectionClicked.emit(2)
    assert [table.item(row, 2).text() for row in range(3)] == [
        "88",
        "91",
        "94.5",
    ]

    header.sectionClicked.emit(3)
    assert [table.item(row, 3).text() for row in range(3)] == [
        "2026-07-13 13:59:00 UTC",
        "2026-07-13 14:00:00 UTC",
        "2026-07-13 14:01:00 UTC",
    ]

    header.sectionClicked.emit(3)
    assert [table.item(row, 3).text() for row in range(3)] == [
        "2026-07-13 14:01:00 UTC",
        "2026-07-13 14:00:00 UTC",
        "2026-07-13 13:59:00 UTC",
    ]

    widget.close()


def test_scanner_workspace_keeps_active_filters_after_refresh(
    qt_application: QApplication,
) -> None:
    updated_results = ScannerResults.ready(
        "Refreshed Scanner",
        (
            ScannerResult(
                symbol="AAPL",
                signal="BREAKOUT",
                score=Decimal("97"),
                observed_at=datetime(2026, 7, 13, 14, 5, tzinfo=UTC),
            ),
            ScannerResult(
                symbol="AMZN",
                signal="MOMENTUM",
                score=Decimal("89"),
                observed_at=datetime(2026, 7, 13, 14, 6, tzinfo=UTC),
            ),
            ScannerResult(
                symbol="MSFT",
                signal="MOMENTUM",
                score=Decimal("90"),
                observed_at=datetime(2026, 7, 13, 14, 7, tzinfo=UTC),
            ),
        ),
    )
    widget = ScannerWorkspaceWidget(
        _ready_results(),
        results_service=ScannerResultsService(
            SequenceScannerResultsProvider(updated_results)
        ),
    )
    symbol_filter = widget.findChild(QLineEdit, "scannerWorkspaceSymbolFilter")
    signal_filter = widget.findChild(QComboBox, "scannerWorkspaceSignalFilter")
    table = widget.findChild(QTableWidget, "scannerWorkspaceTable")

    assert symbol_filter is not None
    assert signal_filter is not None
    assert table is not None
    symbol_filter.setText("A")
    signal_filter.setCurrentText("MOMENTUM")

    _refresh_and_wait(widget)

    assert symbol_filter.text() == "A"
    assert signal_filter.currentText() == "MOMENTUM"
    assert _label_text(widget, "scannerWorkspaceResultCount") == "3"
    assert _label_text(widget, "scannerWorkspaceVisibleResultCount") == "1 of 3"
    assert table.item(0, 0).text() == "AMZN"

    widget.close()
