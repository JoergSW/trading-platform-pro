from __future__ import annotations

import json
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
AGENT_PATH = PROJECT_ROOT / "tools" / "project_analysis_agent.py"


def load_agent_module() -> ModuleType:
    spec = spec_from_file_location("project_analysis_agent", AGENT_PATH)

    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load agent module from {AGENT_PATH}")

    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    return module


agent_module = load_agent_module()
analyze_project = agent_module.analyze_project
render_report = agent_module.render_report
render_json_report = agent_module.render_json_report
collect_quality_gate_failures = agent_module.collect_quality_gate_failures
main = agent_module.main
IMPORTANT_DOCUMENTATION_PATHS = agent_module.IMPORTANT_DOCUMENTATION_PATHS


def write_all_important_docs(root: Path) -> None:
    for documentation_path in IMPORTANT_DOCUMENTATION_PATHS:
        path = root / documentation_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Document\n\nValid content.\n", encoding="utf-8")


def test_analyze_project_counts_expected_files(tmp_path: Path) -> None:
    (tmp_path / "src" / "trading_platform").mkdir(parents=True)
    (tmp_path / "tests" / "unit").mkdir(parents=True)
    (tmp_path / "docs" / "product").mkdir(parents=True)
    (tmp_path / "scripts").mkdir()
    (tmp_path / "tools").mkdir()

    (tmp_path / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Readme\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    (tmp_path / "src" / "trading_platform" / "__init__.py").write_text(
        "", encoding="utf-8"
    )
    (tmp_path / "tests" / "unit" / "test_example.py").write_text(
        "def test_example():\n    assert True\n", encoding="utf-8"
    )
    (tmp_path / "docs" / "product" / "Product_Vision.md").write_text(
        "# Vision\n", encoding="utf-8"
    )
    (tmp_path / "scripts" / "generate_docs.py").write_text(
        "print('docs')\n", encoding="utf-8"
    )
    (tmp_path / "tools" / "project_analysis_agent.py").write_text(
        "print('agent')\n", encoding="utf-8"
    )

    report = analyze_project(tmp_path)

    assert report.total_files == 8
    assert report.python_files == 4
    assert report.markdown_files == 3
    assert report.source_files == 1
    assert report.test_files == 1
    assert report.documentation_files == 1
    assert report.script_files == 1
    assert report.tool_files == 1
    assert report.missing_important_paths == ()


def test_analyze_project_excludes_generated_and_temporary_files(tmp_path: Path) -> None:
    (tmp_path / "docs" / "generated").mkdir(parents=True)
    (tmp_path / "temp").mkdir()
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "src").mkdir()

    (tmp_path / "src" / "included.py").write_text("", encoding="utf-8")
    (tmp_path / "docs" / "generated" / "ignored.md").write_text(
        "# Ignored\n", encoding="utf-8"
    )
    (tmp_path / "temp" / "ignored.txt").write_text("ignored\n", encoding="utf-8")
    (tmp_path / "__pycache__" / "ignored.pyc").write_text("ignored\n", encoding="utf-8")

    report = analyze_project(tmp_path)

    assert report.total_files == 1
    assert report.python_files == 1
    assert report.source_files == 1
    assert report.documentation.documentation_markdown_files == 0


def test_analyze_project_reports_documentation_checks(tmp_path: Path) -> None:
    (tmp_path / "docs" / "product").mkdir(parents=True)
    (tmp_path / "docs" / "generated").mkdir(parents=True)

    (tmp_path / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
    (tmp_path / "docs" / "product" / "Product_Vision.md").write_text(
        "# Vision\n", encoding="utf-8"
    )
    (tmp_path / "docs" / "product" / "Empty.md").write_text("   \n", encoding="utf-8")
    (tmp_path / "docs" / "product" / "Placeholder.md").write_text(
        "# Placeholder\n\nProject specific content.\n", encoding="utf-8"
    )
    (tmp_path / "docs" / "generated" / "Ignored.md").write_text(
        "# TODO\n", encoding="utf-8"
    )

    report = analyze_project(tmp_path)

    assert report.documentation.docs_directory_present is True
    assert report.documentation.agents_file_present is True
    assert report.documentation.documentation_markdown_files == 3
    assert "AGENTS.md" in report.documentation.present_important_documentation_paths
    assert (
        "docs/product/Product_Vision.md"
        in report.documentation.present_important_documentation_paths
    )
    assert "docs/product/Empty.md" in report.documentation.empty_markdown_files
    assert (
        "docs/product/Placeholder.md" in report.documentation.placeholder_markdown_files
    )
    assert "docs/generated/Ignored.md" not in report.documentation.empty_markdown_files
    assert (
        "docs/generated/Ignored.md"
        not in report.documentation.placeholder_markdown_files
    )


def test_analyze_project_reports_architecture_boundary_checks(tmp_path: Path) -> None:
    domain_dir = tmp_path / "src" / "trading_platform" / "domain"
    application_dir = tmp_path / "src" / "trading_platform" / "application"
    infrastructure_dir = tmp_path / "src" / "trading_platform" / "infrastructure"
    presentation_dir = tmp_path / "src" / "trading_platform" / "presentation"

    domain_dir.mkdir(parents=True)
    application_dir.mkdir(parents=True)
    infrastructure_dir.mkdir(parents=True)
    presentation_dir.mkdir(parents=True)

    (domain_dir / "safe.py").write_text(
        "from trading_platform.domain.base import Entity\n", encoding="utf-8"
    )
    (domain_dir / "violating.py").write_text(
        "from trading_platform.infrastructure.clock import SystemClock\n"
        "from sqlalchemy import Column\n"
        "from PySide6.QtWidgets import QWidget\n",
        encoding="utf-8",
    )
    (application_dir / "violating.py").write_text(
        "from trading_platform.presentation.main_window import MainWindow\n",
        encoding="utf-8",
    )
    (infrastructure_dir / "adapter.py").write_text("", encoding="utf-8")
    (presentation_dir / "main_window.py").write_text("", encoding="utf-8")

    report = analyze_project(tmp_path)

    assert report.architecture.architecture_source_files == 5
    assert report.architecture.domain_files == 2
    assert report.architecture.application_files == 1
    assert (
        "src/trading_platform/domain/violating.py -> "
        "trading_platform.infrastructure.clock"
    ) in report.architecture.domain_import_violations
    assert (
        "src/trading_platform/domain/violating.py -> sqlalchemy"
        in report.architecture.domain_import_violations
    )
    assert (
        "src/trading_platform/domain/violating.py -> PySide6.QtWidgets"
        in report.architecture.domain_import_violations
    )
    assert (
        "src/trading_platform/application/violating.py -> "
        "trading_platform.presentation.main_window"
    ) in report.architecture.application_import_violations
    assert report.architecture.parse_errors == ()


def test_analyze_project_reports_python_parse_errors(tmp_path: Path) -> None:
    domain_dir = tmp_path / "src" / "trading_platform" / "domain"
    domain_dir.mkdir(parents=True)
    (domain_dir / "broken.py").write_text("def broken(:\n", encoding="utf-8")

    report = analyze_project(tmp_path)

    assert report.architecture.domain_files == 1
    assert report.architecture.parse_errors == (
        "src/trading_platform/domain/broken.py -> invalid syntax",
    )


def test_analyze_project_reports_trading_safety_hotspots(tmp_path: Path) -> None:
    application_dir = tmp_path / "src" / "trading_platform" / "application"
    infrastructure_dir = tmp_path / "src" / "trading_platform" / "infrastructure"
    application_dir.mkdir(parents=True)
    infrastructure_dir.mkdir(parents=True)

    (application_dir / "orders.py").write_text(
        "def submit_order(order, account):\n"
        "    retry = False\n"
        "    if order.environment == 'LIVE':\n"
        "        return account, retry\n",
        encoding="utf-8",
    )
    (infrastructure_dir / "broker.py").write_text(
        "def handle_broker_execution(fill):\n"
        "    reconciliation = 'discrepancy'\n"
        "    return fill, reconciliation\n",
        encoding="utf-8",
    )

    report = analyze_project(tmp_path)

    assert report.trading_safety.source_files_scanned == 2
    assert "src/trading_platform/application/orders.py" in (
        report.trading_safety.trading_related_files
    )
    assert "src/trading_platform/infrastructure/broker.py" in (
        report.trading_safety.trading_related_files
    )
    assert (
        "src/trading_platform/application/orders.py:L1 -> order, submit"
        in report.trading_safety.order_hotspots
    )
    assert (
        "src/trading_platform/application/orders.py:L2 -> retry"
        in report.trading_safety.retry_hotspots
    )
    assert (
        "src/trading_platform/application/orders.py:L3 -> live, environment"
        in report.trading_safety.live_environment_hotspots
    )
    assert (
        "src/trading_platform/infrastructure/broker.py:L1 -> broker"
        in report.trading_safety.broker_hotspots
    )
    assert (
        "src/trading_platform/infrastructure/broker.py:L1 -> execution, fill"
        in report.trading_safety.execution_hotspots
    )
    assert (
        "src/trading_platform/infrastructure/broker.py:L2 -> "
        "reconciliation, discrepancy"
    ) in report.trading_safety.reconciliation_hotspots


def test_render_report_marks_agent_as_read_only(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "included.py").write_text("", encoding="utf-8")

    report = analyze_project(tmp_path)
    rendered = render_report(report)

    assert "Read-only Project Analysis Agent" in rendered
    assert "Documentation checks:" in rendered
    assert "- docs directory present: no" in rendered
    assert "- generated docs ignored: yes" in rendered
    assert "Architecture checks:" in rendered
    assert "- domain import violations: none" in rendered
    assert "- application import violations: none" in rendered
    assert "Trading safety checks:" in rendered
    assert "- trading-related files: none" in rendered
    assert "- order hotspots: none" in rendered
    assert "- broker hotspots: none" in rendered
    assert "- LIVE/PAPER hotspots: none" in rendered
    assert "- mode: read-only" in rendered
    assert "- file writes: disabled" in rendered
    assert "- broker access: disabled" in rendered
    assert "- trading access: disabled" in rendered
    assert "- LIVE access: disabled" in rendered


def test_render_json_report_returns_machine_readable_output(
    tmp_path: Path,
) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "included.py").write_text("", encoding="utf-8")

    report = analyze_project(tmp_path)
    payload = json.loads(render_json_report(report))

    assert payload["root"] == str(tmp_path.resolve())
    assert payload["file_counts"]["source_files"] == 1
    assert payload["documentation"]["docs_directory_present"] is False
    assert payload["architecture"]["architecture_source_files"] == 1
    assert payload["trading_safety"]["source_files_scanned"] == 1
    assert payload["safety"] == {
        "mode": "read-only",
        "file_writes": "disabled",
        "broker_access": "disabled",
        "trading_access": "disabled",
        "live_access": "disabled",
    }


def test_main_outputs_json_when_requested(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "included.py").write_text("", encoding="utf-8")

    monkeypatch.setattr(
        sys,
        "argv",
        ["project_analysis_agent.py", str(tmp_path), "--json"],
    )

    main()

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert payload["safety"]["mode"] == "read-only"
    assert payload["safety"]["live_access"] == "disabled"
    assert "Read-only Project Analysis Agent" not in captured.out


def test_quality_gate_reports_critical_findings(tmp_path: Path) -> None:
    write_all_important_docs(tmp_path)

    domain_dir = tmp_path / "src" / "trading_platform" / "domain"
    domain_dir.mkdir(parents=True)

    (tmp_path / "docs" / "product" / "Empty.md").write_text("   \n", encoding="utf-8")
    (tmp_path / "docs" / "product" / "Placeholder.md").write_text(
        "# Placeholder\n\nProject specific content.\n", encoding="utf-8"
    )
    (domain_dir / "violating.py").write_text(
        "from trading_platform.infrastructure.clock import SystemClock\n",
        encoding="utf-8",
    )

    report = analyze_project(tmp_path)
    failures = collect_quality_gate_failures(report)

    assert "empty Markdown file: docs/product/Empty.md" in failures
    assert "placeholder Markdown file: docs/product/Placeholder.md" in failures
    assert (
        "domain import violation: "
        "src/trading_platform/domain/violating.py -> "
        "trading_platform.infrastructure.clock"
    ) in failures


def test_quality_gate_ignores_trading_safety_hotspots(tmp_path: Path) -> None:
    write_all_important_docs(tmp_path)

    application_dir = tmp_path / "src" / "trading_platform" / "application"
    application_dir.mkdir(parents=True)
    (application_dir / "orders.py").write_text(
        "def submit_order(order):\n    retry = False\n    return order, retry\n",
        encoding="utf-8",
    )

    report = analyze_project(tmp_path)

    assert report.trading_safety.order_hotspots
    assert report.trading_safety.retry_hotspots
    assert collect_quality_gate_failures(report) == ()


def test_render_json_report_contains_quality_gate(tmp_path: Path) -> None:
    write_all_important_docs(tmp_path)

    report = analyze_project(tmp_path)
    payload = json.loads(render_json_report(report))

    assert payload["quality_gate"] == {
        "passed": True,
        "critical_failures": [],
        "trading_safety_hotspots_are_report_only": True,
    }


def test_main_exits_with_error_when_quality_gate_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["project_analysis_agent.py", str(tmp_path), "--fail-on-critical"],
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1


def test_analyze_project_rejects_missing_root(tmp_path: Path) -> None:
    missing_root = tmp_path / "missing"

    with pytest.raises(ValueError, match="Project root does not exist"):
        analyze_project(missing_root)
