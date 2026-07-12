from __future__ import annotations

from pathlib import Path

from trading_platform.application.diagnostics.project_analysis_report import (
    ProjectAnalysisReport,
    ProjectAnalysisReportService,
)


class StubProjectAnalysisReportGenerator:
    def __init__(self, result: ProjectAnalysisReport) -> None:
        self._result = result
        self.observed_project_root: Path | None = None
        self.observed_report_path: Path | None = None

    def generate(
        self,
        project_root: Path,
        report_path: Path,
    ) -> ProjectAnalysisReport:
        self.observed_project_root = project_root
        self.observed_report_path = report_path
        return self._result


def test_project_analysis_report_service_delegates_to_generator() -> None:
    project_root = Path("/project")
    report_path = Path("/project/temp/report.json")
    expected = ProjectAnalysisReport(
        state="AVAILABLE",
        detail="Source: test",
        payload={"quality_gate": {"passed": True}},
        source_path=report_path,
    )
    generator = StubProjectAnalysisReportGenerator(expected)
    service = ProjectAnalysisReportService(generator)

    result = service.generate(project_root, report_path)

    assert result is expected
    assert generator.observed_project_root == project_root
    assert generator.observed_report_path == report_path
