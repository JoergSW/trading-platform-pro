from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

from PySide6.QtWidgets import QApplication

from trading_platform.kernel.application import Application
from trading_platform.presentation.app.main_window import CockpitMainWindow
from trading_platform.presentation.widgets.project_dashboard import (
    DEFAULT_PROJECT_ANALYSIS_REPORT_PATH,
    ProjectAnalysisData,
    load_project_analysis_data,
)

PROJECT_ANALYSIS_TIMEOUT_SECONDS = 30


def create_qt_application(arguments: Sequence[str] | None = None) -> QApplication:
    existing_application = QApplication.instance()
    if existing_application is not None:
        if not isinstance(existing_application, QApplication):
            raise RuntimeError("A non-GUI Qt application already exists.")
        return existing_application

    application_arguments = sys.argv if arguments is None else list(arguments)
    return QApplication(application_arguments)


def generate_project_analysis_data(
    project_root: Path,
    report_path: Path,
) -> ProjectAnalysisData:
    """Generate and load the read-only Project Analysis report once at startup."""
    agent_path = project_root / "tools" / "project_analysis_agent.py"
    if not agent_path.is_file():
        return ProjectAnalysisData(
            state="ERROR",
            detail=f"Project Analysis Agent not found: {agent_path}",
            source_path=report_path,
        )

    try:
        report_path.unlink(missing_ok=True)
    except OSError as exc:
        return ProjectAnalysisData(
            state="ERROR",
            detail=(
                "Existing Project Analysis report could not be removed: "
                f"{type(exc).__name__}"
            ),
            source_path=report_path,
        )

    try:
        completed_process = subprocess.run(
            (
                sys.executable,
                str(agent_path),
                str(project_root),
                "--json",
            ),
            cwd=project_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=PROJECT_ANALYSIS_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return ProjectAnalysisData(
            state="ERROR",
            detail=(
                f"Project Analysis Agent could not be executed: {type(exc).__name__}"
            ),
            source_path=report_path,
        )

    if completed_process.returncode != 0:
        return ProjectAnalysisData(
            state="ERROR",
            detail=(
                "Project Analysis Agent failed with exit code "
                f"{completed_process.returncode}."
            ),
            source_path=report_path,
        )

    try:
        raw_payload = json.loads(completed_process.stdout)
    except json.JSONDecodeError as exc:
        return ProjectAnalysisData(
            state="ERROR",
            detail=(
                f"Project Analysis Agent returned invalid JSON: {type(exc).__name__}"
            ),
            source_path=report_path,
        )

    if not isinstance(raw_payload, dict):
        return ProjectAnalysisData(
            state="ERROR",
            detail="Project Analysis Agent JSON root must be an object.",
            source_path=report_path,
        )

    temporary_path = report_path.with_name(f"{report_path.name}.tmp")
    try:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path.write_text(
            json.dumps(raw_payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        temporary_path.replace(report_path)
    except OSError as exc:
        try:
            temporary_path.unlink(missing_ok=True)
        except OSError:
            pass
        return ProjectAnalysisData(
            state="ERROR",
            detail=(
                f"Project Analysis report could not be written: {type(exc).__name__}"
            ),
            source_path=report_path,
        )

    return load_project_analysis_data(report_path)


def main() -> int:
    qt_application = create_qt_application()
    platform_application = Application()
    platform_application.start()

    try:
        project_root = Path.cwd()
        report_path = project_root / DEFAULT_PROJECT_ANALYSIS_REPORT_PATH
        project_analysis = generate_project_analysis_data(project_root, report_path)
        main_window = CockpitMainWindow(project_analysis, report_path)
        main_window.show()
        return qt_application.exec()
    finally:
        platform_application.stop()


if __name__ == "__main__":
    raise SystemExit(main())
