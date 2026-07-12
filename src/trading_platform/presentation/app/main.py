from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from trading_platform.application.diagnostics.project_analysis_report import (
    DEFAULT_PROJECT_ANALYSIS_REPORT_PATH,
)
from trading_platform.composition.composition_root import (
    create_project_analysis_report_service,
)
from trading_platform.kernel.application import Application
from trading_platform.presentation.app.startup_controller import (
    CockpitStartupController,
)
from trading_platform.presentation.app.startup_status import StartupStatusDialog


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


def main() -> int:
    qt_application = create_qt_application()
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
        startup_controller = CockpitStartupController(
            startup_status,
            create_project_analysis_report_service(),
            project_root,
            report_path,
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
