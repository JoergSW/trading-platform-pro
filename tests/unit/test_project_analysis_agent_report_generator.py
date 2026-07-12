from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from trading_platform.infrastructure.diagnostics.project_analysis_agent import (
    PROJECT_ANALYSIS_TIMEOUT_SECONDS,
    ProjectAnalysisAgentReportGenerator,
)


def test_generator_writes_and_returns_project_analysis_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = tmp_path / "project"
    agent_path = project_root / "tools" / "project_analysis_agent.py"
    report_path = project_root / "temp" / "project-analysis-agent-report.json"
    agent_path.parent.mkdir(parents=True)
    agent_path.write_text("", encoding="utf-8")
    payload = {
        "root": str(project_root),
        "quality_gate": {"passed": True, "critical_failures": []},
        "safety": {"mode": "read-only"},
    }
    observed_command: tuple[str, ...] | None = None

    def run_agent(
        command: tuple[str, ...],
        **kwargs: object,
    ) -> subprocess.CompletedProcess[str]:
        nonlocal observed_command
        observed_command = command
        assert kwargs["cwd"] == project_root
        assert kwargs["timeout"] == PROJECT_ANALYSIS_TIMEOUT_SECONDS
        assert kwargs["check"] is False
        return subprocess.CompletedProcess(
            command,
            returncode=0,
            stdout=json.dumps(payload),
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", run_agent)
    generator = ProjectAnalysisAgentReportGenerator()

    result = generator.generate(project_root, report_path)

    assert observed_command == (
        sys.executable,
        str(agent_path),
        str(project_root),
        "--json",
    )
    assert result.state == "AVAILABLE"
    assert result.payload == payload
    assert result.source_path == report_path
    assert result.generated_at is not None
    assert json.loads(report_path.read_text(encoding="utf-8")) == payload


def test_generator_reports_agent_failure_without_stale_data(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = tmp_path / "project"
    agent_path = project_root / "tools" / "project_analysis_agent.py"
    report_path = project_root / "temp" / "project-analysis-agent-report.json"
    agent_path.parent.mkdir(parents=True)
    agent_path.write_text("", encoding="utf-8")
    report_path.parent.mkdir(parents=True)
    report_path.write_text('{"stale": true}', encoding="utf-8")

    def run_agent(
        command: tuple[str, ...],
        **kwargs: object,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            command,
            returncode=2,
            stdout="",
            stderr="failed",
        )

    monkeypatch.setattr(subprocess, "run", run_agent)
    generator = ProjectAnalysisAgentReportGenerator()

    result = generator.generate(project_root, report_path)

    assert result.state == "ERROR"
    assert result.detail == "Project Analysis Agent failed with exit code 2."
    assert result.source_path == report_path
    assert result.payload is None
    assert not report_path.exists()
