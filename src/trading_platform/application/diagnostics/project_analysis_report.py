from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol

DEFAULT_PROJECT_ANALYSIS_REPORT_PATH = Path("temp/project-analysis-agent-report.json")


@dataclass(frozen=True)
class ProjectAnalysisReport:
    """Application-owned result of Project Analysis report generation."""

    state: str
    detail: str
    payload: Mapping[str, object] | None = None
    source_path: Path | None = None
    generated_at: datetime | None = None


class ProjectAnalysisReportGenerator(Protocol):
    """Port for generating the Project Analysis report."""

    def generate(
        self,
        project_root: Path,
        report_path: Path,
    ) -> ProjectAnalysisReport:
        """Generate and persist one Project Analysis report."""
        ...


class ProjectAnalysisReportService:
    """Application service coordinating Project Analysis report generation."""

    def __init__(self, generator: ProjectAnalysisReportGenerator) -> None:
        self._generator = generator

    def generate(
        self,
        project_root: Path,
        report_path: Path,
    ) -> ProjectAnalysisReport:
        return self._generator.generate(project_root, report_path)
