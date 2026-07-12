from __future__ import annotations

import os
from pathlib import Path
from threading import Event, get_ident

import pytest
from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication, QLabel

from trading_platform.application.diagnostics.project_analysis_report import (
    ProjectAnalysisReport,
)
from trading_platform.presentation.app.main import create_qt_application
from trading_platform.presentation.app.startup_controller import (
    CockpitStartupController,
)
from trading_platform.presentation.app.startup_status import StartupStatusDialog


@pytest.fixture(scope="module")
def qt_application() -> QApplication:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    return create_qt_application([])


class RecordingReportService:
    def __init__(self) -> None:
        self.thread_id: int | None = None

    def generate(
        self,
        project_root: Path,
        report_path: Path,
    ) -> ProjectAnalysisReport:
        self.thread_id = get_ident()
        return ProjectAnalysisReport(
            state="AVAILABLE",
            detail=f"Source: {report_path}",
            payload={
                "quality_gate": {"passed": True, "critical_failures": []},
                "file_counts": {"total_files": 10},
                "safety": {"mode": "read-only"},
            },
            source_path=report_path,
        )


class BlockingReportService(RecordingReportService):
    def __init__(self) -> None:
        super().__init__()
        self.started = Event()
        self.release = Event()

    def generate(
        self,
        project_root: Path,
        report_path: Path,
    ) -> ProjectAnalysisReport:
        self.thread_id = get_ident()
        self.started.set()
        if not self.release.wait(timeout=2):
            raise TimeoutError("Test report generation was not released.")
        return super().generate(project_root, report_path)


class FailingReportService:
    def generate(
        self,
        project_root: Path,
        report_path: Path,
    ) -> ProjectAnalysisReport:
        raise RuntimeError("controlled test failure")


def _wait_for_completion(
    controller: CockpitStartupController,
    timeout_ms: int = 2_000,
) -> None:
    event_loop = QEventLoop()
    completed = False

    def finish() -> None:
        nonlocal completed
        completed = True
        event_loop.quit()

    controller.completed.connect(finish)
    QTimer.singleShot(timeout_ms, event_loop.quit)
    event_loop.exec()

    assert completed
    assert controller.wait_for_finished()


def test_report_generation_runs_outside_gui_thread(
    qt_application: QApplication,
    tmp_path: Path,
) -> None:
    service = RecordingReportService()
    dialog = StartupStatusDialog()
    controller = CockpitStartupController(
        dialog,
        service,
        tmp_path,
        tmp_path / "report.json",
    )
    gui_thread_id = get_ident()

    controller.start()
    _wait_for_completion(controller)

    assert service.thread_id is not None
    assert service.thread_id != gui_thread_id
    assert controller.main_window is not None
    assert controller.main_window.isVisible()
    assert not dialog.isVisible()

    controller.main_window.close()


def test_startup_dialog_remains_visible_while_report_is_generated(
    qt_application: QApplication,
    tmp_path: Path,
) -> None:
    service = BlockingReportService()
    dialog = StartupStatusDialog()
    controller = CockpitStartupController(
        dialog,
        service,
        tmp_path,
        tmp_path / "report.json",
    )
    event_loop = QEventLoop()
    controller.completed.connect(event_loop.quit)

    controller.start()

    assert service.started.wait(timeout=1)
    status_message = dialog.findChild(QLabel, "startupStatusMessage")
    assert controller.is_running
    assert dialog.isVisible()
    assert status_message is not None
    assert status_message.text() == "Generating Project Analysis report..."

    service.release.set()
    QTimer.singleShot(2_000, event_loop.quit)
    event_loop.exec()

    assert controller.wait_for_finished()
    assert controller.main_window is not None
    controller.main_window.close()


def test_worker_exception_becomes_dashboard_error_state(
    qt_application: QApplication,
    tmp_path: Path,
) -> None:
    dialog = StartupStatusDialog()
    controller = CockpitStartupController(
        dialog,
        FailingReportService(),
        tmp_path,
        tmp_path / "report.json",
    )

    controller.start()
    _wait_for_completion(controller)

    assert controller.last_report is not None
    assert controller.last_report.state == "ERROR"
    assert "RuntimeError" in controller.last_report.detail
    assert controller.main_window is not None
    dashboard_state = controller.main_window.findChild(
        QLabel,
        "projectDashboardState",
    )
    assert dashboard_state is not None
    assert dashboard_state.text() == "ERROR"

    controller.main_window.close()
