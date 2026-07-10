from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Any

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from project_analysis_agent import analyze_project, report_to_dict  # noqa: E402

HOTSPOT_FIELD_MARKERS = ("hotspot", "violation", "finding", "parse_error")
DASHBOARD_SECTION_ORDER = (
    "documentation",
    "architecture",
    "trading_safety",
    "runtime_entrypoints",
    "external_interfaces",
    "cicd_workflows",
    "risk_strategy_decisions",
    "cockpit_ui_surfaces",
    "security_secrets",
    "operations_runbooks",
)
DEFAULT_HOTSPOT_LIMIT = 8


@dataclass(frozen=True)
class DashboardListSection:
    title: str
    items: tuple[str, ...]


def _as_mapping(value: object) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value

    return {}


def _as_list(value: object) -> list[object]:
    if isinstance(value, list):
        return value

    return []


def _format_title(value: str) -> str:
    return value.replace("_", " ").replace("/", " / ").title()


def _is_hotspot_field(field_name: str) -> bool:
    return any(marker in field_name for marker in HOTSPOT_FIELD_MARKERS)


def _stringify_item(value: object) -> str:
    if isinstance(value, str):
        return value

    return json.dumps(value, sort_keys=True)


def collect_dashboard_hotspot_sections(
    payload: Mapping[str, Any], hotspot_limit: int = DEFAULT_HOTSPOT_LIMIT
) -> tuple[DashboardListSection, ...]:
    sections: list[DashboardListSection] = []

    for section_key in DASHBOARD_SECTION_ORDER:
        section = _as_mapping(payload.get(section_key))
        items: list[str] = []

        for field_name, field_value in section.items():
            if not _is_hotspot_field(field_name):
                continue

            for value in _as_list(field_value):
                items.append(f"{_format_title(field_name)}: {_stringify_item(value)}")

        if items:
            sections.append(
                DashboardListSection(
                    title=_format_title(section_key),
                    items=tuple(items[:hotspot_limit]),
                )
            )

    return tuple(sections)


def _render_metric_card(label: str, value: object) -> str:
    return (
        '<div class="metric-card">'
        f'<div class="metric-label">{escape(label)}</div>'
        f'<div class="metric-value">{escape(str(value))}</div>'
        "</div>"
    )


def _render_list(items: list[object] | tuple[object, ...]) -> str:
    if not items:
        return '<p class="muted">none</p>'

    rendered_items = "".join(
        f"<li>{escape(_stringify_item(item))}</li>" for item in items
    )
    return f"<ul>{rendered_items}</ul>"


def _render_file_counts(file_counts: Mapping[str, Any]) -> str:
    cards = "".join(
        _render_metric_card(_format_title(key), value)
        for key, value in file_counts.items()
    )
    return (
        '<section class="card"><h2>File Counts</h2>'
        f'<div class="grid">{cards}</div></section>'
    )


def _render_safety(safety: Mapping[str, Any]) -> str:
    cards = "".join(
        _render_metric_card(_format_title(key), value) for key, value in safety.items()
    )
    return (
        '<section class="card"><h2>Safety Mode</h2>'
        f'<div class="grid">{cards}</div></section>'
    )


def _render_quality_gate(quality_gate: Mapping[str, Any]) -> str:
    passed = bool(quality_gate.get("passed"))
    status = "passed" if passed else "failed"
    failures = _as_list(quality_gate.get("critical_failures"))
    return (
        '<section class="card">'
        "<h2>Quality Gate</h2>"
        f'<p class="status status-{status}">Quality Gate: {status}</p>'
        f"{_render_list(failures)}"
        "</section>"
    )


def _render_hotspots(sections: tuple[DashboardListSection, ...]) -> str:
    if not sections:
        return (
            '<section class="card"><h2>Important Hotspots</h2>'
            '<p class="muted">none</p></section>'
        )

    rendered_sections = "".join(
        f"<h3>{escape(section.title)}</h3>{_render_list(section.items)}"
        for section in sections
    )
    return (
        '<section class="card"><h2>Important Hotspots</h2>'
        f"{rendered_sections}</section>"
    )


def render_dashboard_html(
    payload: Mapping[str, Any], hotspot_limit: int = DEFAULT_HOTSPOT_LIMIT
) -> str:
    root = str(payload.get("root", "unknown"))
    file_counts = _as_mapping(payload.get("file_counts"))
    quality_gate = _as_mapping(payload.get("quality_gate"))
    safety = _as_mapping(payload.get("safety"))
    hotspot_sections = collect_dashboard_hotspot_sections(payload, hotspot_limit)

    return "\n".join(
        (
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            "<title>Project Analysis Dashboard</title>",
            "<style>",
            "body{font-family:Arial,sans-serif;margin:2rem;"
            "background:#f6f7f9;color:#18202a}",
            ".card{background:white;border:1px solid #d8dee8;"
            "border-radius:12px;padding:1rem;margin:1rem 0}",
            ".grid{display:grid;grid-template-columns:"
            "repeat(auto-fit,minmax(150px,1fr));gap:.75rem}",
            ".metric-card{background:#f9fafb;border:1px solid #e5e7eb;"
            "border-radius:10px;padding:.75rem}",
            ".metric-label{font-size:.8rem;color:#657083;text-transform:uppercase}",
            ".metric-value{font-size:1.25rem;font-weight:700;margin-top:.25rem}",
            ".status{display:inline-block;border-radius:999px;"
            "padding:.35rem .7rem;font-weight:700}",
            ".status-passed{background:#e7f7ec;color:#146c2e}",
            ".status-failed{background:#fdecec;color:#9f1d1d}",
            ".muted{color:#657083}",
            "li{margin:.35rem 0}",
            "</style>",
            "</head>",
            "<body>",
            "<main>",
            "<h1>Project Analysis Dashboard</h1>",
            f'<p class="muted">Root: {escape(root)}</p>',
            _render_quality_gate(quality_gate),
            _render_file_counts(file_counts),
            _render_safety(safety),
            _render_hotspots(hotspot_sections),
            "</main>",
            "</body>",
            "</html>",
        )
    )


def build_dashboard_payload(project_root: Path) -> dict[str, object]:
    return report_to_dict(analyze_project(project_root))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render a minimal Project Analysis HTML dashboard."
    )
    parser.add_argument(
        "project_root",
        nargs="?",
        default=".",
        help="Project root directory. Defaults to the current working directory.",
    )
    parser.add_argument(
        "--output",
        default="temp/project-dashboard.html",
        help="Output HTML path. Use '-' to print to stdout.",
    )
    parser.add_argument(
        "--hotspot-limit",
        type=int,
        default=DEFAULT_HOTSPOT_LIMIT,
        help="Maximum number of hotspot rows per section.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = build_dashboard_payload(Path(args.project_root))
    rendered_html = render_dashboard_html(payload, hotspot_limit=args.hotspot_limit)

    if args.output == "-":
        print(rendered_html)
        return

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered_html, encoding="utf-8")
    print(f"Dashboard written to {output_path.resolve()}")


if __name__ == "__main__":
    main()
