from __future__ import annotations

import os
from pathlib import Path
from threading import Event, get_ident
from time import monotonic, sleep

import pytest
from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication, QLabel, QPushButton

from trading_platform.application.diagnostics.project_analysis_report import (
    ProjectAnalysisReport,
)
from trading_platform.presentation.app.main import (
    _ControlledStartupReportFailureGenerator,
    _parse_startup_arguments,
    create_qt_application,
)
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


class FailOnceReportService(RecordingReportService):
    def __init__(self) -> None:
        super().__init__()
        self.attempt_count = 0

    def generate(
        self,
        project_root: Path,
        report_path: Path,
    ) -> ProjectAnalysisReport:
        self.attempt_count += 1
        if self.attempt_count == 1:
            raise RuntimeError("controlled first-attempt failure")
        return super().generate(project_root, report_path)


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


def _wait_for_error_actions(
    qt_application: QApplication,
    dialog: StartupStatusDialog,
    controller: CockpitStartupController,
    timeout_seconds: float = 2.0,
) -> None:
    deadline = monotonic() + timeout_seconds
    retry_button = dialog.findChild(QPushButton, "startupRetryButton")

    assert retry_button is not None

    while monotonic() < deadline:
        qt_application.processEvents()
        if not controller.is_running and retry_button.isVisible():
            return
        sleep(0.01)

    raise AssertionError("Startup error actions did not become visible.")


def _retry_and_wait_for_completion(
    controller: CockpitStartupController,
    retry_button: QPushButton,
    timeout_ms: int = 2_000,
) -> None:
    event_loop = QEventLoop()
    completed = False

    def finish() -> None:
        nonlocal completed
        completed = True
        event_loop.quit()

    controller.completed.connect(finish)
    retry_button.click()
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


def test_worker_exception_keeps_startup_dialog_open(
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
    _wait_for_error_actions(qt_application, dialog, controller)

    assert controller.last_report is not None
    assert controller.last_report.state == "ERROR"
    assert "RuntimeError" in controller.last_report.detail
    assert controller.main_window is None
    assert dialog.isVisible()

    status_message = dialog.findChild(QLabel, "startupStatusMessage")
    assert status_message is not None
    assert status_message.text().startswith("Startup failed:")

    dialog.close()


def test_continue_opens_cockpit_with_dashboard_error_state(
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
    _wait_for_error_actions(qt_application, dialog, controller)

    continue_button = dialog.findChild(QPushButton, "startupContinueButton")
    assert continue_button is not None
    continue_button.click()
    qt_application.processEvents()

    assert controller.main_window is not None
    assert controller.main_window.isVisible()
    assert not dialog.isVisible()

    dashboard_state = controller.main_window.findChild(
        QLabel,
        "projectDashboardState",
    )
    assert dashboard_state is not None
    assert dashboard_state.text() == "ERROR"

    controller.main_window.close()


def test_retry_repeats_generation_and_opens_cockpit_after_success(
    qt_application: QApplication,
    tmp_path: Path,
) -> None:
    service = FailOnceReportService()
    dialog = StartupStatusDialog()
    controller = CockpitStartupController(
        dialog,
        service,
        tmp_path,
        tmp_path / "report.json",
    )

    controller.start()
    _wait_for_error_actions(qt_application, dialog, controller)

    retry_button = dialog.findChild(QPushButton, "startupRetryButton")
    assert retry_button is not None
    _retry_and_wait_for_completion(controller, retry_button)

    assert service.attempt_count == 2
    assert controller.last_report is not None
    assert controller.last_report.state == "AVAILABLE"
    assert controller.main_window is not None
    assert controller.main_window.isVisible()
    assert not dialog.isVisible()

    controller.main_window.close()


def test_controlled_failure_once_allows_retry_to_use_delegate(tmp_path: Path) -> None:
    delegate = RecordingReportService()
    generator = _ControlledStartupReportFailureGenerator(delegate, "once")
    report_path = tmp_path / "report.json"

    first_result = generator.generate(tmp_path, report_path)

    assert first_result.state == "ERROR"
    assert first_result.detail == (
        "Controlled startup report failure simulation (once)."
    )
    assert delegate.thread_id is None

    second_result = generator.generate(tmp_path, report_path)

    assert second_result.state == "AVAILABLE"
    assert delegate.thread_id is not None


def test_controlled_failure_always_never_calls_delegate(tmp_path: Path) -> None:
    delegate = RecordingReportService()
    generator = _ControlledStartupReportFailureGenerator(delegate, "always")
    report_path = tmp_path / "report.json"

    first_result = generator.generate(tmp_path, report_path)
    second_result = generator.generate(tmp_path, report_path)

    assert first_result.state == "ERROR"
    assert second_result.state == "ERROR"
    assert delegate.thread_id is None


def test_parse_startup_arguments_preserves_qt_arguments() -> None:
    failure_mode, qt_arguments = _parse_startup_arguments(
        [
            "--simulate-startup-report-failure",
            "once",
            "-platform",
            "offscreen",
        ]
    )

    assert failure_mode == "once"
    assert qt_arguments == ["-platform", "offscreen"]


def test_parse_startup_arguments_keeps_normal_start_unmodified() -> None:
    failure_mode, qt_arguments = _parse_startup_arguments([])

    assert failure_mode is None
    assert qt_arguments == []
