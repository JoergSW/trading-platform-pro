from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from trading_platform.application.diagnostics.project_analysis_report import (
    ProjectAnalysisReport,
)

PROJECT_ANALYSIS_TIMEOUT_SECONDS = 30


class ProjectAnalysisAgentReportGenerator:
    """Infrastructure adapter for the read-only Project Analysis Agent."""

    def __init__(self, timeout_seconds: int = PROJECT_ANALYSIS_TIMEOUT_SECONDS) -> None:
        self._timeout_seconds = timeout_seconds

    def generate(
        self,
        project_root: Path,
        report_path: Path,
    ) -> ProjectAnalysisReport:
        agent_path = project_root / "tools" / "project_analysis_agent.py"
        if not agent_path.is_file():
            return ProjectAnalysisReport(
                state="ERROR",
                detail=f"Project Analysis Agent not found: {agent_path}",
                source_path=report_path,
            )

        try:
            report_path.unlink(missing_ok=True)
        except OSError as exc:
            return ProjectAnalysisReport(
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
                timeout=self._timeout_seconds,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return ProjectAnalysisReport(
                state="ERROR",
                detail=(
                    "Project Analysis Agent could not be executed: "
                    f"{type(exc).__name__}"
                ),
                source_path=report_path,
            )

        if completed_process.returncode != 0:
            return ProjectAnalysisReport(
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
            return ProjectAnalysisReport(
                state="ERROR",
                detail=(
                    "Project Analysis Agent returned invalid JSON: "
                    f"{type(exc).__name__}"
                ),
                source_path=report_path,
            )

        if not isinstance(raw_payload, dict):
            return ProjectAnalysisReport(
                state="ERROR",
                detail="Project Analysis Agent JSON root must be an object.",
                source_path=report_path,
            )

        payload = cast(dict[str, object], raw_payload)
        temporary_path = report_path.with_name(f"{report_path.name}.tmp")
        try:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            temporary_path.write_text(
                json.dumps(payload, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            temporary_path.replace(report_path)
        except OSError as exc:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
            return ProjectAnalysisReport(
                state="ERROR",
                detail=(
                    "Project Analysis report could not be written: "
                    f"{type(exc).__name__}"
                ),
                source_path=report_path,
            )

        return ProjectAnalysisReport(
            state="AVAILABLE",
            detail=f"Source: {report_path}",
            payload=payload,
            source_path=report_path,
            generated_at=datetime.now(UTC),
        )
