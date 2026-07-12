from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal, Slot

from trading_platform.application.diagnostics.project_analysis_report import (
    ProjectAnalysisReport,
    ProjectAnalysisReportGenerator,
)
from trading_platform.presentation.app.main_window import CockpitMainWindow
from trading_platform.presentation.app.startup_status import StartupStatusDialog
from trading_platform.presentation.widgets.project_dashboard import ProjectAnalysisData

MainWindowFactory = Callable[[ProjectAnalysisData, Path], CockpitMainWindow]


class _ProjectAnalysisReportWorker(QObject):
    completed = Signal(object)

    def __init__(
        self,
        report_service: ProjectAnalysisReportGenerator,
        project_root: Path,
        report_path: Path,
    ) -> None:
        super().__init__()
        self._report_service = report_service
        self._project_root = project_root
        self._report_path = report_path

    @Slot()
    def generate(self) -> None:
        try:
            report = self._report_service.generate(
                self._project_root,
                self._report_path,
            )
        except Exception as exc:
            report = ProjectAnalysisReport(
                state="ERROR",
                detail=(
                    f"Project Analysis report generation raised {type(exc).__name__}."
                ),
                source_path=self._report_path,
            )

        self.completed.emit(report)


class AsyncProjectAnalysisReportRunner(QObject):
    """Run Project Analysis report generation outside the GUI thread."""

    completed = Signal(object)

    def __init__(
        self,
        report_service: ProjectAnalysisReportGenerator,
        project_root: Path,
        report_path: Path,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._report_service = report_service
        self._project_root = project_root
        self._report_path = report_path
        self._thread: QThread | None = None
        self._worker: _ProjectAnalysisReportWorker | None = None

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.isRunning()

    def start(self) -> None:
        if self.is_running:
            raise RuntimeError("Project Analysis report generation is already running.")

        thread = QThread(self)
        worker = _ProjectAnalysisReportWorker(
            self._report_service,
            self._project_root,
            self._report_path,
        )
        worker.moveToThread(thread)

        thread.started.connect(worker.generate)
        worker.completed.connect(self._handle_completed)
        worker.completed.connect(thread.quit)
        worker.completed.connect(worker.deleteLater)
        thread.finished.connect(self._release_thread)
        thread.finished.connect(thread.deleteLater)

        self._thread = thread
        self._worker = worker
        thread.start()

    def wait_for_finished(self, timeout_ms: int = 35_000) -> bool:
        thread = self._thread
        if thread is None or not thread.isRunning():
            return True

        thread.quit()
        return thread.wait(timeout_ms)

    @Slot(object)
    def _handle_completed(self, report: object) -> None:
        self.completed.emit(report)

    @Slot()
    def _release_thread(self) -> None:
        self._worker = None
        self._thread = None


class CockpitStartupController(QObject):
    """Coordinate responsive startup progress and cockpit presentation."""

    completed = Signal()

    def __init__(
        self,
        startup_status: StartupStatusDialog,
        report_service: ProjectAnalysisReportGenerator,
        project_root: Path,
        report_path: Path,
        main_window_factory: MainWindowFactory = CockpitMainWindow,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._startup_status = startup_status
        self._report_path = report_path
        self._main_window_factory = main_window_factory
        self._runner = AsyncProjectAnalysisReportRunner(
            report_service,
            project_root,
            report_path,
            self,
        )
        self._runner.completed.connect(self._handle_report)
        self._main_window: CockpitMainWindow | None = None
        self._last_report: ProjectAnalysisReport | None = None

    @property
    def is_running(self) -> bool:
        return self._runner.is_running

    @property
    def main_window(self) -> CockpitMainWindow | None:
        return self._main_window

    @property
    def last_report(self) -> ProjectAnalysisReport | None:
        return self._last_report

    def start(self) -> None:
        self._startup_status.update_status(
            "Generating Project Analysis report...",
            2,
        )
        if not self._startup_status.isVisible():
            self._startup_status.show()
        self._runner.start()

    def wait_for_finished(self, timeout_ms: int = 35_000) -> bool:
        return self._runner.wait_for_finished(timeout_ms)

    @Slot(object)
    def _handle_report(self, report: object) -> None:
        if not isinstance(report, ProjectAnalysisReport):
            raise TypeError("Startup worker returned an invalid report result.")

        self._last_report = report
        self._startup_status.update_status("Loading dashboard...", 3)
        self._main_window = self._main_window_factory(
            _to_project_analysis_data(report),
            self._report_path,
        )
        self._main_window.show()
        self._startup_status.close()
        self.completed.emit()


def _to_project_analysis_data(
    report: ProjectAnalysisReport,
) -> ProjectAnalysisData:
    return ProjectAnalysisData(
        state=report.state,
        detail=report.detail,
        payload=report.payload,
        source_path=report.source_path,
        loaded_at=report.generated_at,
    )
