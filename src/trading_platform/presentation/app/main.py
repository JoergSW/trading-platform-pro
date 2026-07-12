from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path

from PySide6.QtWidgets import QApplication

from trading_platform.application.diagnostics.project_analysis_report import (
    DEFAULT_PROJECT_ANALYSIS_REPORT_PATH,
    ProjectAnalysisReport,
)
from trading_platform.composition.composition_root import (
    create_project_analysis_report_service,
)
from trading_platform.kernel.application import Application
from trading_platform.presentation.app.main_window import CockpitMainWindow
from trading_platform.presentation.widgets.project_dashboard import ProjectAnalysisData


def create_qt_application(arguments: Sequence[str] | None = None) -> QApplication:
    existing_application = QApplication.instance()
    if existing_application is not None:
        if not isinstance(existing_application, QApplication):
            raise RuntimeError("A non-GUI Qt application already exists.")
        return existing_application

    application_arguments = sys.argv if arguments is None else list(arguments)
    return QApplication(application_arguments)


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


def main() -> int:
    qt_application = create_qt_application()
    platform_application = Application()
    platform_application.start()

    try:
        project_root = Path.cwd()
        report_path = project_root / DEFAULT_PROJECT_ANALYSIS_REPORT_PATH
        report_service = create_project_analysis_report_service()
        report = report_service.generate(project_root, report_path)
        main_window = CockpitMainWindow(
            _to_project_analysis_data(report),
            report_path,
        )
        main_window.show()
        return qt_application.exec()
    finally:
        platform_application.stop()


if __name__ == "__main__":
    raise SystemExit(main())
