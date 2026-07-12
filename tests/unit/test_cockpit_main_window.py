from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path

import pytest
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QListWidget,
    QPushButton,
    QSplitter,
    QStackedWidget,
)

from trading_platform.presentation.app.main import create_qt_application
from trading_platform.presentation.app.main_window import (
    NAVIGATION_ITEMS,
    QUICK_INFO_ITEMS,
    CockpitMainWindow,
)
from trading_platform.presentation.widgets.project_dashboard import (
    ProjectAnalysisData,
    ProjectDashboardWidget,
    collect_project_dashboard_hotspots,
    load_project_analysis_data,
)
from trading_platform.presentation.workspaces.cockpit_workspace import (
    CockpitWorkspaceWidget,
    WorkspacePlaceholderPage,
)
from trading_platform.presentation.workspaces.market_workspace import (
    MarketWorkspaceWidget,
)


@pytest.fixture(scope="module")
def qt_application() -> QApplication:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    application = create_qt_application([])
    return application


def _list_items(widget: QListWidget) -> tuple[str, ...]:
    return tuple(widget.item(index).text() for index in range(widget.count()))


def _project_analysis_data() -> ProjectAnalysisData:
    return ProjectAnalysisData(
        state="AVAILABLE",
        detail="Source: test report",
        payload={
            "root": "/project",
            "file_counts": {
                "total_files": 120,
                "python_files": 80,
                "source_files": 60,
                "test_files": 20,
                "documentation_files": 15,
            },
            "quality_gate": {
                "passed": False,
                "critical_failures": ["architecture violation"],
            },
            "safety": {
                "mode": "read-only",
                "broker_access": "disabled",
                "trading_access": "disabled",
                "live_access": "disabled",
            },
            "architecture": {
                "domain_import_violations": ["domain.py -> infrastructure"],
            },
            "trading_safety": {
                "order_hotspots": ["runtime.py:L10 -> order"],
            },
        },
        source_path=Path("temp/test-report.json"),
        loaded_at=datetime(2026, 7, 11, 12, 30, tzinfo=UTC),
    )


def test_cockpit_shell_contains_target_layout(
    qt_application: QApplication,
) -> None:
    window = CockpitMainWindow()

    splitter = window.findChild(QSplitter, "cockpitContentSplitter")
    navigation = window.findChild(QListWidget, "navigationList")
    quick_info = window.findChild(QListWidget, "quickInfoList")
    application_state = window.findChild(QLabel, "applicationState")
    environment_state = window.findChild(QLabel, "environmentState")
    connection_state = window.findChild(QLabel, "connectionState")
    dashboard = window.findChild(ProjectDashboardWidget, "projectDashboardWidget")
    dashboard_state = window.findChild(QLabel, "projectDashboardState")
    market_workspace = window.findChild(
        MarketWorkspaceWidget,
        "marketWorkspaceWidget",
    )
    market_state = window.findChild(QLabel, "marketWorkspaceState")

    assert splitter is not None
    assert splitter.count() == 3
    assert navigation is not None
    assert _list_items(navigation) == NAVIGATION_ITEMS
    assert quick_info is not None
    assert _list_items(quick_info) == QUICK_INFO_ITEMS
    assert application_state is not None
    assert application_state.text() == "Status: READY"
    assert environment_state is not None
    assert environment_state.text() == "Mode: OFFLINE"
    assert connection_state is not None
    assert connection_state.text() == "Connection: DISCONNECTED"
    assert dashboard is not None
    assert dashboard_state is not None
    assert dashboard_state.text() == "UNAVAILABLE"
    assert market_workspace is not None
    assert market_state is not None
    assert market_state.text() == "UNAVAILABLE"

    window.close()


def test_dashboard_displays_project_analysis_data(
    qt_application: QApplication,
) -> None:
    window = CockpitMainWindow(_project_analysis_data())

    dashboard_state = window.findChild(QLabel, "projectDashboardState")
    quality_gate = window.findChild(QLabel, "projectDashboardQualityGate")
    total_files = window.findChild(QLabel, "projectDashboardTotalFiles")
    safety_mode = window.findChild(QLabel, "projectDashboardSafetyMode")
    broker_access = window.findChild(QLabel, "projectDashboardBrokerAccess")
    source_path = window.findChild(QLabel, "projectDashboardSourcePath")
    last_loaded = window.findChild(QLabel, "projectDashboardLastSuccessfulLoad")
    hotspots = window.findChild(QListWidget, "projectDashboardHotspots")

    assert dashboard_state is not None
    assert dashboard_state.text() == "AVAILABLE"
    assert quality_gate is not None
    assert quality_gate.text() == "FAILED"
    assert total_files is not None
    assert total_files.text() == "120"
    assert safety_mode is not None
    assert safety_mode.text() == "read-only"
    assert broker_access is not None
    assert broker_access.text() == "disabled"
    assert source_path is not None
    assert source_path.text() == f"Source: {Path('temp/test-report.json')}"
    assert last_loaded is not None
    assert last_loaded.text() == "Last successful load: 2026-07-11 12:30:00 UTC"
    assert hotspots is not None
    assert _list_items(hotspots) == (
        "Quality Gate: architecture violation",
        "Architecture / Domain Import Violations: domain.py -> infrastructure",
        "Trading Safety / Order Hotspots: runtime.py:L10 -> order",
    )

    window.close()


def test_navigation_switches_between_distinct_workspace_pages(
    qt_application: QApplication,
) -> None:
    window = CockpitMainWindow(_project_analysis_data())
    navigation = window.findChild(QListWidget, "navigationList")
    workspace = window.findChild(CockpitWorkspaceWidget, "cockpitWorkspaceWidget")
    workspace_title = window.findChild(QLabel, "workspaceTitle")
    workspace_stack = window.findChild(QStackedWidget, "workspaceStack")
    dashboard = window.findChild(ProjectDashboardWidget, "projectDashboardWidget")
    scanner_page = window.findChild(
        WorkspacePlaceholderPage,
        "scannerWorkspacePage",
    )
    market_page = window.findChild(
        MarketWorkspaceWidget,
        "marketWorkspaceWidget",
    )

    assert navigation is not None
    assert workspace is not None
    assert workspace.page_names == NAVIGATION_ITEMS
    assert workspace_title is not None
    assert workspace_stack is not None
    assert workspace_stack.count() == len(NAVIGATION_ITEMS)
    assert dashboard is not None
    assert scanner_page is not None
    assert market_page is not None
    assert scanner_page is not market_page

    navigation.setCurrentRow(NAVIGATION_ITEMS.index("Scanner"))
    qt_application.processEvents()

    assert workspace_title.text() == "Scanner"
    assert workspace_stack.currentWidget() is scanner_page

    navigation.setCurrentRow(NAVIGATION_ITEMS.index("Market"))
    qt_application.processEvents()

    assert workspace_title.text() == "Market"
    assert workspace_stack.currentWidget() is market_page

    navigation.setCurrentRow(NAVIGATION_ITEMS.index("Dashboard"))
    qt_application.processEvents()

    assert workspace_title.text() == "Dashboard"
    assert workspace_stack.currentWidget() is dashboard

    window.close()


def test_dashboard_refresh_reloads_existing_json_report(
    qt_application: QApplication,
    tmp_path: Path,
) -> None:
    report_path = tmp_path / "project-analysis-agent-report.json"
    initial_payload = {
        "root": "/project",
        "file_counts": {"total_files": 10},
        "quality_gate": {"passed": False, "critical_failures": ["one"]},
        "safety": {"mode": "read-only"},
    }
    updated_payload = {
        "root": "/project",
        "file_counts": {"total_files": 240},
        "quality_gate": {"passed": True, "critical_failures": []},
        "safety": {"mode": "read-only"},
    }
    report_path.write_text(json.dumps(initial_payload), encoding="utf-8")
    window = CockpitMainWindow(
        load_project_analysis_data(report_path),
        report_path,
    )

    refresh_button = window.findChild(QPushButton, "projectDashboardRefreshButton")
    total_files = window.findChild(QLabel, "projectDashboardTotalFiles")

    assert refresh_button is not None
    assert refresh_button.isEnabled()
    assert total_files is not None
    assert total_files.text() == "10"

    source_path = window.findChild(QLabel, "projectDashboardSourcePath")
    last_loaded = window.findChild(QLabel, "projectDashboardLastSuccessfulLoad")
    assert source_path is not None
    assert source_path.text() == f"Source: {report_path}"
    assert last_loaded is not None
    assert last_loaded.text() != "Last successful load: Never"

    report_path.write_text(json.dumps(updated_payload), encoding="utf-8")
    refresh_button.click()
    qt_application.processEvents()

    dashboard_state = window.findChild(QLabel, "projectDashboardState")
    quality_gate = window.findChild(QLabel, "projectDashboardQualityGate")
    total_files = window.findChild(QLabel, "projectDashboardTotalFiles")

    assert dashboard_state is not None
    assert dashboard_state.text() == "AVAILABLE"
    assert quality_gate is not None
    assert quality_gate.text() == "PASSED"
    assert total_files is not None
    assert total_files.text() == "240"

    window.close()


def test_dashboard_refresh_updates_error_state(
    qt_application: QApplication,
    tmp_path: Path,
) -> None:
    report_path = tmp_path / "project-analysis-agent-report.json"
    report_path.write_text("{invalid", encoding="utf-8")
    window = CockpitMainWindow(_project_analysis_data(), report_path)
    refresh_button = window.findChild(QPushButton, "projectDashboardRefreshButton")

    assert refresh_button is not None
    refresh_button.click()
    qt_application.processEvents()

    dashboard_state = window.findChild(QLabel, "projectDashboardState")
    unavailable_message = window.findChild(QLabel, "projectDashboardUnavailableMessage")
    source_path = window.findChild(QLabel, "projectDashboardSourcePath")
    last_loaded = window.findChild(QLabel, "projectDashboardLastSuccessfulLoad")

    assert dashboard_state is not None
    assert dashboard_state.text() == "ERROR"
    assert unavailable_message is not None
    assert "JSONDecodeError" in unavailable_message.text()
    assert source_path is not None
    assert source_path.text() == f"Source: {report_path}"
    assert last_loaded is not None
    assert last_loaded.text() == "Last successful load: 2026-07-11 12:30:00 UTC"

    window.close()


def test_collect_project_dashboard_hotspots_applies_limit() -> None:
    payload = {
        "quality_gate": {
            "critical_failures": ["one", "two"],
        },
        "architecture": {
            "parse_errors": ["three"],
        },
    }

    assert collect_project_dashboard_hotspots(payload, limit=2) == (
        "Quality Gate: one",
        "Quality Gate: two",
    )


def test_load_project_analysis_data_reads_json_report(tmp_path: Path) -> None:
    report_path = tmp_path / "report.json"
    payload = {
        "root": "/project",
        "quality_gate": {"passed": True},
    }
    report_path.write_text(json.dumps(payload), encoding="utf-8")

    result = load_project_analysis_data(report_path)

    assert result.state == "AVAILABLE"
    assert result.payload == payload
    assert result.detail == f"Source: {report_path}"
    assert result.source_path == report_path
    assert result.loaded_at is not None
    assert result.loaded_at.tzinfo is UTC


def test_load_project_analysis_data_reports_missing_file(tmp_path: Path) -> None:
    report_path = tmp_path / "missing.json"

    result = load_project_analysis_data(report_path)

    assert result.state == "UNAVAILABLE"
    assert result.payload is None
    assert result.source_path == report_path
    assert result.loaded_at is None


def test_create_qt_application_reuses_existing_application(
    qt_application: QApplication,
) -> None:
    assert create_qt_application([]) is qt_application
