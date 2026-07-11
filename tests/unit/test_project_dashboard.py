from __future__ import annotations

import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DASHBOARD_PATH = PROJECT_ROOT / "tools" / "project_dashboard.py"


def load_dashboard_module() -> ModuleType:
    spec = spec_from_file_location("project_dashboard", DASHBOARD_PATH)

    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load dashboard module from {DASHBOARD_PATH}")

    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    return module


dashboard_module = load_dashboard_module()
collect_dashboard_hotspot_sections = dashboard_module.collect_dashboard_hotspot_sections
collect_dashboard_section_cards = dashboard_module.collect_dashboard_section_cards
render_dashboard_html = dashboard_module.render_dashboard_html
main = dashboard_module.main


def test_render_dashboard_html_shows_minimal_project_summary() -> None:
    payload = {
        "root": "/project/<demo>",
        "file_counts": {
            "total_files": 10,
            "python_files": 4,
        },
        "quality_gate": {
            "passed": False,
            "critical_failures": ["docs directory missing"],
        },
        "safety": {
            "mode": "read-only",
            "broker_access": "disabled",
        },
        "trading_safety": {
            "order_hotspots": ["src/app.py:L1 -> order"],
        },
        "architecture": {
            "domain_import_violations": ["domain.py -> infrastructure"],
        },
    }

    rendered = render_dashboard_html(payload)

    assert "Project Analysis Dashboard" in rendered
    assert "Root: /project/&lt;demo&gt;" in rendered
    assert "Quality Gate: failed" in rendered
    assert "docs directory missing" in rendered
    assert "File Counts" in rendered
    assert "Total Files" in rendered
    assert "10" in rendered
    assert "Safety Mode" in rendered
    assert "read-only" in rendered
    assert "Core Check Sections" in rendered
    assert "Architecture" in rendered
    assert "Import Violations" in rendered
    assert "Trading Safety" in rendered
    assert "Live Environment Hotspots" in rendered
    assert "Important Hotspots" in rendered
    assert "Order Hotspots: src/app.py:L1 -&gt; order" in rendered
    assert "Domain Import Violations: domain.py -&gt; infrastructure" in rendered


def test_collect_dashboard_section_cards_builds_core_check_cards() -> None:
    payload = {
        "quality_gate": {
            "passed": False,
            "critical_failures": ["architecture violation"],
        },
        "safety": {
            "mode": "read-only",
            "file_writes": "disabled",
            "broker_access": "disabled",
            "trading_access": "disabled",
            "live_access": "disabled",
        },
        "architecture": {
            "architecture_source_files": 5,
            "domain_files": 2,
            "application_files": 3,
            "domain_import_violations": ["domain -> infrastructure"],
            "application_import_violations": [],
            "parse_errors": [],
        },
        "trading_safety": {
            "source_files_scanned": 5,
            "trading_related_files": ["src/runtime.py"],
            "order_hotspots": ["src/runtime.py:L10 -> order"],
            "broker_hotspots": [],
            "live_environment_hotspots": [],
            "retry_hotspots": [],
            "reconciliation_hotspots": [],
            "execution_hotspots": [],
        },
    }

    cards = collect_dashboard_section_cards(payload)

    assert [card.title for card in cards] == [
        "Quality Gate",
        "Safety",
        "Architecture",
        "Trading Safety",
    ]
    assert cards[0].status == "failed"
    assert ("Critical Failures", 1) in cards[0].metrics
    assert cards[1].status == "read-only"
    assert ("Broker Access", "disabled") in cards[1].metrics
    assert cards[2].status == "review"
    assert ("Import Violations", 1) in cards[2].metrics
    assert cards[3].status == "report-only"
    assert ("Order Hotspots", 1) in cards[3].metrics
    assert cards[3].hotspots == ("Order Hotspots: src/runtime.py:L10 -> order",)


def test_collect_dashboard_hotspot_sections_limits_items() -> None:
    payload = {
        "trading_safety": {
            "order_hotspots": ["one", "two", "three"],
        }
    }

    sections = collect_dashboard_hotspot_sections(payload, hotspot_limit=2)

    assert len(sections) == 1
    assert sections[0].title == "Trading Safety"
    assert sections[0].items == (
        "Order Hotspots: one",
        "Order Hotspots: two",
    )


def test_main_writes_dashboard_html(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    project_root = tmp_path / "project"
    output_path = tmp_path / "dashboard.html"
    (project_root / "src").mkdir(parents=True)
    (project_root / "src" / "included.py").write_text("", encoding="utf-8")

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "project_dashboard.py",
            str(project_root),
            "--output",
            str(output_path),
        ],
    )

    main()

    captured = capsys.readouterr()
    assert "Dashboard written to" in captured.out
    assert output_path.exists()
    assert "Project Analysis Dashboard" in output_path.read_text(encoding="utf-8")
