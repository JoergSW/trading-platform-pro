from __future__ import annotations

import argparse
import ast
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".idea",
    ".vscode",
    ".tox",
    "temp",
}

EXCLUDED_PATH_PREFIXES = {
    ("docs", "generated"),
}

IMPORTANT_PATHS = (
    "AGENTS.md",
    "README.md",
    "pyproject.toml",
    "src",
    "tests",
    "docs",
    "scripts",
    "tools",
)

IMPORTANT_DOCUMENTATION_PATHS = (
    "AGENTS.md",
    "docs/product/Product_Vision.md",
    "docs/product/Product_Roadmap.md",
    "docs/product/Project_Overview.md",
    "docs/specifications/Technical_Specifications.md",
    "docs/specifications/Widget_Catalog.md",
    "docs/architecture/Architecture.md",
    "docs/architecture/Domain_Model.md",
    "docs/architecture/Infrastructure.md",
    "docs/architecture/Project_Structure.md",
    "docs/api/API_Guidelines.md",
    "docs/operations/Configuration.md",
    "docs/operations/Runtime.md",
    "docs/operations/Logging.md",
    "docs/operations/Monitoring.md",
    "docs/operations/CI_CD.md",
    "docs/developer/Coding_Standards.md",
    "docs/developer/Development_Guidelines.md",
    "docs/developer/Git_Workflow.md",
    "docs/developer/Testing_Strategy.md",
    "docs/developer/AI_Agent_Guide.md",
    "docs/decisions/Decision_Log.md",
    "docs/decisions/Roadmap.md",
    "docs/adr/README.md",
    "docs/ui/UI_Guidelines.md",
    "docs/user/User_Guide.md",
)

PLACEHOLDER_MARKERS = (
    "project specific content",
    "todo",
    "tbd",
    "placeholder",
    "coming soon",
    "to be defined",
)

PROJECT_PACKAGE = "trading_platform"
DOMAIN_PACKAGE = f"{PROJECT_PACKAGE}.domain"
APPLICATION_PACKAGE = f"{PROJECT_PACKAGE}.application"
INFRASTRUCTURE_PACKAGE = f"{PROJECT_PACKAGE}.infrastructure"
PRESENTATION_PACKAGE = f"{PROJECT_PACKAGE}.presentation"

DOMAIN_FORBIDDEN_IMPORT_PREFIXES = (
    INFRASTRUCTURE_PACKAGE,
    PRESENTATION_PACKAGE,
    "sqlalchemy",
    "PySide6",
    "PyQt5",
    "PyQt6",
    "ib_insync",
    "ibapi",
)

APPLICATION_FORBIDDEN_IMPORT_PREFIXES = (PRESENTATION_PACKAGE,)


@dataclass(frozen=True)
class DocumentationCheckReport:
    docs_directory_present: bool
    agents_file_present: bool
    documentation_markdown_files: int
    present_important_documentation_paths: tuple[str, ...]
    missing_important_documentation_paths: tuple[str, ...]
    empty_markdown_files: tuple[str, ...]
    placeholder_markdown_files: tuple[str, ...]


@dataclass(frozen=True)
class ArchitectureCheckReport:
    architecture_source_files: int
    domain_files: int
    application_files: int
    domain_import_violations: tuple[str, ...]
    application_import_violations: tuple[str, ...]
    parse_errors: tuple[str, ...]


@dataclass(frozen=True)
class ProjectAnalysisReport:
    root: Path
    total_files: int
    python_files: int
    markdown_files: int
    source_files: int
    test_files: int
    documentation_files: int
    script_files: int
    tool_files: int
    present_important_paths: tuple[str, ...]
    missing_important_paths: tuple[str, ...]
    documentation: DocumentationCheckReport
    architecture: ArchitectureCheckReport


def _has_excluded_prefix(relative_path: Path) -> bool:
    parts = relative_path.parts

    return any(parts[: len(prefix)] == prefix for prefix in EXCLUDED_PATH_PREFIXES)


def should_include_path(path: Path, root: Path) -> bool:
    relative_path = path.relative_to(root)

    if any(part in EXCLUDED_DIRS for part in relative_path.parts):
        return False

    return not _has_excluded_prefix(relative_path)


def iter_project_files(root: Path) -> Iterable[Path]:
    resolved_root = root.resolve()

    for path in sorted(resolved_root.rglob("*")):
        if path.is_file() and should_include_path(path, resolved_root):
            yield path


def _is_under(relative_path: Path, directory: str) -> bool:
    return len(relative_path.parts) > 1 and relative_path.parts[0] == directory


def _is_under_package(relative_path: Path, package_parts: tuple[str, ...]) -> bool:
    return relative_path.parts[: len(package_parts)] == package_parts


def _to_posix(relative_path: Path) -> str:
    return relative_path.as_posix()


def _read_markdown_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _read_python_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _is_placeholder_markdown(path: Path) -> bool:
    text = _read_markdown_text(path).strip().lower()

    if not text:
        return False

    return any(marker in text for marker in PLACEHOLDER_MARKERS)


def _build_documentation_report(
    root: Path, relative_files: tuple[Path, ...]
) -> DocumentationCheckReport:
    markdown_files = tuple(path for path in relative_files if path.suffix == ".md")
    documentation_markdown_files = tuple(
        path for path in markdown_files if _is_under(path, "docs")
    )

    present_important_documentation_paths = tuple(
        documentation_path
        for documentation_path in IMPORTANT_DOCUMENTATION_PATHS
        if (root / documentation_path).exists()
    )
    missing_important_documentation_paths = tuple(
        documentation_path
        for documentation_path in IMPORTANT_DOCUMENTATION_PATHS
        if not (root / documentation_path).exists()
    )

    empty_markdown_files = tuple(
        _to_posix(path)
        for path in markdown_files
        if not _read_markdown_text(root / path).strip()
    )
    placeholder_markdown_files = tuple(
        _to_posix(path)
        for path in markdown_files
        if _is_placeholder_markdown(root / path)
    )

    return DocumentationCheckReport(
        docs_directory_present=(root / "docs").is_dir(),
        agents_file_present=(root / "AGENTS.md").is_file(),
        documentation_markdown_files=len(documentation_markdown_files),
        present_important_documentation_paths=present_important_documentation_paths,
        missing_important_documentation_paths=missing_important_documentation_paths,
        empty_markdown_files=empty_markdown_files,
        placeholder_markdown_files=placeholder_markdown_files,
    )


def _module_name_from_path(relative_path: Path) -> str:
    if relative_path.suffix != ".py":
        raise ValueError(f"Not a Python file: {relative_path}")

    without_suffix = relative_path.with_suffix("")
    parts = without_suffix.parts

    if parts and parts[0] == "src":
        parts = parts[1:]

    return ".".join(parts)


def _resolve_relative_import(
    module_name: str, import_module: str | None, level: int
) -> str:
    if level == 0:
        return import_module or ""

    module_parts = module_name.split(".")
    package_parts = module_parts[:-1]
    keep_count = max(len(package_parts) - level + 1, 0)
    resolved_parts = package_parts[:keep_count]

    if import_module:
        resolved_parts.extend(import_module.split("."))

    return ".".join(part for part in resolved_parts if part)


def _iter_imported_modules(tree: ast.AST, module_name: str) -> Iterable[str]:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom):
            yield _resolve_relative_import(module_name, node.module, node.level)


def _matches_prefix(module_name: str, prefixes: tuple[str, ...]) -> bool:
    return any(
        module_name == prefix or module_name.startswith(f"{prefix}.")
        for prefix in prefixes
    )


def _format_violation(relative_path: Path, imported_module: str) -> str:
    return f"{_to_posix(relative_path)} -> {imported_module}"


def _build_architecture_report(
    root: Path, relative_files: tuple[Path, ...]
) -> ArchitectureCheckReport:
    python_files = tuple(
        path
        for path in relative_files
        if path.suffix == ".py" and _is_under(path, "src")
    )
    domain_package_parts = ("src", PROJECT_PACKAGE, "domain")
    application_package_parts = ("src", PROJECT_PACKAGE, "application")
    domain_files = tuple(
        path for path in python_files if _is_under_package(path, domain_package_parts)
    )
    application_files = tuple(
        path
        for path in python_files
        if _is_under_package(path, application_package_parts)
    )

    domain_import_violations: list[str] = []
    application_import_violations: list[str] = []
    parse_errors: list[str] = []

    for relative_path in (*domain_files, *application_files):
        absolute_path = root / relative_path
        module_name = _module_name_from_path(relative_path)

        try:
            tree = ast.parse(
                _read_python_text(absolute_path), filename=str(absolute_path)
            )
        except SyntaxError as exc:
            parse_errors.append(f"{_to_posix(relative_path)} -> {exc.msg}")
            continue

        imported_modules = tuple(_iter_imported_modules(tree, module_name))

        if relative_path in domain_files:
            domain_import_violations.extend(
                _format_violation(relative_path, imported_module)
                for imported_module in imported_modules
                if _matches_prefix(imported_module, DOMAIN_FORBIDDEN_IMPORT_PREFIXES)
            )

        if relative_path in application_files:
            application_import_violations.extend(
                _format_violation(relative_path, imported_module)
                for imported_module in imported_modules
                if _matches_prefix(
                    imported_module, APPLICATION_FORBIDDEN_IMPORT_PREFIXES
                )
            )

    return ArchitectureCheckReport(
        architecture_source_files=len(python_files),
        domain_files=len(domain_files),
        application_files=len(application_files),
        domain_import_violations=tuple(domain_import_violations),
        application_import_violations=tuple(application_import_violations),
        parse_errors=tuple(parse_errors),
    )


def analyze_project(root: Path) -> ProjectAnalysisReport:
    resolved_root = root.resolve()

    if not resolved_root.exists():
        raise ValueError(f"Project root does not exist: {resolved_root}")

    if not resolved_root.is_dir():
        raise ValueError(f"Project root is not a directory: {resolved_root}")

    files = tuple(iter_project_files(resolved_root))
    relative_files = tuple(path.relative_to(resolved_root) for path in files)

    present_important_paths = tuple(
        important_path
        for important_path in IMPORTANT_PATHS
        if (resolved_root / important_path).exists()
    )
    missing_important_paths = tuple(
        important_path
        for important_path in IMPORTANT_PATHS
        if not (resolved_root / important_path).exists()
    )

    return ProjectAnalysisReport(
        root=resolved_root,
        total_files=len(files),
        python_files=sum(path.suffix == ".py" for path in relative_files),
        markdown_files=sum(path.suffix == ".md" for path in relative_files),
        source_files=sum(_is_under(path, "src") for path in relative_files),
        test_files=sum(_is_under(path, "tests") for path in relative_files),
        documentation_files=sum(_is_under(path, "docs") for path in relative_files),
        script_files=sum(_is_under(path, "scripts") for path in relative_files),
        tool_files=sum(_is_under(path, "tools") for path in relative_files),
        present_important_paths=present_important_paths,
        missing_important_paths=missing_important_paths,
        documentation=_build_documentation_report(resolved_root, relative_files),
        architecture=_build_architecture_report(resolved_root, relative_files),
    )


def _format_items(items: tuple[str, ...]) -> str:
    if not items:
        return "none"

    return ", ".join(items)


def _format_bool(value: bool) -> str:
    return "yes" if value else "no"


def render_report(report: ProjectAnalysisReport) -> str:
    documentation = report.documentation
    architecture = report.architecture
    lines = [
        "Read-only Project Analysis Agent",
        "================================",
        f"Project root: {report.root}",
        "",
        "File counts:",
        f"- total files: {report.total_files}",
        f"- Python files: {report.python_files}",
        f"- Markdown files: {report.markdown_files}",
        f"- source files: {report.source_files}",
        f"- test files: {report.test_files}",
        f"- documentation files: {report.documentation_files}",
        f"- script files: {report.script_files}",
        f"- tool files: {report.tool_files}",
        "",
        "Important paths:",
        f"- present: {_format_items(report.present_important_paths)}",
        f"- missing: {_format_items(report.missing_important_paths)}",
        "",
        "Documentation checks:",
        (
            "- docs directory present: "
            f"{_format_bool(documentation.docs_directory_present)}"
        ),
        f"- AGENTS.md present: {_format_bool(documentation.agents_file_present)}",
        (
            "- documentation Markdown files: "
            f"{documentation.documentation_markdown_files}"
        ),
        "- important docs present: "
        f"{_format_items(documentation.present_important_documentation_paths)}",
        "- important docs missing: "
        f"{_format_items(documentation.missing_important_documentation_paths)}",
        f"- empty Markdown files: {_format_items(documentation.empty_markdown_files)}",
        "- placeholder Markdown files: "
        f"{_format_items(documentation.placeholder_markdown_files)}",
        "- generated docs ignored: yes",
        "",
        "Architecture checks:",
        f"- source Python files checked: {architecture.architecture_source_files}",
        f"- domain files checked: {architecture.domain_files}",
        f"- application files checked: {architecture.application_files}",
        "- domain import violations: "
        f"{_format_items(architecture.domain_import_violations)}",
        "- application import violations: "
        f"{_format_items(architecture.application_import_violations)}",
        f"- Python parse errors: {_format_items(architecture.parse_errors)}",
        "",
        "Safety:",
        "- mode: read-only",
        "- file writes: disabled",
        "- broker access: disabled",
        "- trading access: disabled",
        "- LIVE access: disabled",
    ]

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a read-only project structure analysis."
    )
    parser.add_argument(
        "project_root",
        nargs="?",
        default=".",
        help="Project root directory. Defaults to the current working directory.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = analyze_project(Path(args.project_root))
    print(render_report(report))


if __name__ == "__main__":
    main()
