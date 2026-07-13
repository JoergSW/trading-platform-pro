from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from functools import partial
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from trading_platform.application.diagnostics.project_analysis_report import (
    DEFAULT_PROJECT_ANALYSIS_REPORT_PATH,
    ProjectAnalysisReport,
    ProjectAnalysisReportGenerator,
)
from trading_platform.composition.composition_root import (
    create_market_snapshot_service,
    create_project_analysis_report_service,
)
from trading_platform.kernel.application import Application
from trading_platform.presentation.app.main_window import CockpitMainWindow
from trading_platform.presentation.app.startup_controller import (
    CockpitStartupController,
)
from trading_platform.presentation.app.startup_status import StartupStatusDialog

STARTUP_REPORT_FAILURE_MODES = ("once", "always")


class _ControlledStartupReportFailureGenerator:
    """Explicit manual-test decorator for startup recovery paths."""

    def __init__(
        self,
        delegate: ProjectAnalysisReportGenerator,
        failure_mode: str,
    ) -> None:
        if failure_mode not in STARTUP_REPORT_FAILURE_MODES:
            raise ValueError(f"Unsupported startup failure mode: {failure_mode}")

        self._delegate = delegate
        self._failure_mode = failure_mode
        self._failure_emitted = False

    def generate(
        self,
        project_root: Path,
        report_path: Path,
    ) -> ProjectAnalysisReport:
        should_fail = self._failure_mode == "always" or not self._failure_emitted
        if should_fail:
            self._failure_emitted = True
            return ProjectAnalysisReport(
                state="ERROR",
                detail=(
                    "Controlled startup report failure simulation "
                    f"({self._failure_mode})."
                ),
                source_path=report_path,
            )

        return self._delegate.generate(project_root, report_path)


def _parse_startup_arguments(
    arguments: Sequence[str],
) -> tuple[str | None, Path | None, list[str]]:
    parser = argparse.ArgumentParser(description="Start the Trading Cockpit.")
    parser.add_argument(
        "--simulate-startup-report-failure",
        choices=STARTUP_REPORT_FAILURE_MODES,
        help=(
            "Manual system-test mode. Simulate Project Analysis report generation "
            "failure once or on every attempt."
        ),
    )
    parser.add_argument(
        "--market-snapshot-json",
        type=Path,
        help=(
            "Explicit read-only JSON market snapshot file. No default file is "
            "loaded when this option is omitted."
        ),
    )
    options, qt_arguments = parser.parse_known_args(list(arguments))
    return (
        options.simulate_startup_report_failure,
        options.market_snapshot_json,
        qt_arguments,
    )


def _create_report_service(
    failure_mode: str | None,
) -> ProjectAnalysisReportGenerator:
    service = create_project_analysis_report_service()
    if failure_mode is None:
        return service

    return _ControlledStartupReportFailureGenerator(service, failure_mode)


def create_qt_application(arguments: Sequence[str] | None = None) -> QApplication:
    existing_application = QApplication.instance()
    if existing_application is not None:
        if not isinstance(existing_application, QApplication):
            raise RuntimeError("A non-GUI Qt application already exists.")
        return existing_application

    application_arguments = sys.argv if arguments is None else list(arguments)
    return QApplication(application_arguments)


def _show_startup_step(
    qt_application: QApplication,
    startup_status: StartupStatusDialog,
    message: str,
    step: int,
) -> None:
    startup_status.update_status(message, step)
    if not startup_status.isVisible():
        startup_status.show()
    qt_application.processEvents()


def main(arguments: Sequence[str] | None = None) -> int:
    raw_arguments = sys.argv[1:] if arguments is None else list(arguments)
    failure_mode, market_snapshot_path, qt_arguments = _parse_startup_arguments(
        raw_arguments
    )
    application_name = sys.argv[0] if arguments is None else "trading-cockpit"
    qt_application = create_qt_application([application_name, *qt_arguments])
    startup_status = StartupStatusDialog()
    platform_application = Application()
    platform_started = False
    startup_controller: CockpitStartupController | None = None

    _show_startup_step(
        qt_application,
        startup_status,
        "Starting application...",
        1,
    )

    try:
        platform_application.start()
        platform_started = True

        project_root = Path.cwd()
        report_path = project_root / DEFAULT_PROJECT_ANALYSIS_REPORT_PATH
        market_snapshot = create_market_snapshot_service(
            market_snapshot_path
        ).load_snapshot()
        startup_controller = CockpitStartupController(
            startup_status,
            _create_report_service(failure_mode),
            project_root,
            report_path,
            main_window_factory=partial(
                CockpitMainWindow,
                market_snapshot=market_snapshot,
            ),
        )
        QTimer.singleShot(0, startup_controller.start)
        return qt_application.exec()
    finally:
        if startup_controller is not None:
            startup_controller.wait_for_finished()
        startup_status.close()
        if platform_started:
            platform_application.stop()


if __name__ == "__main__":
    raise SystemExit(main())
