from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path

from PySide6.QtWidgets import QApplication

from trading_platform.kernel.application import Application
from trading_platform.presentation.app.main_window import CockpitMainWindow
from trading_platform.presentation.widgets.project_dashboard import (
    DEFAULT_PROJECT_ANALYSIS_REPORT_PATH,
    load_project_analysis_data,
)


def create_qt_application(arguments: Sequence[str] | None = None) -> QApplication:
    existing_application = QApplication.instance()
    if existing_application is not None:
        if not isinstance(existing_application, QApplication):
            raise RuntimeError("A non-GUI Qt application already exists.")
        return existing_application

    application_arguments = sys.argv if arguments is None else list(arguments)
    return QApplication(application_arguments)


def main() -> int:
    qt_application = create_qt_application()
    platform_application = Application()
    platform_application.start()

    try:
        report_path = Path.cwd() / DEFAULT_PROJECT_ANALYSIS_REPORT_PATH
        project_analysis = load_project_analysis_data(report_path)
        main_window = CockpitMainWindow(project_analysis)
        main_window.show()
        return qt_application.exec()
    finally:
        platform_application.stop()


if __name__ == "__main__":
    raise SystemExit(main())
