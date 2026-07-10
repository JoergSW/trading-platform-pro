from __future__ import annotations

import argparse
import ast
import json
import re
import tomllib
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

ORDER_TERMS = (
    "order",
    "orders",
    "submission",
    "submit",
    "submitted",
    "cancel",
    "cancellation",
)
BROKER_TERMS = (
    "broker",
    "brokers",
    "ibkr",
    "ib_insync",
    "ibapi",
    "interactivebrokers",
)
LIVE_TERMS = (
    "live",
    "paper",
    "environment",
    "account",
)
RETRY_TERMS = (
    "retry",
    "retries",
    "timeout",
    "timeouts",
    "disconnect",
    "reconnect",
)
RECONCILIATION_TERMS = (
    "reconciliation",
    "reconcile",
    "reconciled",
    "discrepancy",
    "discrepancies",
)
EXECUTION_TERMS = (
    "execution",
    "executions",
    "fill",
    "fills",
    "filled",
    "partial",
)

TRADING_SAFETY_TERMS = (
    *ORDER_TERMS,
    *BROKER_TERMS,
    *LIVE_TERMS,
    *RETRY_TERMS,
    *RECONCILIATION_TERMS,
    *EXECUTION_TERMS,
)

HIGH_COUPLING_THRESHOLD = 5
TEST_CATEGORY_DIRS = (
    "unit",
    "integration",
    "regression",
    "system",
    "architecture",
    "smoke",
    "performance",
)
EXPECTED_CONFIGURATION_PATHS = (
    ".env.example",
    "config/development.yaml",
    "config/paper.yaml",
    "config/live.yaml",
)
CONFIG_FILE_SUFFIXES = (".env", ".yaml", ".yml", ".toml")
CONFIG_FILE_NAMES = (".env.example", "pyproject.toml")
ENVIRONMENT_TERMS = (
    "APP_ENV",
    "environment",
    "profile",
    "development",
    "paper",
    "live",
)
SECRET_REFERENCE_TERMS = (
    "secret",
    "secrets",
    "password",
    "passwd",
    "credential",
    "credentials",
    "token",
    "api_key",
    "apikey",
    "account",
)
SECRET_VALUE_MARKERS = (
    "example",
    "placeholder",
    "changeme",
    "change_me",
    "dummy",
    "test",
    "none",
    "null",
    "",
)
RUNTIME_ENTRYPOINT_DIRECTORIES = ("src", "scripts", "tools")
CLI_IMPORT_ROOTS = ("argparse", "click", "typer")
CLI_CALL_NAMES = ("ArgumentParser", "command", "group", "Typer")
RUNTIME_DEFAULT_TERMS = (
    "default",
    "defaults",
    "mode",
    "environment",
    "paper",
    "live",
    "debug",
    "dry_run",
    "host",
    "port",
)
DEPENDENCY_FILE_PREFIXES = ("requirements",)
DEPENDENCY_FILE_SUFFIXES = (".txt", ".in")
LOCK_FILE_NAMES = (
    "requirements.lock",
    "uv.lock",
    "poetry.lock",
    "Pipfile.lock",
    "pdm.lock",
)
DEPENDENCY_VERSION_MARKERS = ("===", "==", ">=", "<=", "~=", "!=", ">", "<")
REQUIREMENT_OPTION_PREFIXES = (
    "--index-url",
    "--extra-index-url",
    "--find-links",
    "--trusted-host",
    "--constraint",
    "-c",
    "--requirement",
    "-r",
)
PACKAGING_TOOL_SECTION_PREFIXES = (
    "build-system",
    "project",
    "project.optional-dependencies",
    "tool.setuptools",
    "tool.poetry",
    "tool.hatch",
    "tool.pytest",
    "tool.ruff",
    "tool.mypy",
)
PERSISTENCE_DATABASE_FILE_SUFFIXES = (".db", ".sqlite", ".sqlite3")
PERSISTENCE_SCHEMA_FILE_NAMES = ("schema.sql", "database.sql")
PERSISTENCE_DIRECTORY_NAMES = (
    "data",
    "state",
    "db",
    "database",
    "storage",
    "migrations",
    "alembic",
)
MIGRATION_DIRECTORY_NAMES = ("migrations", "alembic")
MIGRATION_FILE_SUFFIXES = (".sql", ".py")
PERSISTENCE_TEXT_FILE_SUFFIXES = (".py", ".sql")
PERSISTENCE_IMPORT_TERMS = ("sqlite3", "sqlalchemy", "alembic")
PERSISTENCE_WRITE_TERMS = (
    "write",
    "save",
    "insert",
    "update",
    "delete",
    "remove",
    "commit",
    "rollback",
    "transaction",
    "execute",
    "executemany",
)
PERSISTENCE_TRADING_STATE_TERMS = (
    "settlement",
    "settled",
    "position",
    "positions",
    "order",
    "orders",
    "state",
    "status",
    "intent",
    "trade",
    "fill",
    "fills",
)
OBSERVABILITY_TEXT_FILE_SUFFIXES = (
    ".py",
    ".md",
    ".yaml",
    ".yml",
    ".toml",
    ".json",
)
OBSERVABILITY_DIRECTORY_NAMES = (
    "logs",
    "log",
    "audit",
    "monitoring",
    "metrics",
    "observability",
)
OBSERVABILITY_FILE_NAME_TERMS = (
    "log",
    "logging",
    "audit",
    "monitoring",
    "metrics",
    "metric",
    "telemetry",
    "observability",
)
LOGGING_CONFIG_FILE_NAMES = (
    "logging.yaml",
    "logging.yml",
    "logging.toml",
    "logging.json",
)
LOGGING_IMPORT_TERMS = ("logging", "loguru", "structlog")
LOGGING_CALL_NAMES = (
    "debug",
    "info",
    "warning",
    "warn",
    "error",
    "exception",
    "critical",
    "log",
    "getLogger",
)
OBSERVABILITY_CRITICAL_EVENT_TERMS = (
    "audit",
    "metric",
    "metrics",
    "monitor",
    "monitoring",
    "heartbeat",
    "health",
    "error",
    "errors",
    "exception",
    "exceptions",
    "critical",
    "order",
    "orders",
    "broker",
    "live",
    "paper",
    "retry",
    "timeout",
    "disconnect",
    "reconnect",
    "reconciliation",
    "execution",
    "fill",
    "fills",
    "filled",
    "settlement",
    "settled",
    "position",
    "positions",
    "state",
    "status",
    "intent",
    "trade",
)
EXTERNAL_BROKER_IMPORT_PREFIXES = ("ib_insync", "ibapi")
EXTERNAL_NETWORK_IMPORT_PREFIXES = (
    "requests",
    "httpx",
    "urllib",
    "socket",
    "websocket",
    "aiohttp",
)
EXTERNAL_INTERFACE_IMPORT_PREFIXES = (
    *EXTERNAL_BROKER_IMPORT_PREFIXES,
    *EXTERNAL_NETWORK_IMPORT_PREFIXES,
)
EXTERNAL_INTERFACE_FILE_NAME_TERMS = (
    "broker",
    "gateway",
    "adapter",
    "client",
    "api",
    "http",
    "socket",
    "ibkr",
    "tws",
)
EXTERNAL_BROKER_TERMS = (*BROKER_TERMS, "tws", "gateway")
EXTERNAL_NETWORK_TERMS = (
    "http",
    "https",
    "url",
    "endpoint",
    "host",
    "port",
    "socket",
    "connect",
    "disconnect",
    "client",
)
INTERFACE_ORDER_EXECUTION_TERMS = (*ORDER_TERMS, *EXECUTION_TERMS)
CICD_WORKFLOW_SUFFIXES = (".yaml", ".yml")
CICD_TRIGGER_TERMS = ("on", "push", "pull_request", "workflow_dispatch", "schedule")
CICD_JOB_TERMS = ("jobs", "runs-on", "steps", "matrix")
CICD_ACTION_USAGE_TERMS = (
    "uses",
    "actions/checkout",
    "actions/setup-python",
    "actions/upload-artifact",
    "actions/download-artifact",
)
CICD_RUN_COMMAND_TERMS = (
    "run",
    "python",
    "pip",
    "pytest",
    "ruff",
    "mypy",
    "pre-commit",
)
CICD_QUALITY_GATE_TERMS = (
    "project_analysis_agent.py",
    "--fail-on-critical",
    "project-analysis-agent-report",
    "quality gate",
    "json.tool",
)
CICD_RISKY_DEPLOY_PUBLISH_TERMS = (
    "deploy",
    "publish",
    "release",
    "twine",
    "pypi",
    "docker",
)
CICD_SECRET_USAGE_TERMS = (
    "secrets",
    "token",
    "password",
    "credential",
    "credentials",
    "api_key",
    "apikey",
)
CICD_PERMISSION_TERMS = ("permissions", "contents", "packages", "id-token")
CICD_TRADING_BROKER_LIVE_TERMS = (
    *BROKER_TERMS,
    *LIVE_TERMS,
    *ORDER_TERMS,
    *EXECUTION_TERMS,
    "trading",
)
TIME_SCHEDULE_IMPORT_PREFIXES = (
    "datetime",
    "time",
    "zoneinfo",
    "pytz",
    "dateutil",
    "calendar",
    "asyncio",
    "sched",
    "threading",
    "apscheduler",
)
TIME_SCHEDULE_FILE_NAME_TERMS = (
    "clock",
    "datetime",
    "timezone",
    "calendar",
    "schedule",
    "scheduler",
    "settlement",
    "expiry",
    "expiration",
)
TIMEZONE_TERMS = (
    "timezone",
    "tzinfo",
    "zoneinfo",
    "pytz",
    "utc",
    "America/New_York",
    "New_York",
)
SCHEDULE_TIMER_TERMS = (
    "schedule",
    "scheduler",
    "sleep",
    "loop",
    "timer",
    "interval",
    "delay",
    "cron",
    "wait",
    "timeout",
    "heartbeat",
)
MARKET_CALENDAR_TERMS = (
    "market",
    "market_open",
    "market_close",
    "trading_day",
    "session",
    "holiday",
    "weekday",
    "calendar",
)
EXPIRY_SETTLEMENT_TERMS = (
    "expiry",
    "expiration",
    "expire",
    "settlement",
    "settled",
    "settle",
    "trading_day",
)
RISK_STRATEGY_FILE_NAME_TERMS = (
    "risk",
    "strategy",
    "strategies",
    "regime",
    "decision",
    "signal",
    "sizing",
    "entry",
    "exit",
    "pnl",
    "position",
)
STRATEGY_DECISION_TERMS = (
    "strategy",
    "strategies",
    "regime",
    "regimes",
    "signal",
    "signals",
    "decision",
    "decisions",
    "decide",
    "select",
    "selected",
    "candidate",
    "candidates",
    "rationale",
)
RISK_LIMIT_SIZING_TERMS = (
    "risk",
    "limit",
    "limits",
    "sizing",
    "size",
    "qty",
    "quantity",
    "exposure",
    "notional",
    "margin",
    "drawdown",
    "stop",
    "loss",
)
ENTRY_EXIT_DECISION_TERMS = (
    "entry",
    "entries",
    "exit",
    "exits",
    "open",
    "close",
    "buy",
    "sell",
    "debit",
    "credit",
    "spread",
)
PNL_POSITION_STATE_TERMS = (
    "pnl",
    "profit",
    "loss",
    "settlement",
    "settled",
    "position",
    "positions",
    "order",
    "orders",
    "fill",
    "fills",
    "status",
    "state",
)
AUTO_DECISION_TERMS = (
    "auto",
    "automatic",
    "automatically",
    "decide",
    "select",
    "selected",
    "execute",
    "execution",
    "place_order",
    "submit_order",
    "open_trade",
)
COCKPIT_UI_FILE_NAME_TERMS = (
    "cockpit",
    "ui",
    "view",
    "views",
    "widget",
    "widgets",
    "screen",
    "panel",
    "dashboard",
    "form",
    "button",
)
UI_FRAMEWORK_IMPORT_PREFIXES = (
    "streamlit",
    "dash",
    "panel",
    "gradio",
    "tkinter",
    "PySide6",
    "PyQt6",
    "textual",
    "rich",
)
UI_SURFACE_TERMS = (
    "cockpit",
    "dashboard",
    "view",
    "widget",
    "panel",
    "screen",
    "render",
    "display",
)
UI_ACTION_TERMS = (
    "button",
    "click",
    "clicked",
    "submit",
    "action",
    "handler",
    "callback",
    "form",
    "input",
)
READ_ONLY_UI_TERMS = (
    "read_only",
    "readonly",
    "read-only",
    "disabled",
    "dry_run",
    "preview",
)
UI_TRADING_TERMS = (
    *BROKER_TERMS,
    *LIVE_TERMS,
    *ORDER_TERMS,
    *EXECUTION_TERMS,
    "trade",
    "trading",
)
DIRECT_TRADING_ACTION_TERMS = (
    "place_order",
    "submit_order",
    "send_order",
    "execute_order",
    "open_trade",
    "close_trade",
    "buy",
    "sell",
)
DATA_ARTIFACT_FILE_SUFFIXES = (
    ".csv",
    ".json",
    ".jsonl",
    ".xlsx",
    ".xls",
    ".pdf",
    ".docx",
    ".parquet",
    ".feather",
    ".pkl",
    ".pickle",
    ".db",
    ".sqlite",
    ".sqlite3",
    ".html",
)
DATA_ARTIFACT_DIRECTORY_NAMES = (
    "generated",
    "exports",
    "export",
    "artifacts",
    "artifact",
    "reports",
    "report",
    "output",
    "outputs",
    "data",
    "state",
    "temp",
    "runtime",
    "logs",
    "snapshots",
)
TEST_DATA_DIRECTORY_NAMES = (
    "tests",
    "fixtures",
    "fixture",
    "samples",
    "sample",
    "testdata",
    "test_data",
)
RUNTIME_ARTIFACT_DIRECTORY_NAMES = (
    "data",
    "state",
    "temp",
    "runtime",
    "logs",
    "exports",
    "output",
    "outputs",
)
REPORT_ARTIFACT_TERMS = (
    "report",
    "reports",
    "statement",
    "activity",
    "export",
    "exports",
    "generated",
    "artifact",
    "artifacts",
)
SENSITIVE_ARTIFACT_TERMS = (
    "account",
    "konto",
    "order",
    "orders",
    "pnl",
    "profit",
    "loss",
    "cash",
    "broker",
    "ibkr",
    "trade",
    "trades",
    "fill",
    "fills",
    "position",
    "positions",
    "settlement",
    "statement",
    "activity",
    "portfolio",
    "balance",
)
DATA_ARTIFACT_METADATA_EXCLUDED_DIRS = (
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".idea",
    ".vscode",
    ".tox",
)
RELEASE_VERSION_FILE_NAMES = ("VERSION", "CHANGELOG.md", "README.md", "pyproject.toml")
RELEASE_VERSION_SCAN_SUFFIXES = (".md", ".toml", ".txt")
RELEASE_TAG_TERMS = ("release", "released", "tag", "tags", "changelog")
PRERELEASE_TERMS = (
    "alpha",
    "beta",
    "rc",
    "release candidate",
    "pre-release",
    "prerelease",
)
VERSION_REFERENCE_PATTERN = (
    r"\bv?\d+\.\d+(?:\.\d+)?"
    r"(?:[-.]?(?:alpha|beta|rc)\.?\d+|[ab]\d+)?\b"
)
SECURITY_SECRET_TEXT_FILE_SUFFIXES = (
    ".py",
    ".md",
    ".yaml",
    ".yml",
    ".toml",
    ".json",
    ".txt",
    ".ini",
    ".cfg",
)
SECURITY_SECRET_FILE_SUFFIXES = (".pem", ".key", ".crt", ".cer", ".p12", ".pfx")
SECURITY_SECRET_FILE_NAME_TERMS = (
    "secret",
    "secrets",
    "credential",
    "credentials",
    "token",
    "password",
    "passwd",
    "api_key",
    "apikey",
    "account",
    "key",
    "cert",
    "certificate",
    "pem",
    "env",
)
SECURITY_SECRET_KEY_TERMS = (
    *SECRET_REFERENCE_TERMS,
    "private_key",
    "client_secret",
    "access_token",
    "refresh_token",
    "bearer",
    "authorization",
    "auth",
    "broker_token",
    "ibkr",
)
SECURITY_ACCOUNT_BROKER_TERMS = (
    "account",
    "konto",
    "broker",
    "ibkr",
    "tws",
    "api_key",
    "token",
    "credential",
    "credentials",
)
SECURITY_HARDCODED_SECRET_VALUE_EXCLUSIONS = (
    "os.environ",
    "os.getenv",
    "${{ secrets.",
    "getenv(",
    "env.",
    "settings.",
    "config.",
    "example",
    "placeholder",
    "changeme",
    "change_me",
    "dummy",
    "test",
    "none",
    "null",
    "",
)
SECURITY_GITIGNORE_SECRET_PATTERNS = (
    ".env",
    "*.pem",
    "*.key",
    "*.crt",
    "*.p12",
    "*.pfx",
)
OPERATIONS_RUNBOOK_TEXT_FILE_SUFFIXES = (".md", ".txt", ".yaml", ".yml", ".toml", ".py")
OPERATIONS_RUNBOOK_FILE_NAME_TERMS = (
    "runbook",
    "operations",
    "operation",
    "recovery",
    "recover",
    "rollback",
    "restart",
    "runtime",
    "manual",
    "troubleshooting",
    "incident",
    "settlement",
    "reconciliation",
)
OPERATIONS_COMMAND_TERMS = (
    "python",
    "pytest",
    "ruff",
    "git",
    "pip",
    "pre-commit",
    "docker",
    "make",
    "uv",
    "poetry",
    "hatch",
)
OPERATIONS_START_STOP_RESTART_TERMS = (
    "start",
    "stop",
    "restart",
    "run",
    "execute",
    "launch",
    "shutdown",
)
OPERATIONS_RECOVERY_ROLLBACK_TERMS = (
    "recover",
    "recovery",
    "rollback",
    "restore",
    "manual",
    "settlement",
    "reconciliation",
    "reconcile",
    "incident",
)
OPERATIONS_DESTRUCTIVE_COMMAND_TERMS = (
    "rm",
    "remove",
    "delete",
    "del",
    "drop",
    "truncate",
    "reset",
    "clean",
    "purge",
    "rmdir",
    "unlink",
    "shutil.rmtree",
)
OPERATIONS_TRADING_BROKER_LIVE_TERMS = (
    *BROKER_TERMS,
    *LIVE_TERMS,
    *ORDER_TERMS,
    *EXECUTION_TERMS,
    "trade",
    "trading",
)


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
class TradingSafetyCheckReport:
    source_files_scanned: int
    trading_related_files: tuple[str, ...]
    order_hotspots: tuple[str, ...]
    broker_hotspots: tuple[str, ...]
    live_environment_hotspots: tuple[str, ...]
    retry_hotspots: tuple[str, ...]
    reconciliation_hotspots: tuple[str, ...]
    execution_hotspots: tuple[str, ...]


@dataclass(frozen=True)
class ImportMapReport:
    source_modules: int
    internal_import_edges: tuple[str, ...]
    external_import_roots: tuple[str, ...]
    module_dependency_counts: tuple[str, ...]
    highly_coupled_modules: tuple[str, ...]
    parse_errors: tuple[str, ...]


@dataclass(frozen=True)
class TestStructureReport:
    source_modules: int
    test_files: int
    test_categories_present: tuple[str, ...]
    test_categories_missing: tuple[str, ...]
    test_category_counts: tuple[str, ...]
    source_modules_without_direct_tests: tuple[str, ...]
    direct_test_matches: tuple[str, ...]


@dataclass(frozen=True)
class ConfigurationSafetyReport:
    configuration_files: tuple[str, ...]
    expected_configuration_files_present: tuple[str, ...]
    expected_configuration_files_missing: tuple[str, ...]
    environment_hotspots: tuple[str, ...]
    secret_reference_hotspots: tuple[str, ...]
    possible_plain_secret_value_hotspots: tuple[str, ...]
    live_default_hotspots: tuple[str, ...]


@dataclass(frozen=True)
class RuntimeEntrypointReport:
    runtime_python_files_scanned: int
    script_files: tuple[str, ...]
    tool_files: tuple[str, ...]
    python_entrypoint_files: tuple[str, ...]
    cli_parser_files: tuple[str, ...]
    pyproject_script_entries: tuple[str, ...]
    entrypoint_trading_hotspots: tuple[str, ...]
    entrypoint_runtime_default_hotspots: tuple[str, ...]
    parse_errors: tuple[str, ...]


@dataclass(frozen=True)
class DependencyPackagingReport:
    pyproject_present: bool
    build_backend: str
    requires_python: str
    build_system_requires: tuple[str, ...]
    dependency_files: tuple[str, ...]
    lock_files: tuple[str, ...]
    packaging_tool_sections: tuple[str, ...]
    pyproject_dependency_entries: tuple[str, ...]
    requirement_file_entries: tuple[str, ...]
    unpinned_dependency_entries: tuple[str, ...]
    editable_or_path_dependency_entries: tuple[str, ...]
    parse_errors: tuple[str, ...]


@dataclass(frozen=True)
class PersistenceStateReport:
    database_files: tuple[str, ...]
    migration_files: tuple[str, ...]
    persistence_directories: tuple[str, ...]
    persistence_python_files: tuple[str, ...]
    persistence_import_hotspots: tuple[str, ...]
    persistence_write_hotspots: tuple[str, ...]
    trading_state_hotspots: tuple[str, ...]
    parse_errors: tuple[str, ...]


@dataclass(frozen=True)
class ObservabilityLoggingReport:
    observability_files: tuple[str, ...]
    logging_config_files: tuple[str, ...]
    logging_python_files: tuple[str, ...]
    logging_import_hotspots: tuple[str, ...]
    logging_call_hotspots: tuple[str, ...]
    print_hotspots: tuple[str, ...]
    exception_handler_hotspots: tuple[str, ...]
    silent_exception_hotspots: tuple[str, ...]
    pass_hotspots: tuple[str, ...]
    critical_event_hotspots: tuple[str, ...]
    parse_errors: tuple[str, ...]


@dataclass(frozen=True)
class ExternalInterfaceReport:
    source_python_files_scanned: int
    external_interface_files: tuple[str, ...]
    broker_import_hotspots: tuple[str, ...]
    network_import_hotspots: tuple[str, ...]
    broker_term_hotspots: tuple[str, ...]
    network_term_hotspots: tuple[str, ...]
    order_execution_interface_hotspots: tuple[str, ...]
    domain_external_import_violations: tuple[str, ...]
    application_external_import_violations: tuple[str, ...]
    parse_errors: tuple[str, ...]


@dataclass(frozen=True)
class CicdWorkflowReport:
    workflow_files: tuple[str, ...]
    workflow_trigger_hotspots: tuple[str, ...]
    job_hotspots: tuple[str, ...]
    action_usage_hotspots: tuple[str, ...]
    run_command_hotspots: tuple[str, ...]
    quality_gate_hotspots: tuple[str, ...]
    risky_deploy_publish_hotspots: tuple[str, ...]
    secret_usage_hotspots: tuple[str, ...]
    permission_hotspots: tuple[str, ...]
    trading_broker_live_hotspots: tuple[str, ...]


@dataclass(frozen=True)
class TimeScheduleReport:
    source_python_files_scanned: int
    time_schedule_files: tuple[str, ...]
    time_import_hotspots: tuple[str, ...]
    timezone_hotspots: tuple[str, ...]
    schedule_timer_hotspots: tuple[str, ...]
    market_calendar_hotspots: tuple[str, ...]
    expiry_settlement_hotspots: tuple[str, ...]
    naive_datetime_hotspots: tuple[str, ...]
    parse_errors: tuple[str, ...]


@dataclass(frozen=True)
class RiskStrategyDecisionReport:
    source_python_files_scanned: int
    risk_strategy_files: tuple[str, ...]
    domain_strategy_files: tuple[str, ...]
    application_strategy_files: tuple[str, ...]
    strategy_decision_hotspots: tuple[str, ...]
    risk_limit_sizing_hotspots: tuple[str, ...]
    entry_exit_decision_hotspots: tuple[str, ...]
    pnl_position_state_hotspots: tuple[str, ...]
    auto_decision_hotspots: tuple[str, ...]
    parse_errors: tuple[str, ...]


@dataclass(frozen=True)
class CockpitUiSurfaceReport:
    source_python_files_scanned: int
    cockpit_ui_files: tuple[str, ...]
    ui_framework_import_hotspots: tuple[str, ...]
    ui_surface_hotspots: tuple[str, ...]
    ui_action_hotspots: tuple[str, ...]
    read_only_ui_hotspots: tuple[str, ...]
    ui_trading_hotspots: tuple[str, ...]
    direct_trading_action_hotspots: tuple[str, ...]
    parse_errors: tuple[str, ...]


@dataclass(frozen=True)
class DataArtifactReport:
    metadata_files_scanned: int
    data_artifact_files: tuple[str, ...]
    artifact_directories: tuple[str, ...]
    generated_export_report_artifacts: tuple[str, ...]
    test_data_artifacts: tuple[str, ...]
    runtime_data_artifacts: tuple[str, ...]
    sensitive_artifact_hotspots: tuple[str, ...]
    versioned_runtime_artifacts: tuple[str, ...]


@dataclass(frozen=True)
class ReleaseVersionReport:
    release_version_files: tuple[str, ...]
    pyproject_version: str
    version_file_value: str
    changelog_present: bool
    version_reference_hotspots: tuple[str, ...]
    changelog_version_hotspots: tuple[str, ...]
    readme_version_hotspots: tuple[str, ...]
    docs_version_hotspots: tuple[str, ...]
    prerelease_hotspots: tuple[str, ...]
    release_tag_hotspots: tuple[str, ...]
    version_consistency_findings: tuple[str, ...]


@dataclass(frozen=True)
class SecuritySecretsReport:
    text_files_scanned: int
    security_sensitive_files: tuple[str, ...]
    env_key_cert_files: tuple[str, ...]
    secret_reference_hotspots: tuple[str, ...]
    hardcoded_secret_value_hotspots: tuple[str, ...]
    broker_account_credential_hotspots: tuple[str, ...]
    ci_secret_usage_hotspots: tuple[str, ...]
    config_secret_usage_hotspots: tuple[str, ...]
    source_secret_usage_hotspots: tuple[str, ...]
    gitignore_secret_protection_findings: tuple[str, ...]


@dataclass(frozen=True)
class OperationsRunbookReport:
    text_files_scanned: int
    operations_runbook_files: tuple[str, ...]
    command_hotspots: tuple[str, ...]
    start_stop_restart_hotspots: tuple[str, ...]
    recovery_rollback_hotspots: tuple[str, ...]
    destructive_command_hotspots: tuple[str, ...]
    trading_broker_live_hotspots: tuple[str, ...]


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
    trading_safety: TradingSafetyCheckReport
    import_map: ImportMapReport
    test_structure: TestStructureReport
    configuration_safety: ConfigurationSafetyReport
    runtime_entrypoints: RuntimeEntrypointReport
    dependency_packaging: DependencyPackagingReport
    persistence_state: PersistenceStateReport
    observability_logging: ObservabilityLoggingReport
    external_interfaces: ExternalInterfaceReport
    cicd_workflows: CicdWorkflowReport
    time_schedule: TimeScheduleReport
    risk_strategy_decisions: RiskStrategyDecisionReport
    cockpit_ui_surfaces: CockpitUiSurfaceReport
    data_artifacts: DataArtifactReport
    release_versions: ReleaseVersionReport
    security_secrets: SecuritySecretsReport
    operations_runbooks: OperationsRunbookReport


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

    normalized_text = " ".join(text.split())

    if len(normalized_text) > 500:
        return False

    return any(marker in normalized_text for marker in PLACEHOLDER_MARKERS)


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


def _matches_term(line: str, term: str) -> bool:
    pattern = rf"(?<![A-Za-z0-9]){re.escape(term.lower())}(?![A-Za-z0-9])"

    return re.search(pattern, line.lower()) is not None


def _matching_terms(line: str, terms: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(term for term in terms if _matches_term(line, term))


def _format_hotspot(
    relative_path: Path, line_number: int, matched_terms: tuple[str, ...]
) -> str:
    return f"{_to_posix(relative_path)}:L{line_number} -> {', '.join(matched_terms)}"


def _collect_term_hotspots(
    root: Path, relative_path: Path, terms: tuple[str, ...]
) -> tuple[str, ...]:
    text = _read_python_text(root / relative_path)
    hotspots: list[str] = []

    for line_number, line in enumerate(text.splitlines(), start=1):
        matched_terms = _matching_terms(line, terms)

        if matched_terms:
            hotspots.append(_format_hotspot(relative_path, line_number, matched_terms))

    return tuple(hotspots)


def _is_trading_related_file(root: Path, relative_path: Path) -> bool:
    text = _read_python_text(root / relative_path)

    return any(_matches_term(text, term) for term in TRADING_SAFETY_TERMS)


def _build_trading_safety_report(
    root: Path, relative_files: tuple[Path, ...]
) -> TradingSafetyCheckReport:
    source_python_files = tuple(
        path
        for path in relative_files
        if path.suffix == ".py" and _is_under(path, "src")
    )
    trading_related_files = tuple(
        _to_posix(path)
        for path in source_python_files
        if _is_trading_related_file(root, path)
    )

    order_hotspots: list[str] = []
    broker_hotspots: list[str] = []
    live_environment_hotspots: list[str] = []
    retry_hotspots: list[str] = []
    reconciliation_hotspots: list[str] = []
    execution_hotspots: list[str] = []

    for relative_path in source_python_files:
        order_hotspots.extend(_collect_term_hotspots(root, relative_path, ORDER_TERMS))
        broker_hotspots.extend(
            _collect_term_hotspots(root, relative_path, BROKER_TERMS)
        )
        live_environment_hotspots.extend(
            _collect_term_hotspots(root, relative_path, LIVE_TERMS)
        )
        retry_hotspots.extend(_collect_term_hotspots(root, relative_path, RETRY_TERMS))
        reconciliation_hotspots.extend(
            _collect_term_hotspots(root, relative_path, RECONCILIATION_TERMS)
        )
        execution_hotspots.extend(
            _collect_term_hotspots(root, relative_path, EXECUTION_TERMS)
        )

    return TradingSafetyCheckReport(
        source_files_scanned=len(source_python_files),
        trading_related_files=trading_related_files,
        order_hotspots=tuple(order_hotspots),
        broker_hotspots=tuple(broker_hotspots),
        live_environment_hotspots=tuple(live_environment_hotspots),
        retry_hotspots=tuple(retry_hotspots),
        reconciliation_hotspots=tuple(reconciliation_hotspots),
        execution_hotspots=tuple(execution_hotspots),
    )


def _module_root(imported_module: str) -> str:
    return imported_module.split(".", maxsplit=1)[0]


def _is_internal_import(imported_module: str) -> bool:
    return imported_module == PROJECT_PACKAGE or imported_module.startswith(
        f"{PROJECT_PACKAGE}."
    )


def _format_dependency_count(
    module_name: str, inbound_count: int, outbound_count: int
) -> str:
    return f"{module_name} -> inbound {inbound_count}, outbound {outbound_count}"


def _build_import_map_report(
    root: Path, relative_files: tuple[Path, ...]
) -> ImportMapReport:
    source_python_files = tuple(
        path
        for path in relative_files
        if path.suffix == ".py" and _is_under(path, "src")
    )
    source_modules = tuple(_module_name_from_path(path) for path in source_python_files)
    source_module_set = set(source_modules)
    internal_edges: set[tuple[str, str]] = set()
    external_import_roots: set[str] = set()
    inbound_counts = dict.fromkeys(source_modules, 0)
    outbound_counts = dict.fromkeys(source_modules, 0)
    parse_errors: list[str] = []

    for relative_path in source_python_files:
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

        for imported_module in imported_modules:
            if not imported_module:
                continue

            if _is_internal_import(imported_module):
                edge = (module_name, imported_module)

                if edge not in internal_edges:
                    internal_edges.add(edge)
                    outbound_counts[module_name] = (
                        outbound_counts.get(module_name, 0) + 1
                    )

                    if imported_module in source_module_set:
                        inbound_counts[imported_module] = (
                            inbound_counts.get(imported_module, 0) + 1
                        )
            else:
                external_import_roots.add(_module_root(imported_module))

    module_dependency_counts: list[str] = []
    highly_coupled_modules: list[str] = []

    for module_name in sorted(source_modules):
        inbound_count = inbound_counts.get(module_name, 0)
        outbound_count = outbound_counts.get(module_name, 0)
        dependency_count = _format_dependency_count(
            module_name, inbound_count, outbound_count
        )
        module_dependency_counts.append(dependency_count)

        if (inbound_count + outbound_count) >= HIGH_COUPLING_THRESHOLD:
            highly_coupled_modules.append(dependency_count)

    return ImportMapReport(
        source_modules=len(source_modules),
        internal_import_edges=tuple(
            f"{source} -> {target}" for source, target in sorted(internal_edges)
        ),
        external_import_roots=tuple(sorted(external_import_roots)),
        module_dependency_counts=tuple(module_dependency_counts),
        highly_coupled_modules=tuple(highly_coupled_modules),
        parse_errors=tuple(parse_errors),
    )


def _is_test_file(relative_path: Path) -> bool:
    return (
        relative_path.suffix == ".py"
        and _is_under(relative_path, "tests")
        and relative_path.name.startswith("test_")
    )


def _test_category_name(relative_path: Path) -> str:
    if len(relative_path.parts) > 2 and relative_path.parts[0] == "tests":
        return relative_path.parts[1]

    return "root"


def _source_module_test_token(module_name: str) -> str:
    return module_name.rsplit(".", maxsplit=1)[-1].lower()


def _is_direct_test_candidate(module_name: str) -> bool:
    return not module_name.endswith(".__init__")


def _test_matches_source_module(test_path: Path, module_name: str) -> bool:
    token = _source_module_test_token(module_name)

    return token in test_path.stem.lower()


def _format_test_category_count(category: str, count: int) -> str:
    return f"{category}: {count}"


def _build_test_structure_report(
    relative_files: tuple[Path, ...],
) -> TestStructureReport:
    source_python_files = tuple(
        path
        for path in relative_files
        if path.suffix == ".py" and _is_under(path, "src")
    )
    source_modules = tuple(
        sorted(_module_name_from_path(path) for path in source_python_files)
    )
    test_files = tuple(sorted(path for path in relative_files if _is_test_file(path)))

    category_counts: dict[str, int] = {}

    for test_file in test_files:
        category = _test_category_name(test_file)
        category_counts[category] = category_counts.get(category, 0) + 1

    test_categories_present = tuple(sorted(category_counts))
    test_categories_missing = tuple(
        category
        for category in TEST_CATEGORY_DIRS
        if category not in test_categories_present
    )
    test_category_counts = tuple(
        _format_test_category_count(category, category_counts[category])
        for category in sorted(category_counts)
    )

    direct_test_matches: list[str] = []
    source_modules_without_direct_tests: list[str] = []

    for module_name in source_modules:
        if not _is_direct_test_candidate(module_name):
            continue

        matching_tests = tuple(
            test_file
            for test_file in test_files
            if _test_matches_source_module(test_file, module_name)
        )

        if not matching_tests:
            source_modules_without_direct_tests.append(module_name)
            continue

        direct_test_matches.extend(
            f"{module_name} -> {_to_posix(test_file)}" for test_file in matching_tests
        )

    return TestStructureReport(
        source_modules=len(source_modules),
        test_files=len(test_files),
        test_categories_present=test_categories_present,
        test_categories_missing=test_categories_missing,
        test_category_counts=test_category_counts,
        source_modules_without_direct_tests=tuple(source_modules_without_direct_tests),
        direct_test_matches=tuple(direct_test_matches),
    )


def _is_configuration_file(relative_path: Path) -> bool:
    if not relative_path.parts:
        return False

    if relative_path.as_posix() in CONFIG_FILE_NAMES:
        return True

    if relative_path.parts[0] == "config":
        return relative_path.suffix.lower() in CONFIG_FILE_SUFFIXES

    return relative_path.name.startswith(".env")


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _format_line_hotspot(
    relative_path: Path, line_number: int, description: str
) -> str:
    return f"{_to_posix(relative_path)}:L{line_number} -> {description}"


def _collect_text_hotspots(
    root: Path, relative_path: Path, terms: tuple[str, ...]
) -> tuple[str, ...]:
    text = _read_text(root / relative_path)
    hotspots: list[str] = []

    for line_number, line in enumerate(text.splitlines(), start=1):
        matched_terms = _matching_terms(line, terms)

        if matched_terms:
            hotspots.append(
                _format_line_hotspot(
                    relative_path, line_number, ", ".join(matched_terms)
                )
            )

    return tuple(hotspots)


def _extract_assignment_value(line: str) -> str | None:
    stripped_line = line.strip()

    if not stripped_line or stripped_line.startswith("#"):
        return None

    separator = "=" if "=" in stripped_line else ":" if ":" in stripped_line else ""

    if not separator:
        return None

    value = stripped_line.split(separator, maxsplit=1)[1].strip()
    return value.strip("\"'")


def _contains_secret_key(line: str) -> bool:
    return bool(_matching_terms(line, SECRET_REFERENCE_TERMS))


def _is_possible_plain_secret_value(line: str) -> bool:
    if not _contains_secret_key(line):
        return False

    value = _extract_assignment_value(line)

    if value is None:
        return False

    normalized_value = value.strip().lower()

    return normalized_value not in SECRET_VALUE_MARKERS


def _is_live_default_line(line: str) -> bool:
    normalized_line = line.lower()

    return "live" in normalized_line and (
        "default" in normalized_line or "app_env" in normalized_line
    )


def _build_configuration_safety_report(
    root: Path, relative_files: tuple[Path, ...]
) -> ConfigurationSafetyReport:
    configuration_files = tuple(
        path for path in relative_files if _is_configuration_file(path)
    )
    expected_configuration_files_present = tuple(
        path for path in EXPECTED_CONFIGURATION_PATHS if (root / path).exists()
    )
    expected_configuration_files_missing = tuple(
        path for path in EXPECTED_CONFIGURATION_PATHS if not (root / path).exists()
    )

    environment_hotspots: list[str] = []
    secret_reference_hotspots: list[str] = []
    possible_plain_secret_value_hotspots: list[str] = []
    live_default_hotspots: list[str] = []

    for relative_path in configuration_files:
        environment_hotspots.extend(
            _collect_text_hotspots(root, relative_path, ENVIRONMENT_TERMS)
        )
        secret_reference_hotspots.extend(
            _collect_text_hotspots(root, relative_path, SECRET_REFERENCE_TERMS)
        )

        text = _read_text(root / relative_path)

        for line_number, line in enumerate(text.splitlines(), start=1):
            if _is_possible_plain_secret_value(line):
                possible_plain_secret_value_hotspots.append(
                    _format_line_hotspot(
                        relative_path, line_number, "possible plain secret value"
                    )
                )

            if _is_live_default_line(line):
                live_default_hotspots.append(
                    _format_line_hotspot(
                        relative_path, line_number, "LIVE default reference"
                    )
                )

    return ConfigurationSafetyReport(
        configuration_files=tuple(_to_posix(path) for path in configuration_files),
        expected_configuration_files_present=expected_configuration_files_present,
        expected_configuration_files_missing=expected_configuration_files_missing,
        environment_hotspots=tuple(environment_hotspots),
        secret_reference_hotspots=tuple(secret_reference_hotspots),
        possible_plain_secret_value_hotspots=tuple(
            possible_plain_secret_value_hotspots
        ),
        live_default_hotspots=tuple(live_default_hotspots),
    )


def _is_runtime_python_file(relative_path: Path) -> bool:
    return (
        relative_path.suffix == ".py"
        and bool(relative_path.parts)
        and relative_path.parts[0] in RUNTIME_ENTRYPOINT_DIRECTORIES
    )


def _is_script_python_file(relative_path: Path) -> bool:
    return relative_path.suffix == ".py" and _is_under(relative_path, "scripts")


def _is_tool_python_file(relative_path: Path) -> bool:
    return relative_path.suffix == ".py" and _is_under(relative_path, "tools")


def _is_main_guard(node: ast.AST) -> bool:
    if not isinstance(node, ast.If):
        return False

    test = node.test

    if not isinstance(test, ast.Compare):
        return False

    if len(test.ops) != 1 or not isinstance(test.ops[0], ast.Eq):
        return False

    if len(test.comparators) != 1:
        return False

    left = test.left
    right = test.comparators[0]

    return (
        isinstance(left, ast.Name)
        and left.id == "__name__"
        and isinstance(right, ast.Constant)
        and right.value == "__main__"
    )


def _has_main_guard(tree: ast.AST) -> bool:
    return any(_is_main_guard(node) for node in ast.walk(tree))


def _has_cli_parser_reference(tree: ast.AST, imported_modules: tuple[str, ...]) -> bool:
    if any(
        _module_root(imported_module) in CLI_IMPORT_ROOTS
        for imported_module in imported_modules
    ):
        return True

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            function = node.func

            if isinstance(function, ast.Name) and function.id in CLI_CALL_NAMES:
                return True

            if isinstance(function, ast.Attribute) and function.attr in CLI_CALL_NAMES:
                return True

    return False


def _collect_pyproject_script_entries(root: Path) -> tuple[str, ...]:
    pyproject_path = root / "pyproject.toml"

    if not pyproject_path.exists():
        return ()

    entries: list[str] = []
    current_section = ""

    for line_number, line in enumerate(
        _read_text(pyproject_path).splitlines(), start=1
    ):
        stripped_line = line.strip()

        if stripped_line.startswith("[") and stripped_line.endswith("]"):
            current_section = stripped_line.strip("[]")
            continue

        if current_section not in {"project.scripts", "tool.poetry.scripts"}:
            continue

        if (
            not stripped_line
            or stripped_line.startswith("#")
            or "=" not in stripped_line
        ):
            continue

        entries.append(f"pyproject.toml:L{line_number} -> {stripped_line}")

    return tuple(entries)


def _build_runtime_entrypoint_report(
    root: Path, relative_files: tuple[Path, ...]
) -> RuntimeEntrypointReport:
    runtime_python_files = tuple(
        path for path in relative_files if _is_runtime_python_file(path)
    )
    script_files = tuple(
        _to_posix(path) for path in relative_files if _is_script_python_file(path)
    )
    tool_files = tuple(
        _to_posix(path) for path in relative_files if _is_tool_python_file(path)
    )

    python_entrypoint_files: list[str] = []
    cli_parser_files: list[str] = []
    entrypoint_trading_hotspots: list[str] = []
    entrypoint_runtime_default_hotspots: list[str] = []
    parse_errors: list[str] = []

    for relative_path in runtime_python_files:
        absolute_path = root / relative_path
        module_name = _module_name_from_path(relative_path)

        try:
            text = _read_python_text(absolute_path)
            tree = ast.parse(text, filename=str(absolute_path))
        except SyntaxError as exc:
            parse_errors.append(f"{_to_posix(relative_path)} -> {exc.msg}")
            continue

        imported_modules = tuple(_iter_imported_modules(tree, module_name))
        has_entrypoint = _has_main_guard(tree)

        if has_entrypoint:
            python_entrypoint_files.append(_to_posix(relative_path))

        if _has_cli_parser_reference(tree, imported_modules):
            cli_parser_files.append(_to_posix(relative_path))

        if has_entrypoint:
            for line_number, line in enumerate(text.splitlines(), start=1):
                trading_terms = _matching_terms(line, TRADING_SAFETY_TERMS)

                if trading_terms:
                    entrypoint_trading_hotspots.append(
                        _format_hotspot(relative_path, line_number, trading_terms)
                    )

                runtime_default_terms = _matching_terms(line, RUNTIME_DEFAULT_TERMS)

                if runtime_default_terms:
                    entrypoint_runtime_default_hotspots.append(
                        _format_hotspot(
                            relative_path, line_number, runtime_default_terms
                        )
                    )

    return RuntimeEntrypointReport(
        runtime_python_files_scanned=len(runtime_python_files),
        script_files=tuple(sorted(script_files)),
        tool_files=tuple(sorted(tool_files)),
        python_entrypoint_files=tuple(sorted(python_entrypoint_files)),
        cli_parser_files=tuple(sorted(cli_parser_files)),
        pyproject_script_entries=_collect_pyproject_script_entries(root),
        entrypoint_trading_hotspots=tuple(entrypoint_trading_hotspots),
        entrypoint_runtime_default_hotspots=tuple(entrypoint_runtime_default_hotspots),
        parse_errors=tuple(parse_errors),
    )


def _is_dependency_file(relative_path: Path) -> bool:
    if len(relative_path.parts) != 1:
        return False

    return relative_path.name.startswith(DEPENDENCY_FILE_PREFIXES) and (
        relative_path.suffix in DEPENDENCY_FILE_SUFFIXES
    )


def _is_lock_file(relative_path: Path) -> bool:
    return len(relative_path.parts) == 1 and relative_path.name in LOCK_FILE_NAMES


def _collect_pyproject_section_names(root: Path) -> tuple[str, ...]:
    pyproject_path = root / "pyproject.toml"

    if not pyproject_path.exists():
        return ()

    section_names: list[str] = []

    for line in _read_text(pyproject_path).splitlines():
        stripped_line = line.strip()

        if not (stripped_line.startswith("[") and stripped_line.endswith("]")):
            continue

        section_name = stripped_line.strip("[]")

        if any(
            section_name == prefix or section_name.startswith(f"{prefix}.")
            for prefix in PACKAGING_TOOL_SECTION_PREFIXES
        ):
            section_names.append(section_name)

    return tuple(section_names)


def _load_pyproject_data(root: Path) -> tuple[dict[str, object], tuple[str, ...]]:
    pyproject_path = root / "pyproject.toml"

    if not pyproject_path.exists():
        return {}, ()

    try:
        return tomllib.loads(_read_text(pyproject_path)), ()
    except tomllib.TOMLDecodeError as exc:
        return {}, (f"pyproject.toml -> {exc}",)


def _as_string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()

    return tuple(item for item in value if isinstance(item, str))


def _extract_pyproject_dependencies(
    pyproject_data: dict[str, object],
) -> tuple[tuple[str, ...], tuple[str, ...], str, str]:
    build_system = pyproject_data.get("build-system", {})
    project = pyproject_data.get("project", {})

    if not isinstance(build_system, dict):
        build_system = {}

    if not isinstance(project, dict):
        project = {}

    build_backend = build_system.get("build-backend")
    requires_python = project.get("requires-python")
    build_system_requires = _as_string_tuple(build_system.get("requires"))

    dependency_entries: list[str] = []

    for dependency in _as_string_tuple(project.get("dependencies")):
        dependency_entries.append(
            f"pyproject.toml:project.dependencies -> {dependency}"
        )

    optional_dependencies = project.get("optional-dependencies", {})

    if isinstance(optional_dependencies, dict):
        for group_name in sorted(optional_dependencies):
            for dependency in _as_string_tuple(optional_dependencies[group_name]):
                dependency_entries.append(
                    "pyproject.toml:project.optional-dependencies."
                    f"{group_name} -> {dependency}"
                )

    return (
        build_system_requires,
        tuple(dependency_entries),
        build_backend if isinstance(build_backend, str) else "missing",
        requires_python if isinstance(requires_python, str) else "missing",
    )


def _strip_requirement_inline_comment(line: str) -> str:
    return line.split(" #", maxsplit=1)[0].strip()


def _is_requirement_option(line: str) -> bool:
    return line.startswith(REQUIREMENT_OPTION_PREFIXES)


def _is_requirement_dependency_entry(line: str) -> bool:
    stripped_line = _strip_requirement_inline_comment(line)

    if not stripped_line or stripped_line.startswith("#"):
        return False

    if _is_requirement_option(stripped_line):
        return False

    return True


def _has_dependency_version_marker(dependency: str) -> bool:
    return any(marker in dependency for marker in DEPENDENCY_VERSION_MARKERS)


def _is_unpinned_dependency(dependency: str) -> bool:
    stripped_dependency = dependency.strip()

    if not stripped_dependency:
        return False

    if stripped_dependency.startswith("-e "):
        return True

    if " @ " in stripped_dependency:
        return False

    return not _has_dependency_version_marker(stripped_dependency)


def _is_editable_or_path_dependency(dependency: str) -> bool:
    stripped_dependency = dependency.strip()
    lowered_dependency = stripped_dependency.lower()

    return (
        stripped_dependency.startswith("-e ")
        or stripped_dependency.startswith(("./", "../", "/"))
        or " @ file:" in lowered_dependency
        or " @ ./" in lowered_dependency
        or " @ ../" in lowered_dependency
    )


def _dependency_entry_value(formatted_entry: str) -> str:
    return formatted_entry.split(" -> ", maxsplit=1)[1]


def _collect_requirement_file_entries(
    root: Path, dependency_files: tuple[Path, ...]
) -> tuple[str, ...]:
    entries: list[str] = []

    for relative_path in dependency_files:
        for line_number, line in enumerate(
            _read_text(root / relative_path).splitlines(), start=1
        ):
            stripped_line = _strip_requirement_inline_comment(line)

            if not _is_requirement_dependency_entry(stripped_line):
                continue

            entries.append(
                f"{_to_posix(relative_path)}:L{line_number} -> {stripped_line}"
            )

    return tuple(entries)


def _build_dependency_packaging_report(
    root: Path, relative_files: tuple[Path, ...]
) -> DependencyPackagingReport:
    dependency_files = tuple(
        sorted(path for path in relative_files if _is_dependency_file(path))
    )
    lock_files = tuple(sorted(path for path in relative_files if _is_lock_file(path)))
    pyproject_data, parse_errors = _load_pyproject_data(root)
    (
        build_system_requires,
        pyproject_dependency_entries,
        build_backend,
        requires_python,
    ) = _extract_pyproject_dependencies(pyproject_data)
    requirement_file_entries = _collect_requirement_file_entries(root, dependency_files)
    build_system_dependency_entries = tuple(
        f"pyproject.toml:build-system.requires -> {dependency}"
        for dependency in build_system_requires
    )
    all_dependency_entries = (
        *build_system_dependency_entries,
        *pyproject_dependency_entries,
        *requirement_file_entries,
    )
    unpinned_dependency_entries = tuple(
        entry
        for entry in all_dependency_entries
        if _is_unpinned_dependency(_dependency_entry_value(entry))
    )
    editable_or_path_dependency_entries = tuple(
        entry
        for entry in all_dependency_entries
        if _is_editable_or_path_dependency(_dependency_entry_value(entry))
    )

    return DependencyPackagingReport(
        pyproject_present=(root / "pyproject.toml").is_file(),
        build_backend=build_backend,
        requires_python=requires_python,
        build_system_requires=build_system_requires,
        dependency_files=tuple(_to_posix(path) for path in dependency_files),
        lock_files=tuple(_to_posix(path) for path in lock_files),
        packaging_tool_sections=_collect_pyproject_section_names(root),
        pyproject_dependency_entries=pyproject_dependency_entries,
        requirement_file_entries=requirement_file_entries,
        unpinned_dependency_entries=unpinned_dependency_entries,
        editable_or_path_dependency_entries=editable_or_path_dependency_entries,
        parse_errors=parse_errors,
    )


def _is_database_file(relative_path: Path) -> bool:
    return relative_path.suffix.lower() in PERSISTENCE_DATABASE_FILE_SUFFIXES


def _is_schema_file(relative_path: Path) -> bool:
    return relative_path.name.lower() in PERSISTENCE_SCHEMA_FILE_NAMES


def _is_migration_file(relative_path: Path) -> bool:
    if relative_path.suffix.lower() not in MIGRATION_FILE_SUFFIXES:
        return False

    return any(part in MIGRATION_DIRECTORY_NAMES for part in relative_path.parts)


def _is_persistence_text_file(relative_path: Path) -> bool:
    return relative_path.suffix.lower() in PERSISTENCE_TEXT_FILE_SUFFIXES


def _collect_persistence_directories(
    relative_files: tuple[Path, ...],
) -> tuple[str, ...]:
    directories: set[str] = set()

    for relative_path in relative_files:
        for index, part in enumerate(relative_path.parts[:-1]):
            if part in PERSISTENCE_DIRECTORY_NAMES:
                directories.add(Path(*relative_path.parts[: index + 1]).as_posix())

    return tuple(sorted(directories))


def _is_persistence_python_file(
    root: Path, relative_path: Path, migration_files: tuple[Path, ...]
) -> bool:
    if relative_path.suffix != ".py":
        return False

    if not relative_path.parts:
        return False

    if relative_path.parts[0] not in (
        *RUNTIME_ENTRYPOINT_DIRECTORIES,
        *MIGRATION_DIRECTORY_NAMES,
    ):
        return False

    if relative_path in migration_files:
        return True

    text = _read_python_text(root / relative_path)

    return any(
        _matches_term(text, term)
        for term in (*PERSISTENCE_IMPORT_TERMS, *PERSISTENCE_TRADING_STATE_TERMS)
    )


def _collect_persistence_line_hotspots(
    root: Path, relative_path: Path, terms: tuple[str, ...]
) -> tuple[str, ...]:
    text = _read_text(root / relative_path)
    hotspots: list[str] = []

    for line_number, line in enumerate(text.splitlines(), start=1):
        matched_terms = _matching_terms(line, terms)

        if matched_terms:
            hotspots.append(_format_hotspot(relative_path, line_number, matched_terms))

    return tuple(hotspots)


def _collect_persistence_parse_errors(
    root: Path, python_files: tuple[Path, ...]
) -> tuple[str, ...]:
    parse_errors: list[str] = []

    for relative_path in python_files:
        absolute_path = root / relative_path

        try:
            ast.parse(_read_python_text(absolute_path), filename=str(absolute_path))
        except SyntaxError as exc:
            parse_errors.append(f"{_to_posix(relative_path)} -> {exc.msg}")

    return tuple(parse_errors)


def _build_persistence_state_report(
    root: Path, relative_files: tuple[Path, ...]
) -> PersistenceStateReport:
    database_files = tuple(
        sorted(path for path in relative_files if _is_database_file(path))
    )
    migration_files = tuple(
        sorted(
            path
            for path in relative_files
            if _is_migration_file(path) or _is_schema_file(path)
        )
    )
    text_files = tuple(
        path for path in relative_files if _is_persistence_text_file(path)
    )
    persistence_python_files = tuple(
        sorted(
            path
            for path in relative_files
            if _is_persistence_python_file(root, path, migration_files)
        )
    )

    persistence_import_hotspots: list[str] = []
    persistence_write_hotspots: list[str] = []
    trading_state_hotspots: list[str] = []

    for relative_path in text_files:
        persistence_import_hotspots.extend(
            _collect_persistence_line_hotspots(
                root, relative_path, PERSISTENCE_IMPORT_TERMS
            )
        )
        persistence_write_hotspots.extend(
            _collect_persistence_line_hotspots(
                root, relative_path, PERSISTENCE_WRITE_TERMS
            )
        )
        trading_state_hotspots.extend(
            _collect_persistence_line_hotspots(
                root, relative_path, PERSISTENCE_TRADING_STATE_TERMS
            )
        )

    return PersistenceStateReport(
        database_files=tuple(_to_posix(path) for path in database_files),
        migration_files=tuple(_to_posix(path) for path in migration_files),
        persistence_directories=_collect_persistence_directories(relative_files),
        persistence_python_files=tuple(
            _to_posix(path) for path in persistence_python_files
        ),
        persistence_import_hotspots=tuple(persistence_import_hotspots),
        persistence_write_hotspots=tuple(persistence_write_hotspots),
        trading_state_hotspots=tuple(trading_state_hotspots),
        parse_errors=_collect_persistence_parse_errors(root, persistence_python_files),
    )


def _is_observability_text_file(relative_path: Path) -> bool:
    return relative_path.suffix.lower() in OBSERVABILITY_TEXT_FILE_SUFFIXES


def _is_observability_file(relative_path: Path) -> bool:
    if not _is_observability_text_file(relative_path):
        return False

    path_text = _to_posix(relative_path).lower()

    return any(
        part in OBSERVABILITY_DIRECTORY_NAMES for part in relative_path.parts
    ) or any(term in path_text for term in OBSERVABILITY_FILE_NAME_TERMS)


def _is_logging_config_file(relative_path: Path) -> bool:
    return relative_path.name.lower() in LOGGING_CONFIG_FILE_NAMES


def _is_observability_scan_python_file(relative_path: Path) -> bool:
    return (
        relative_path.suffix == ".py"
        and bool(relative_path.parts)
        and relative_path.parts[0] in RUNTIME_ENTRYPOINT_DIRECTORIES
    )


def _call_name(node: ast.Call) -> str:
    function = node.func

    if isinstance(function, ast.Name):
        return function.id

    if isinstance(function, ast.Attribute):
        return function.attr

    return ""


def _collect_logging_import_hotspots(
    root: Path, relative_path: Path
) -> tuple[str, ...]:
    return _collect_persistence_line_hotspots(root, relative_path, LOGGING_IMPORT_TERMS)


def _collect_print_hotspots_from_tree(
    relative_path: Path, tree: ast.AST
) -> tuple[str, ...]:
    hotspots: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _call_name(node) == "print":
            hotspots.append(_format_line_hotspot(relative_path, node.lineno, "print"))

    return tuple(hotspots)


def _collect_logging_call_hotspots_from_tree(
    relative_path: Path, tree: ast.AST
) -> tuple[str, ...]:
    hotspots: list[str] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        call_name = _call_name(node)

        if call_name in LOGGING_CALL_NAMES:
            hotspots.append(_format_line_hotspot(relative_path, node.lineno, call_name))

    return tuple(hotspots)


def _exception_handler_description(handler: ast.ExceptHandler) -> str:
    if handler.type is None:
        return "bare except"

    if isinstance(handler.type, ast.Name):
        return handler.type.id

    if isinstance(handler.type, ast.Attribute):
        return handler.type.attr

    return "exception handler"


def _handler_has_observable_action(handler: ast.ExceptHandler) -> bool:
    for statement in handler.body:
        for node in ast.walk(statement):
            if isinstance(node, ast.Raise):
                return True

            if isinstance(node, ast.Call):
                call_name = _call_name(node)

                if call_name == "print" or call_name in LOGGING_CALL_NAMES:
                    return True

    return False


def _collect_exception_handler_hotspots_from_tree(
    relative_path: Path, tree: ast.AST
) -> tuple[str, ...]:
    hotspots: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            hotspots.append(
                _format_line_hotspot(
                    relative_path,
                    node.lineno,
                    _exception_handler_description(node),
                )
            )

    return tuple(hotspots)


def _collect_silent_exception_hotspots_from_tree(
    relative_path: Path, tree: ast.AST
) -> tuple[str, ...]:
    hotspots: list[str] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue

        if not _handler_has_observable_action(node):
            hotspots.append(
                _format_line_hotspot(
                    relative_path,
                    node.lineno,
                    "handler without raise/logging/print",
                )
            )

    return tuple(hotspots)


def _collect_pass_hotspots_from_tree(
    relative_path: Path, tree: ast.AST
) -> tuple[str, ...]:
    hotspots: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Pass):
            hotspots.append(_format_line_hotspot(relative_path, node.lineno, "pass"))

    return tuple(hotspots)


def _build_observability_logging_report(
    root: Path, relative_files: tuple[Path, ...]
) -> ObservabilityLoggingReport:
    observability_files = tuple(
        sorted(path for path in relative_files if _is_observability_file(path))
    )
    logging_config_files = tuple(
        sorted(path for path in relative_files if _is_logging_config_file(path))
    )
    scan_python_files = tuple(
        path for path in relative_files if _is_observability_scan_python_file(path)
    )
    critical_event_scan_files = tuple(
        sorted((*scan_python_files, *observability_files))
    )

    logging_python_files: set[str] = set()
    logging_import_hotspots: list[str] = []
    logging_call_hotspots: list[str] = []
    print_hotspots: list[str] = []
    exception_handler_hotspots: list[str] = []
    silent_exception_hotspots: list[str] = []
    pass_hotspots: list[str] = []
    critical_event_hotspots: list[str] = []
    parse_errors: list[str] = []

    for relative_path in scan_python_files:
        absolute_path = root / relative_path

        try:
            text = _read_python_text(absolute_path)
            tree = ast.parse(text, filename=str(absolute_path))
        except SyntaxError as exc:
            parse_errors.append(f"{_to_posix(relative_path)} -> {exc.msg}")
            continue

        file_logging_import_hotspots = _collect_logging_import_hotspots(
            root, relative_path
        )
        file_logging_call_hotspots = _collect_logging_call_hotspots_from_tree(
            relative_path, tree
        )

        if file_logging_import_hotspots or file_logging_call_hotspots:
            logging_python_files.add(_to_posix(relative_path))

        logging_import_hotspots.extend(file_logging_import_hotspots)
        logging_call_hotspots.extend(file_logging_call_hotspots)
        print_hotspots.extend(_collect_print_hotspots_from_tree(relative_path, tree))
        exception_handler_hotspots.extend(
            _collect_exception_handler_hotspots_from_tree(relative_path, tree)
        )
        silent_exception_hotspots.extend(
            _collect_silent_exception_hotspots_from_tree(relative_path, tree)
        )
        pass_hotspots.extend(_collect_pass_hotspots_from_tree(relative_path, tree))

    for relative_path in critical_event_scan_files:
        critical_event_hotspots.extend(
            _collect_persistence_line_hotspots(
                root,
                relative_path,
                OBSERVABILITY_CRITICAL_EVENT_TERMS,
            )
        )

    return ObservabilityLoggingReport(
        observability_files=tuple(_to_posix(path) for path in observability_files),
        logging_config_files=tuple(_to_posix(path) for path in logging_config_files),
        logging_python_files=tuple(sorted(logging_python_files)),
        logging_import_hotspots=tuple(logging_import_hotspots),
        logging_call_hotspots=tuple(logging_call_hotspots),
        print_hotspots=tuple(print_hotspots),
        exception_handler_hotspots=tuple(exception_handler_hotspots),
        silent_exception_hotspots=tuple(silent_exception_hotspots),
        pass_hotspots=tuple(pass_hotspots),
        critical_event_hotspots=tuple(critical_event_hotspots),
        parse_errors=tuple(parse_errors),
    )


def _is_external_interface_python_file(relative_path: Path) -> bool:
    return relative_path.suffix == ".py" and _is_under(relative_path, "src")


def _has_external_import(imported_modules: tuple[str, ...]) -> bool:
    return any(
        _matches_prefix(imported_module, EXTERNAL_INTERFACE_IMPORT_PREFIXES)
        for imported_module in imported_modules
    )


def _collect_import_hotspots(
    relative_path: Path,
    imported_modules: tuple[str, ...],
    import_prefixes: tuple[str, ...],
) -> tuple[str, ...]:
    return tuple(
        _format_violation(relative_path, imported_module)
        for imported_module in imported_modules
        if _matches_prefix(imported_module, import_prefixes)
    )


def _has_external_interface_file_signal(
    root: Path, relative_path: Path, imported_modules: tuple[str, ...]
) -> bool:
    path_text = _to_posix(relative_path).lower()

    if any(term in path_text for term in EXTERNAL_INTERFACE_FILE_NAME_TERMS):
        return True

    if _has_external_import(imported_modules):
        return True

    text = _read_python_text(root / relative_path)

    return any(
        _matches_term(text, term)
        for term in (*EXTERNAL_BROKER_TERMS, *EXTERNAL_NETWORK_TERMS)
    )


def _build_external_interface_report(
    root: Path, relative_files: tuple[Path, ...]
) -> ExternalInterfaceReport:
    source_python_files = tuple(
        path for path in relative_files if _is_external_interface_python_file(path)
    )
    domain_package_parts = ("src", PROJECT_PACKAGE, "domain")
    application_package_parts = ("src", PROJECT_PACKAGE, "application")

    external_interface_files: list[str] = []
    broker_import_hotspots: list[str] = []
    network_import_hotspots: list[str] = []
    broker_term_hotspots: list[str] = []
    network_term_hotspots: list[str] = []
    order_execution_interface_hotspots: list[str] = []
    domain_external_import_violations: list[str] = []
    application_external_import_violations: list[str] = []
    parse_errors: list[str] = []

    for relative_path in source_python_files:
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
        broker_import_hotspots.extend(
            _collect_import_hotspots(
                relative_path, imported_modules, EXTERNAL_BROKER_IMPORT_PREFIXES
            )
        )
        network_import_hotspots.extend(
            _collect_import_hotspots(
                relative_path, imported_modules, EXTERNAL_NETWORK_IMPORT_PREFIXES
            )
        )

        if _has_external_interface_file_signal(root, relative_path, imported_modules):
            external_interface_files.append(_to_posix(relative_path))

        broker_term_hotspots.extend(
            _collect_persistence_line_hotspots(
                root, relative_path, EXTERNAL_BROKER_TERMS
            )
        )
        network_term_hotspots.extend(
            _collect_persistence_line_hotspots(
                root, relative_path, EXTERNAL_NETWORK_TERMS
            )
        )
        order_execution_interface_hotspots.extend(
            _collect_persistence_line_hotspots(
                root, relative_path, INTERFACE_ORDER_EXECUTION_TERMS
            )
        )

        if _is_under_package(relative_path, domain_package_parts):
            domain_external_import_violations.extend(
                _format_violation(relative_path, imported_module)
                for imported_module in imported_modules
                if _matches_prefix(imported_module, EXTERNAL_INTERFACE_IMPORT_PREFIXES)
            )

        if _is_under_package(relative_path, application_package_parts):
            application_external_import_violations.extend(
                _format_violation(relative_path, imported_module)
                for imported_module in imported_modules
                if _matches_prefix(imported_module, EXTERNAL_INTERFACE_IMPORT_PREFIXES)
            )

    return ExternalInterfaceReport(
        source_python_files_scanned=len(source_python_files),
        external_interface_files=tuple(sorted(external_interface_files)),
        broker_import_hotspots=tuple(broker_import_hotspots),
        network_import_hotspots=tuple(network_import_hotspots),
        broker_term_hotspots=tuple(broker_term_hotspots),
        network_term_hotspots=tuple(network_term_hotspots),
        order_execution_interface_hotspots=tuple(order_execution_interface_hotspots),
        domain_external_import_violations=tuple(domain_external_import_violations),
        application_external_import_violations=tuple(
            application_external_import_violations
        ),
        parse_errors=tuple(parse_errors),
    )


def _is_cicd_workflow_file(relative_path: Path) -> bool:
    return (
        len(relative_path.parts) >= 3
        and relative_path.parts[0] == ".github"
        and relative_path.parts[1] == "workflows"
        and relative_path.suffix.lower() in CICD_WORKFLOW_SUFFIXES
    )


def _collect_cicd_workflow_hotspots(
    root: Path, workflow_files: tuple[Path, ...], terms: tuple[str, ...]
) -> tuple[str, ...]:
    hotspots: list[str] = []

    for relative_path in workflow_files:
        hotspots.extend(_collect_persistence_line_hotspots(root, relative_path, terms))

    return tuple(hotspots)


def _build_cicd_workflow_report(
    root: Path, relative_files: tuple[Path, ...]
) -> CicdWorkflowReport:
    workflow_files = tuple(
        sorted(path for path in relative_files if _is_cicd_workflow_file(path))
    )

    return CicdWorkflowReport(
        workflow_files=tuple(_to_posix(path) for path in workflow_files),
        workflow_trigger_hotspots=_collect_cicd_workflow_hotspots(
            root, workflow_files, CICD_TRIGGER_TERMS
        ),
        job_hotspots=_collect_cicd_workflow_hotspots(
            root, workflow_files, CICD_JOB_TERMS
        ),
        action_usage_hotspots=_collect_cicd_workflow_hotspots(
            root, workflow_files, CICD_ACTION_USAGE_TERMS
        ),
        run_command_hotspots=_collect_cicd_workflow_hotspots(
            root, workflow_files, CICD_RUN_COMMAND_TERMS
        ),
        quality_gate_hotspots=_collect_cicd_workflow_hotspots(
            root, workflow_files, CICD_QUALITY_GATE_TERMS
        ),
        risky_deploy_publish_hotspots=_collect_cicd_workflow_hotspots(
            root, workflow_files, CICD_RISKY_DEPLOY_PUBLISH_TERMS
        ),
        secret_usage_hotspots=_collect_cicd_workflow_hotspots(
            root, workflow_files, CICD_SECRET_USAGE_TERMS
        ),
        permission_hotspots=_collect_cicd_workflow_hotspots(
            root, workflow_files, CICD_PERMISSION_TERMS
        ),
        trading_broker_live_hotspots=_collect_cicd_workflow_hotspots(
            root, workflow_files, CICD_TRADING_BROKER_LIVE_TERMS
        ),
    )


def _is_time_schedule_python_file(relative_path: Path) -> bool:
    return (
        relative_path.suffix == ".py"
        and bool(relative_path.parts)
        and relative_path.parts[0] in RUNTIME_ENTRYPOINT_DIRECTORIES
    )


def _call_reference_name(node: ast.Call) -> str:
    parts: list[str] = []
    function: ast.AST = node.func

    while isinstance(function, ast.Attribute):
        parts.append(function.attr)
        function = function.value

    if isinstance(function, ast.Name):
        parts.append(function.id)

    return ".".join(reversed(parts))


def _is_datetime_now_call_without_timezone(node: ast.Call, call_reference: str) -> bool:
    if not call_reference.endswith(".now"):
        return False

    has_timezone_arg = bool(node.args) or any(
        keyword.arg in {"tz", "tzinfo"} for keyword in node.keywords
    )

    return not has_timezone_arg


def _is_naive_datetime_call(node: ast.Call) -> bool:
    call_reference = _call_reference_name(node)

    return (
        call_reference.endswith(".utcnow")
        or call_reference.endswith(".today")
        or _is_datetime_now_call_without_timezone(node, call_reference)
    )


def _collect_naive_datetime_hotspots_from_tree(
    relative_path: Path, tree: ast.AST
) -> tuple[str, ...]:
    hotspots: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _is_naive_datetime_call(node):
            hotspots.append(
                _format_line_hotspot(
                    relative_path,
                    node.lineno,
                    f"naive datetime call: {_call_reference_name(node)}",
                )
            )

    return tuple(hotspots)


def _has_time_schedule_file_signal(
    root: Path, relative_path: Path, imported_modules: tuple[str, ...]
) -> bool:
    path_text = _to_posix(relative_path).lower()

    if any(term in path_text for term in TIME_SCHEDULE_FILE_NAME_TERMS):
        return True

    if any(
        _matches_prefix(imported_module, TIME_SCHEDULE_IMPORT_PREFIXES)
        for imported_module in imported_modules
    ):
        return True

    text = _read_python_text(root / relative_path)

    return any(
        _matches_term(text, term)
        for term in (
            *TIMEZONE_TERMS,
            *SCHEDULE_TIMER_TERMS,
            *MARKET_CALENDAR_TERMS,
            *EXPIRY_SETTLEMENT_TERMS,
        )
    )


def _build_time_schedule_report(
    root: Path, relative_files: tuple[Path, ...]
) -> TimeScheduleReport:
    source_python_files = tuple(
        path for path in relative_files if _is_time_schedule_python_file(path)
    )
    time_schedule_files: list[str] = []
    time_import_hotspots: list[str] = []
    timezone_hotspots: list[str] = []
    schedule_timer_hotspots: list[str] = []
    market_calendar_hotspots: list[str] = []
    expiry_settlement_hotspots: list[str] = []
    naive_datetime_hotspots: list[str] = []
    parse_errors: list[str] = []

    for relative_path in source_python_files:
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
        time_import_hotspots.extend(
            _collect_import_hotspots(
                relative_path, imported_modules, TIME_SCHEDULE_IMPORT_PREFIXES
            )
        )

        if _has_time_schedule_file_signal(root, relative_path, imported_modules):
            time_schedule_files.append(_to_posix(relative_path))

        timezone_hotspots.extend(
            _collect_persistence_line_hotspots(root, relative_path, TIMEZONE_TERMS)
        )
        schedule_timer_hotspots.extend(
            _collect_persistence_line_hotspots(
                root,
                relative_path,
                SCHEDULE_TIMER_TERMS,
            )
        )
        market_calendar_hotspots.extend(
            _collect_persistence_line_hotspots(
                root,
                relative_path,
                MARKET_CALENDAR_TERMS,
            )
        )
        expiry_settlement_hotspots.extend(
            _collect_persistence_line_hotspots(
                root,
                relative_path,
                EXPIRY_SETTLEMENT_TERMS,
            )
        )
        naive_datetime_hotspots.extend(
            _collect_naive_datetime_hotspots_from_tree(relative_path, tree)
        )

    return TimeScheduleReport(
        source_python_files_scanned=len(source_python_files),
        time_schedule_files=tuple(sorted(time_schedule_files)),
        time_import_hotspots=tuple(time_import_hotspots),
        timezone_hotspots=tuple(timezone_hotspots),
        schedule_timer_hotspots=tuple(schedule_timer_hotspots),
        market_calendar_hotspots=tuple(market_calendar_hotspots),
        expiry_settlement_hotspots=tuple(expiry_settlement_hotspots),
        naive_datetime_hotspots=tuple(naive_datetime_hotspots),
        parse_errors=tuple(parse_errors),
    )


def _is_risk_strategy_python_file(relative_path: Path) -> bool:
    return relative_path.suffix == ".py" and _is_under(relative_path, "src")


def _has_risk_strategy_file_signal(root: Path, relative_path: Path) -> bool:
    path_text = _to_posix(relative_path).lower()

    if any(term in path_text for term in RISK_STRATEGY_FILE_NAME_TERMS):
        return True

    text = _read_python_text(root / relative_path)

    return any(
        _matches_term(text, term)
        for term in (
            *STRATEGY_DECISION_TERMS,
            *RISK_LIMIT_SIZING_TERMS,
            *ENTRY_EXIT_DECISION_TERMS,
            *PNL_POSITION_STATE_TERMS,
            *AUTO_DECISION_TERMS,
        )
    )


def _is_under_domain_package(relative_path: Path) -> bool:
    return _is_under_package(relative_path, ("src", PROJECT_PACKAGE, "domain"))


def _is_under_application_package(relative_path: Path) -> bool:
    return _is_under_package(relative_path, ("src", PROJECT_PACKAGE, "application"))


def _build_risk_strategy_decision_report(
    root: Path, relative_files: tuple[Path, ...]
) -> RiskStrategyDecisionReport:
    source_python_files = tuple(
        path for path in relative_files if _is_risk_strategy_python_file(path)
    )
    risk_strategy_files = tuple(
        sorted(
            path
            for path in source_python_files
            if _has_risk_strategy_file_signal(root, path)
        )
    )
    domain_strategy_files = tuple(
        path for path in risk_strategy_files if _is_under_domain_package(path)
    )
    application_strategy_files = tuple(
        path for path in risk_strategy_files if _is_under_application_package(path)
    )

    strategy_decision_hotspots: list[str] = []
    risk_limit_sizing_hotspots: list[str] = []
    entry_exit_decision_hotspots: list[str] = []
    pnl_position_state_hotspots: list[str] = []
    auto_decision_hotspots: list[str] = []
    parse_errors: list[str] = []

    for relative_path in source_python_files:
        try:
            ast.parse(
                _read_python_text(root / relative_path),
                filename=str(root / relative_path),
            )
        except SyntaxError as exc:
            parse_errors.append(f"{_to_posix(relative_path)} -> {exc.msg}")
            continue

        strategy_decision_hotspots.extend(
            _collect_persistence_line_hotspots(
                root, relative_path, STRATEGY_DECISION_TERMS
            )
        )
        risk_limit_sizing_hotspots.extend(
            _collect_persistence_line_hotspots(
                root, relative_path, RISK_LIMIT_SIZING_TERMS
            )
        )
        entry_exit_decision_hotspots.extend(
            _collect_persistence_line_hotspots(
                root, relative_path, ENTRY_EXIT_DECISION_TERMS
            )
        )
        pnl_position_state_hotspots.extend(
            _collect_persistence_line_hotspots(
                root, relative_path, PNL_POSITION_STATE_TERMS
            )
        )
        auto_decision_hotspots.extend(
            _collect_persistence_line_hotspots(root, relative_path, AUTO_DECISION_TERMS)
        )

    return RiskStrategyDecisionReport(
        source_python_files_scanned=len(source_python_files),
        risk_strategy_files=tuple(_to_posix(path) for path in risk_strategy_files),
        domain_strategy_files=tuple(_to_posix(path) for path in domain_strategy_files),
        application_strategy_files=tuple(
            _to_posix(path) for path in application_strategy_files
        ),
        strategy_decision_hotspots=tuple(strategy_decision_hotspots),
        risk_limit_sizing_hotspots=tuple(risk_limit_sizing_hotspots),
        entry_exit_decision_hotspots=tuple(entry_exit_decision_hotspots),
        pnl_position_state_hotspots=tuple(pnl_position_state_hotspots),
        auto_decision_hotspots=tuple(auto_decision_hotspots),
        parse_errors=tuple(parse_errors),
    )


def _is_cockpit_ui_python_file(relative_path: Path) -> bool:
    return relative_path.suffix == ".py" and _is_under(relative_path, "src")


def _has_cockpit_ui_file_signal(
    root: Path, relative_path: Path, imported_modules: tuple[str, ...]
) -> bool:
    path_text = _to_posix(relative_path).lower()

    if any(_matches_term(path_text, term) for term in COCKPIT_UI_FILE_NAME_TERMS):
        return True

    if any(
        _matches_prefix(imported_module, UI_FRAMEWORK_IMPORT_PREFIXES)
        for imported_module in imported_modules
    ):
        return True

    text = _read_python_text(root / relative_path)

    return any(
        _matches_term(text, term) for term in (*UI_SURFACE_TERMS, *UI_ACTION_TERMS)
    )


def _build_cockpit_ui_surface_report(
    root: Path, relative_files: tuple[Path, ...]
) -> CockpitUiSurfaceReport:
    source_python_files = tuple(
        path for path in relative_files if _is_cockpit_ui_python_file(path)
    )
    cockpit_ui_files: list[str] = []
    ui_framework_import_hotspots: list[str] = []
    ui_surface_hotspots: list[str] = []
    ui_action_hotspots: list[str] = []
    read_only_ui_hotspots: list[str] = []
    ui_trading_hotspots: list[str] = []
    direct_trading_action_hotspots: list[str] = []
    parse_errors: list[str] = []

    for relative_path in source_python_files:
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
        ui_framework_import_hotspots.extend(
            _collect_import_hotspots(
                relative_path, imported_modules, UI_FRAMEWORK_IMPORT_PREFIXES
            )
        )

        if _has_cockpit_ui_file_signal(root, relative_path, imported_modules):
            cockpit_ui_files.append(_to_posix(relative_path))

        ui_surface_hotspots.extend(
            _collect_persistence_line_hotspots(root, relative_path, UI_SURFACE_TERMS)
        )
        ui_action_hotspots.extend(
            _collect_persistence_line_hotspots(root, relative_path, UI_ACTION_TERMS)
        )
        read_only_ui_hotspots.extend(
            _collect_persistence_line_hotspots(root, relative_path, READ_ONLY_UI_TERMS)
        )
        ui_trading_hotspots.extend(
            _collect_persistence_line_hotspots(root, relative_path, UI_TRADING_TERMS)
        )
        direct_trading_action_hotspots.extend(
            _collect_persistence_line_hotspots(
                root, relative_path, DIRECT_TRADING_ACTION_TERMS
            )
        )

    return CockpitUiSurfaceReport(
        source_python_files_scanned=len(source_python_files),
        cockpit_ui_files=tuple(sorted(cockpit_ui_files)),
        ui_framework_import_hotspots=tuple(ui_framework_import_hotspots),
        ui_surface_hotspots=tuple(ui_surface_hotspots),
        ui_action_hotspots=tuple(ui_action_hotspots),
        read_only_ui_hotspots=tuple(read_only_ui_hotspots),
        ui_trading_hotspots=tuple(ui_trading_hotspots),
        direct_trading_action_hotspots=tuple(direct_trading_action_hotspots),
        parse_errors=tuple(parse_errors),
    )


def _is_artifact_metadata_scan_excluded(relative_path: Path) -> bool:
    return any(
        part in DATA_ARTIFACT_METADATA_EXCLUDED_DIRS for part in relative_path.parts
    )


def _iter_artifact_metadata_files(root: Path) -> tuple[Path, ...]:
    relative_files: list[Path] = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        relative_path = path.relative_to(root)

        if _is_artifact_metadata_scan_excluded(relative_path):
            continue

        relative_files.append(relative_path)

    return tuple(sorted(relative_files))


def _path_has_named_part(relative_path: Path, names: tuple[str, ...]) -> bool:
    normalized_names = set(names)

    return any(part.lower() in normalized_names for part in relative_path.parts)


def _is_data_artifact_file(relative_path: Path) -> bool:
    return relative_path.suffix.lower() in DATA_ARTIFACT_FILE_SUFFIXES


def _collect_artifact_directories(relative_files: tuple[Path, ...]) -> tuple[str, ...]:
    directories: set[str] = set()

    for relative_path in relative_files:
        for index, part in enumerate(relative_path.parts[:-1]):
            if part.lower() in DATA_ARTIFACT_DIRECTORY_NAMES:
                directories.add(Path(*relative_path.parts[: index + 1]).as_posix())

    return tuple(sorted(directories))


def _is_generated_export_report_artifact(relative_path: Path) -> bool:
    path_text = _to_posix(relative_path).lower()

    return _is_data_artifact_file(relative_path) and (
        _path_has_named_part(relative_path, DATA_ARTIFACT_DIRECTORY_NAMES)
        or any(_matches_term(path_text, term) for term in REPORT_ARTIFACT_TERMS)
    )


def _is_test_data_artifact(relative_path: Path) -> bool:
    return _is_data_artifact_file(relative_path) and _path_has_named_part(
        relative_path, TEST_DATA_DIRECTORY_NAMES
    )


def _is_runtime_data_artifact(relative_path: Path) -> bool:
    return _is_data_artifact_file(relative_path) and _path_has_named_part(
        relative_path, RUNTIME_ARTIFACT_DIRECTORY_NAMES
    )


def _format_path_terms_hotspot(relative_path: Path, terms: tuple[str, ...]) -> str:
    return f"{_to_posix(relative_path)} -> {', '.join(terms)}"


def _collect_sensitive_artifact_hotspots(
    data_artifact_files: tuple[Path, ...],
) -> tuple[str, ...]:
    hotspots: list[str] = []

    for relative_path in data_artifact_files:
        path_text = _to_posix(relative_path)
        matched_terms = _matching_terms(path_text, SENSITIVE_ARTIFACT_TERMS)

        if matched_terms:
            hotspots.append(_format_path_terms_hotspot(relative_path, matched_terms))

    return tuple(hotspots)


def _build_data_artifact_report(root: Path) -> DataArtifactReport:
    metadata_files = _iter_artifact_metadata_files(root)
    data_artifact_files = tuple(
        sorted(path for path in metadata_files if _is_data_artifact_file(path))
    )
    generated_export_report_artifacts = tuple(
        sorted(
            path
            for path in data_artifact_files
            if _is_generated_export_report_artifact(path)
        )
    )
    test_data_artifacts = tuple(
        sorted(path for path in data_artifact_files if _is_test_data_artifact(path))
    )
    runtime_data_artifacts = tuple(
        sorted(
            path
            for path in data_artifact_files
            if _is_runtime_data_artifact(path) and not _is_test_data_artifact(path)
        )
    )

    return DataArtifactReport(
        metadata_files_scanned=len(metadata_files),
        data_artifact_files=tuple(_to_posix(path) for path in data_artifact_files),
        artifact_directories=_collect_artifact_directories(metadata_files),
        generated_export_report_artifacts=tuple(
            _to_posix(path) for path in generated_export_report_artifacts
        ),
        test_data_artifacts=tuple(_to_posix(path) for path in test_data_artifacts),
        runtime_data_artifacts=tuple(
            _to_posix(path) for path in runtime_data_artifacts
        ),
        sensitive_artifact_hotspots=_collect_sensitive_artifact_hotspots(
            data_artifact_files
        ),
        versioned_runtime_artifacts=tuple(
            _to_posix(path) for path in runtime_data_artifacts
        ),
    )


def _extract_version_strings(line: str) -> tuple[str, ...]:
    return tuple(re.findall(VERSION_REFERENCE_PATTERN, line, flags=re.IGNORECASE))


def _format_versions_hotspot(
    relative_path: Path, line_number: int, versions: tuple[str, ...]
) -> str:
    return _format_line_hotspot(
        relative_path, line_number, f"versions: {', '.join(versions)}"
    )


def _collect_version_reference_hotspots(
    root: Path, relative_path: Path
) -> tuple[str, ...]:
    hotspots: list[str] = []

    for line_number, line in enumerate(
        _read_text(root / relative_path).splitlines(), start=1
    ):
        versions = _extract_version_strings(line)

        if versions:
            hotspots.append(
                _format_versions_hotspot(relative_path, line_number, versions)
            )

    return tuple(hotspots)


def _extract_pyproject_version(root: Path) -> str:
    pyproject_data, parse_errors = _load_pyproject_data(root)

    if parse_errors:
        return "parse error"

    project = pyproject_data.get("project", {})

    if not isinstance(project, dict):
        return "missing"

    version = project.get("version")

    return version if isinstance(version, str) else "missing"


def _read_version_file_value(root: Path) -> str:
    version_path = root / "VERSION"

    if not version_path.exists():
        return "missing"

    for line in _read_text(version_path).splitlines():
        stripped_line = line.strip()

        if stripped_line:
            return stripped_line

    return "empty"


def _is_release_root_file(relative_path: Path) -> bool:
    return (
        len(relative_path.parts) == 1
        and relative_path.name in RELEASE_VERSION_FILE_NAMES
    )


def _has_docs_version_signal(root: Path, relative_path: Path) -> bool:
    if not (_is_under(relative_path, "docs") and relative_path.suffix == ".md"):
        return False

    text = _read_text(root / relative_path)

    return bool(re.search(VERSION_REFERENCE_PATTERN, text, flags=re.IGNORECASE)) or any(
        _matches_term(text, term) for term in PRERELEASE_TERMS
    )


def _is_release_version_scan_file(root: Path, relative_path: Path) -> bool:
    if relative_path.suffix.lower() not in RELEASE_VERSION_SCAN_SUFFIXES and not (
        relative_path.name == "VERSION"
    ):
        return False

    return _is_release_root_file(relative_path) or _has_docs_version_signal(
        root, relative_path
    )


def _collect_release_version_files(
    root: Path, relative_files: tuple[Path, ...]
) -> tuple[Path, ...]:
    return tuple(
        sorted(
            (
                path
                for path in relative_files
                if _is_release_version_scan_file(root, path)
            ),
            key=lambda path: _to_posix(path).lower(),
        )
    )


def _collect_version_consistency_findings(
    root: Path, pyproject_version: str, version_file_value: str
) -> tuple[str, ...]:
    findings: list[str] = []

    if pyproject_version in {"missing", "parse error"}:
        findings.append(f"pyproject version {pyproject_version}")

    if version_file_value in {"missing", "empty"}:
        findings.append(f"VERSION file {version_file_value}")

    if (
        pyproject_version not in {"missing", "parse error"}
        and version_file_value not in {"missing", "empty"}
        and pyproject_version != version_file_value
    ):
        findings.append(
            "version mismatch: "
            f"pyproject.toml={pyproject_version}, VERSION={version_file_value}"
        )

    changelog_path = root / "CHANGELOG.md"

    if not changelog_path.exists():
        findings.append("CHANGELOG.md missing")
        return tuple(findings)

    current_version = (
        pyproject_version
        if pyproject_version not in {"missing", "parse error"}
        else version_file_value
    )

    if current_version not in {"missing", "empty", "parse error"} and (
        current_version not in _read_text(changelog_path)
    ):
        findings.append(
            f"CHANGELOG.md does not mention current version: {current_version}"
        )

    return tuple(findings)


def _build_release_version_report(
    root: Path, relative_files: tuple[Path, ...]
) -> ReleaseVersionReport:
    release_version_files = _collect_release_version_files(root, relative_files)
    pyproject_version = _extract_pyproject_version(root)
    version_file_value = _read_version_file_value(root)
    version_reference_hotspots: list[str] = []
    changelog_version_hotspots: list[str] = []
    readme_version_hotspots: list[str] = []
    docs_version_hotspots: list[str] = []
    prerelease_hotspots: list[str] = []
    release_tag_hotspots: list[str] = []

    for relative_path in release_version_files:
        file_version_hotspots = _collect_version_reference_hotspots(root, relative_path)
        version_reference_hotspots.extend(file_version_hotspots)

        if relative_path.name == "CHANGELOG.md":
            changelog_version_hotspots.extend(file_version_hotspots)

        if relative_path.name == "README.md":
            readme_version_hotspots.extend(file_version_hotspots)

        if _is_under(relative_path, "docs"):
            docs_version_hotspots.extend(file_version_hotspots)

        prerelease_hotspots.extend(
            _collect_persistence_line_hotspots(root, relative_path, PRERELEASE_TERMS)
        )
        release_tag_hotspots.extend(
            _collect_persistence_line_hotspots(root, relative_path, RELEASE_TAG_TERMS)
        )

    return ReleaseVersionReport(
        release_version_files=tuple(_to_posix(path) for path in release_version_files),
        pyproject_version=pyproject_version,
        version_file_value=version_file_value,
        changelog_present=(root / "CHANGELOG.md").is_file(),
        version_reference_hotspots=tuple(version_reference_hotspots),
        changelog_version_hotspots=tuple(changelog_version_hotspots),
        readme_version_hotspots=tuple(readme_version_hotspots),
        docs_version_hotspots=tuple(docs_version_hotspots),
        prerelease_hotspots=tuple(prerelease_hotspots),
        release_tag_hotspots=tuple(release_tag_hotspots),
        version_consistency_findings=_collect_version_consistency_findings(
            root, pyproject_version, version_file_value
        ),
    )


def _is_security_secret_text_file(relative_path: Path) -> bool:
    return (
        relative_path.name.startswith(".env")
        or relative_path.suffix.lower() in SECURITY_SECRET_TEXT_FILE_SUFFIXES
    )


def _is_env_key_cert_file(relative_path: Path) -> bool:
    return (
        relative_path.name.startswith(".env")
        or relative_path.suffix.lower() in SECURITY_SECRET_FILE_SUFFIXES
    )


def _has_security_sensitive_file_signal(root: Path, relative_path: Path) -> bool:
    path_text = _to_posix(relative_path).lower()

    if _is_env_key_cert_file(relative_path):
        return True

    if any(term in path_text for term in SECURITY_SECRET_FILE_NAME_TERMS):
        return True

    if not _is_security_secret_text_file(relative_path):
        return False

    text = _read_text(root / relative_path)

    return any(_matches_term(text, term) for term in SECURITY_SECRET_KEY_TERMS)


def _contains_security_secret_key(line: str) -> bool:
    return bool(_matching_terms(line, SECURITY_SECRET_KEY_TERMS))


def _is_secret_reference_value(value: str) -> bool:
    normalized_value = value.strip().strip("\"'").lower()

    return any(
        marker and marker in normalized_value
        for marker in SECURITY_HARDCODED_SECRET_VALUE_EXCLUSIONS
    )


def _is_hardcoded_secret_value_line(line: str) -> bool:
    if not _contains_security_secret_key(line):
        return False

    value = _extract_assignment_value(line)

    if value is None:
        return False

    normalized_value = value.strip().strip("\"'").lower()

    if not normalized_value:
        return False

    return not _is_secret_reference_value(normalized_value)


def _collect_hardcoded_secret_value_hotspots(
    root: Path, relative_path: Path
) -> tuple[str, ...]:
    hotspots: list[str] = []

    for line_number, line in enumerate(
        _read_text(root / relative_path).splitlines(), start=1
    ):
        if _is_hardcoded_secret_value_line(line):
            hotspots.append(
                _format_line_hotspot(
                    relative_path, line_number, "possible hardcoded secret value"
                )
            )

    return tuple(hotspots)


def _collect_gitignore_secret_protection_findings(root: Path) -> tuple[str, ...]:
    gitignore_path = root / ".gitignore"

    if not gitignore_path.exists():
        return (".gitignore missing",)

    gitignore_text = _read_text(gitignore_path)

    return tuple(
        f".gitignore missing secret pattern: {pattern}"
        for pattern in SECURITY_GITIGNORE_SECRET_PATTERNS
        if pattern not in gitignore_text
    )


def _build_security_secrets_report(
    root: Path, relative_files: tuple[Path, ...]
) -> SecuritySecretsReport:
    text_files = tuple(
        path for path in relative_files if _is_security_secret_text_file(path)
    )
    security_sensitive_files = tuple(
        sorted(
            (
                path
                for path in relative_files
                if _has_security_sensitive_file_signal(root, path)
            ),
            key=lambda path: _to_posix(path).lower(),
        )
    )
    env_key_cert_files = tuple(
        sorted(
            (path for path in relative_files if _is_env_key_cert_file(path)),
            key=lambda path: _to_posix(path).lower(),
        )
    )
    secret_reference_hotspots: list[str] = []
    hardcoded_secret_value_hotspots: list[str] = []
    broker_account_credential_hotspots: list[str] = []
    ci_secret_usage_hotspots: list[str] = []
    config_secret_usage_hotspots: list[str] = []
    source_secret_usage_hotspots: list[str] = []

    for relative_path in text_files:
        file_secret_reference_hotspots = _collect_persistence_line_hotspots(
            root, relative_path, SECURITY_SECRET_KEY_TERMS
        )
        file_hardcoded_secret_value_hotspots = _collect_hardcoded_secret_value_hotspots(
            root, relative_path
        )

        secret_reference_hotspots.extend(file_secret_reference_hotspots)
        hardcoded_secret_value_hotspots.extend(file_hardcoded_secret_value_hotspots)
        broker_account_credential_hotspots.extend(
            _collect_persistence_line_hotspots(
                root, relative_path, SECURITY_ACCOUNT_BROKER_TERMS
            )
        )

        if _is_under(relative_path, ".github"):
            ci_secret_usage_hotspots.extend(file_secret_reference_hotspots)

        if _is_under(relative_path, "config") or relative_path.name.startswith(".env"):
            config_secret_usage_hotspots.extend(file_secret_reference_hotspots)

        if _is_under(relative_path, "src"):
            source_secret_usage_hotspots.extend(file_secret_reference_hotspots)

    return SecuritySecretsReport(
        text_files_scanned=len(text_files),
        security_sensitive_files=tuple(
            _to_posix(path) for path in security_sensitive_files
        ),
        env_key_cert_files=tuple(_to_posix(path) for path in env_key_cert_files),
        secret_reference_hotspots=tuple(secret_reference_hotspots),
        hardcoded_secret_value_hotspots=tuple(hardcoded_secret_value_hotspots),
        broker_account_credential_hotspots=tuple(broker_account_credential_hotspots),
        ci_secret_usage_hotspots=tuple(ci_secret_usage_hotspots),
        config_secret_usage_hotspots=tuple(config_secret_usage_hotspots),
        source_secret_usage_hotspots=tuple(source_secret_usage_hotspots),
        gitignore_secret_protection_findings=(
            _collect_gitignore_secret_protection_findings(root)
        ),
    )


def _is_operations_text_file(relative_path: Path) -> bool:
    return relative_path.suffix.lower() in OPERATIONS_RUNBOOK_TEXT_FILE_SUFFIXES


def _is_operations_runbook_file(root: Path, relative_path: Path) -> bool:
    path_text = _to_posix(relative_path).lower()

    if not _is_operations_text_file(relative_path):
        return False

    if _is_under(relative_path, "docs") and "operations" in relative_path.parts:
        return True

    if any(term in path_text for term in OPERATIONS_RUNBOOK_FILE_NAME_TERMS):
        return True

    text = _read_text(root / relative_path)

    return any(
        _matches_term(text, term)
        for term in (
            *OPERATIONS_START_STOP_RESTART_TERMS,
            *OPERATIONS_RECOVERY_ROLLBACK_TERMS,
        )
    )


def _build_operations_runbook_report(
    root: Path, relative_files: tuple[Path, ...]
) -> OperationsRunbookReport:
    text_files = tuple(
        path for path in relative_files if _is_operations_text_file(path)
    )
    operations_runbook_files = tuple(
        sorted(
            (path for path in text_files if _is_operations_runbook_file(root, path)),
            key=lambda path: _to_posix(path).lower(),
        )
    )
    command_hotspots: list[str] = []
    start_stop_restart_hotspots: list[str] = []
    recovery_rollback_hotspots: list[str] = []
    destructive_command_hotspots: list[str] = []
    trading_broker_live_hotspots: list[str] = []

    for relative_path in operations_runbook_files:
        command_hotspots.extend(
            _collect_persistence_line_hotspots(
                root, relative_path, OPERATIONS_COMMAND_TERMS
            )
        )
        start_stop_restart_hotspots.extend(
            _collect_persistence_line_hotspots(
                root, relative_path, OPERATIONS_START_STOP_RESTART_TERMS
            )
        )
        recovery_rollback_hotspots.extend(
            _collect_persistence_line_hotspots(
                root, relative_path, OPERATIONS_RECOVERY_ROLLBACK_TERMS
            )
        )
        destructive_command_hotspots.extend(
            _collect_persistence_line_hotspots(
                root, relative_path, OPERATIONS_DESTRUCTIVE_COMMAND_TERMS
            )
        )
        trading_broker_live_hotspots.extend(
            _collect_persistence_line_hotspots(
                root, relative_path, OPERATIONS_TRADING_BROKER_LIVE_TERMS
            )
        )

    return OperationsRunbookReport(
        text_files_scanned=len(text_files),
        operations_runbook_files=tuple(
            _to_posix(path) for path in operations_runbook_files
        ),
        command_hotspots=tuple(command_hotspots),
        start_stop_restart_hotspots=tuple(start_stop_restart_hotspots),
        recovery_rollback_hotspots=tuple(recovery_rollback_hotspots),
        destructive_command_hotspots=tuple(destructive_command_hotspots),
        trading_broker_live_hotspots=tuple(trading_broker_live_hotspots),
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
        trading_safety=_build_trading_safety_report(resolved_root, relative_files),
        import_map=_build_import_map_report(resolved_root, relative_files),
        test_structure=_build_test_structure_report(relative_files),
        configuration_safety=_build_configuration_safety_report(
            resolved_root, relative_files
        ),
        runtime_entrypoints=_build_runtime_entrypoint_report(
            resolved_root, relative_files
        ),
        dependency_packaging=_build_dependency_packaging_report(
            resolved_root, relative_files
        ),
        persistence_state=_build_persistence_state_report(
            resolved_root, relative_files
        ),
        observability_logging=_build_observability_logging_report(
            resolved_root, relative_files
        ),
        external_interfaces=_build_external_interface_report(
            resolved_root, relative_files
        ),
        cicd_workflows=_build_cicd_workflow_report(resolved_root, relative_files),
        time_schedule=_build_time_schedule_report(resolved_root, relative_files),
        risk_strategy_decisions=_build_risk_strategy_decision_report(
            resolved_root, relative_files
        ),
        cockpit_ui_surfaces=_build_cockpit_ui_surface_report(
            resolved_root, relative_files
        ),
        data_artifacts=_build_data_artifact_report(resolved_root),
        release_versions=_build_release_version_report(resolved_root, relative_files),
        security_secrets=_build_security_secrets_report(resolved_root, relative_files),
        operations_runbooks=_build_operations_runbook_report(
            resolved_root, relative_files
        ),
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
    trading_safety = report.trading_safety
    import_map = report.import_map
    test_structure = report.test_structure
    configuration_safety = report.configuration_safety
    runtime_entrypoints = report.runtime_entrypoints
    dependency_packaging = report.dependency_packaging
    persistence_state = report.persistence_state
    observability_logging = report.observability_logging
    external_interfaces = report.external_interfaces
    cicd_workflows = report.cicd_workflows
    time_schedule = report.time_schedule
    risk_strategy_decisions = report.risk_strategy_decisions
    cockpit_ui_surfaces = report.cockpit_ui_surfaces
    data_artifacts = report.data_artifacts
    release_versions = report.release_versions
    security_secrets = report.security_secrets
    operations_runbooks = report.operations_runbooks
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
        "Trading safety checks:",
        f"- source files scanned: {trading_safety.source_files_scanned}",
        "- trading-related files: "
        f"{_format_items(trading_safety.trading_related_files)}",
        f"- order hotspots: {_format_items(trading_safety.order_hotspots)}",
        f"- broker hotspots: {_format_items(trading_safety.broker_hotspots)}",
        "- LIVE/PAPER hotspots: "
        f"{_format_items(trading_safety.live_environment_hotspots)}",
        f"- retry hotspots: {_format_items(trading_safety.retry_hotspots)}",
        "- reconciliation hotspots: "
        f"{_format_items(trading_safety.reconciliation_hotspots)}",
        f"- execution hotspots: {_format_items(trading_safety.execution_hotspots)}",
        "",
        "Import map checks:",
        f"- source modules: {import_map.source_modules}",
        f"- internal import edges: {_format_items(import_map.internal_import_edges)}",
        f"- external import roots: {_format_items(import_map.external_import_roots)}",
        "- module dependency counts: "
        f"{_format_items(import_map.module_dependency_counts)}",
        f"- highly coupled modules: {_format_items(import_map.highly_coupled_modules)}",
        f"- import map parse errors: {_format_items(import_map.parse_errors)}",
        "",
        "Test structure checks:",
        f"- source modules: {test_structure.source_modules}",
        f"- test files: {test_structure.test_files}",
        "- test categories present: "
        f"{_format_items(test_structure.test_categories_present)}",
        "- test categories missing: "
        f"{_format_items(test_structure.test_categories_missing)}",
        f"- test category counts: {_format_items(test_structure.test_category_counts)}",
        "- source modules without direct tests: "
        f"{_format_items(test_structure.source_modules_without_direct_tests)}",
        f"- direct test matches: {_format_items(test_structure.direct_test_matches)}",
        "",
        "Configuration safety checks:",
        "- configuration files: "
        f"{_format_items(configuration_safety.configuration_files)}",
        "- expected config files present: "
        f"{_format_items(configuration_safety.expected_configuration_files_present)}",
        "- expected config files missing: "
        f"{_format_items(configuration_safety.expected_configuration_files_missing)}",
        "- environment hotspots: "
        f"{_format_items(configuration_safety.environment_hotspots)}",
        "- secret reference hotspots: "
        f"{_format_items(configuration_safety.secret_reference_hotspots)}",
        "- possible plain secret value hotspots: "
        f"{_format_items(configuration_safety.possible_plain_secret_value_hotspots)}",
        "- LIVE default hotspots: "
        f"{_format_items(configuration_safety.live_default_hotspots)}",
        "",
        "Runtime entrypoint checks:",
        "- runtime Python files scanned: "
        f"{runtime_entrypoints.runtime_python_files_scanned}",
        f"- script files: {_format_items(runtime_entrypoints.script_files)}",
        f"- tool files: {_format_items(runtime_entrypoints.tool_files)}",
        "- Python entrypoint files: "
        f"{_format_items(runtime_entrypoints.python_entrypoint_files)}",
        f"- CLI parser files: {_format_items(runtime_entrypoints.cli_parser_files)}",
        "- pyproject script entries: "
        f"{_format_items(runtime_entrypoints.pyproject_script_entries)}",
        "- entrypoint trading hotspots: "
        f"{_format_items(runtime_entrypoints.entrypoint_trading_hotspots)}",
        "- entrypoint runtime default hotspots: "
        f"{_format_items(runtime_entrypoints.entrypoint_runtime_default_hotspots)}",
        "- runtime entrypoint parse errors: "
        f"{_format_items(runtime_entrypoints.parse_errors)}",
        "",
        "Dependency / packaging checks:",
        "- pyproject.toml present: "
        f"{_format_bool(dependency_packaging.pyproject_present)}",
        f"- build backend: {dependency_packaging.build_backend}",
        f"- requires Python: {dependency_packaging.requires_python}",
        "- build-system requires: "
        f"{_format_items(dependency_packaging.build_system_requires)}",
        f"- dependency files: {_format_items(dependency_packaging.dependency_files)}",
        f"- lock files: {_format_items(dependency_packaging.lock_files)}",
        "- packaging tool sections: "
        f"{_format_items(dependency_packaging.packaging_tool_sections)}",
        "- pyproject dependency entries: "
        f"{_format_items(dependency_packaging.pyproject_dependency_entries)}",
        "- requirement file entries: "
        f"{_format_items(dependency_packaging.requirement_file_entries)}",
        "- unpinned dependency entries: "
        f"{_format_items(dependency_packaging.unpinned_dependency_entries)}",
        "- editable/path dependency entries: "
        f"{_format_items(dependency_packaging.editable_or_path_dependency_entries)}",
        "- dependency packaging parse errors: "
        f"{_format_items(dependency_packaging.parse_errors)}",
        "",
        "Persistence / state checks:",
        f"- database files: {_format_items(persistence_state.database_files)}",
        f"- migration files: {_format_items(persistence_state.migration_files)}",
        "- persistence directories: "
        f"{_format_items(persistence_state.persistence_directories)}",
        "- persistence Python files: "
        f"{_format_items(persistence_state.persistence_python_files)}",
        "- persistence import hotspots: "
        f"{_format_items(persistence_state.persistence_import_hotspots)}",
        "- persistence write hotspots: "
        f"{_format_items(persistence_state.persistence_write_hotspots)}",
        "- trading state hotspots: "
        f"{_format_items(persistence_state.trading_state_hotspots)}",
        f"- persistence parse errors: {_format_items(persistence_state.parse_errors)}",
        "",
        "Observability / logging checks:",
        "- observability files: "
        f"{_format_items(observability_logging.observability_files)}",
        "- logging config files: "
        f"{_format_items(observability_logging.logging_config_files)}",
        "- logging Python files: "
        f"{_format_items(observability_logging.logging_python_files)}",
        "- logging import hotspots: "
        f"{_format_items(observability_logging.logging_import_hotspots)}",
        "- logging call hotspots: "
        f"{_format_items(observability_logging.logging_call_hotspots)}",
        f"- print hotspots: {_format_items(observability_logging.print_hotspots)}",
        "- exception handler hotspots: "
        f"{_format_items(observability_logging.exception_handler_hotspots)}",
        "- silent exception hotspots: "
        f"{_format_items(observability_logging.silent_exception_hotspots)}",
        f"- pass hotspots: {_format_items(observability_logging.pass_hotspots)}",
        "- critical event hotspots: "
        f"{_format_items(observability_logging.critical_event_hotspots)}",
        "- observability parse errors: "
        f"{_format_items(observability_logging.parse_errors)}",
        "",
        "External interface / broker boundary checks:",
        "- source Python files scanned: "
        f"{external_interfaces.source_python_files_scanned}",
        "- external interface files: "
        f"{_format_items(external_interfaces.external_interface_files)}",
        "- broker import hotspots: "
        f"{_format_items(external_interfaces.broker_import_hotspots)}",
        "- network import hotspots: "
        f"{_format_items(external_interfaces.network_import_hotspots)}",
        "- broker term hotspots: "
        f"{_format_items(external_interfaces.broker_term_hotspots)}",
        "- network term hotspots: "
        f"{_format_items(external_interfaces.network_term_hotspots)}",
        "- order/execution interface hotspots: "
        f"{_format_items(external_interfaces.order_execution_interface_hotspots)}",
        "- domain external import violations: "
        f"{_format_items(external_interfaces.domain_external_import_violations)}",
        "- application external import violations: "
        f"{_format_items(external_interfaces.application_external_import_violations)}",
        "- external interface parse errors: "
        f"{_format_items(external_interfaces.parse_errors)}",
        "",
        "CI/CD workflow checks:",
        f"- workflow files: {_format_items(cicd_workflows.workflow_files)}",
        "- workflow trigger hotspots: "
        f"{_format_items(cicd_workflows.workflow_trigger_hotspots)}",
        f"- job hotspots: {_format_items(cicd_workflows.job_hotspots)}",
        "- action usage hotspots: "
        f"{_format_items(cicd_workflows.action_usage_hotspots)}",
        f"- run command hotspots: {_format_items(cicd_workflows.run_command_hotspots)}",
        "- quality gate hotspots: "
        f"{_format_items(cicd_workflows.quality_gate_hotspots)}",
        "- risky deploy/publish hotspots: "
        f"{_format_items(cicd_workflows.risky_deploy_publish_hotspots)}",
        "- secret usage hotspots: "
        f"{_format_items(cicd_workflows.secret_usage_hotspots)}",
        f"- permission hotspots: {_format_items(cicd_workflows.permission_hotspots)}",
        "- trading/broker/LIVE hotspots: "
        f"{_format_items(cicd_workflows.trading_broker_live_hotspots)}",
        "",
        "Time / schedule / market calendar checks:",
        f"- source Python files scanned: {time_schedule.source_python_files_scanned}",
        f"- time/schedule files: {_format_items(time_schedule.time_schedule_files)}",
        f"- time import hotspots: {_format_items(time_schedule.time_import_hotspots)}",
        f"- timezone hotspots: {_format_items(time_schedule.timezone_hotspots)}",
        "- schedule/timer hotspots: "
        f"{_format_items(time_schedule.schedule_timer_hotspots)}",
        "- market calendar hotspots: "
        f"{_format_items(time_schedule.market_calendar_hotspots)}",
        "- expiry/settlement hotspots: "
        f"{_format_items(time_schedule.expiry_settlement_hotspots)}",
        "- naive datetime hotspots: "
        f"{_format_items(time_schedule.naive_datetime_hotspots)}",
        f"- time schedule parse errors: {_format_items(time_schedule.parse_errors)}",
        "",
        "Risk / strategy / decision checks:",
        "- source Python files scanned: "
        f"{risk_strategy_decisions.source_python_files_scanned}",
        "- risk/strategy files: "
        f"{_format_items(risk_strategy_decisions.risk_strategy_files)}",
        "- domain strategy files: "
        f"{_format_items(risk_strategy_decisions.domain_strategy_files)}",
        "- application strategy files: "
        f"{_format_items(risk_strategy_decisions.application_strategy_files)}",
        "- strategy/decision hotspots: "
        f"{_format_items(risk_strategy_decisions.strategy_decision_hotspots)}",
        "- risk/limit/sizing hotspots: "
        f"{_format_items(risk_strategy_decisions.risk_limit_sizing_hotspots)}",
        "- entry/exit decision hotspots: "
        f"{_format_items(risk_strategy_decisions.entry_exit_decision_hotspots)}",
        "- PnL/position/state hotspots: "
        f"{_format_items(risk_strategy_decisions.pnl_position_state_hotspots)}",
        "- auto decision hotspots: "
        f"{_format_items(risk_strategy_decisions.auto_decision_hotspots)}",
        "- risk strategy parse errors: "
        f"{_format_items(risk_strategy_decisions.parse_errors)}",
        "",
        "Cockpit / UI surface checks:",
        "- source Python files scanned: "
        f"{cockpit_ui_surfaces.source_python_files_scanned}",
        f"- cockpit/UI files: {_format_items(cockpit_ui_surfaces.cockpit_ui_files)}",
        "- UI framework import hotspots: "
        f"{_format_items(cockpit_ui_surfaces.ui_framework_import_hotspots)}",
        "- UI surface hotspots: "
        f"{_format_items(cockpit_ui_surfaces.ui_surface_hotspots)}",
        "- UI action hotspots: "
        f"{_format_items(cockpit_ui_surfaces.ui_action_hotspots)}",
        "- read-only UI hotspots: "
        f"{_format_items(cockpit_ui_surfaces.read_only_ui_hotspots)}",
        "- UI trading hotspots: "
        f"{_format_items(cockpit_ui_surfaces.ui_trading_hotspots)}",
        "- direct trading action hotspots: "
        f"{_format_items(cockpit_ui_surfaces.direct_trading_action_hotspots)}",
        f"- cockpit UI parse errors: {_format_items(cockpit_ui_surfaces.parse_errors)}",
        "",
        "Data / artifact / export checks:",
        f"- metadata files scanned: {data_artifacts.metadata_files_scanned}",
        f"- data artifact files: {_format_items(data_artifacts.data_artifact_files)}",
        f"- artifact directories: {_format_items(data_artifacts.artifact_directories)}",
        "- generated/export/report artifacts: "
        f"{_format_items(data_artifacts.generated_export_report_artifacts)}",
        f"- test data artifacts: {_format_items(data_artifacts.test_data_artifacts)}",
        "- runtime data artifacts: "
        f"{_format_items(data_artifacts.runtime_data_artifacts)}",
        "- sensitive artifact hotspots: "
        f"{_format_items(data_artifacts.sensitive_artifact_hotspots)}",
        "- versioned runtime artifacts: "
        f"{_format_items(data_artifacts.versioned_runtime_artifacts)}",
        "- content scan: disabled (metadata-only path scan)",
        "",
        "Release / version / changelog checks:",
        "- release/version files: "
        f"{_format_items(release_versions.release_version_files)}",
        f"- pyproject version: {release_versions.pyproject_version}",
        f"- VERSION file value: {release_versions.version_file_value}",
        f"- CHANGELOG.md present: {_format_bool(release_versions.changelog_present)}",
        "- version reference hotspots: "
        f"{_format_items(release_versions.version_reference_hotspots)}",
        "- CHANGELOG version hotspots: "
        f"{_format_items(release_versions.changelog_version_hotspots)}",
        "- README version hotspots: "
        f"{_format_items(release_versions.readme_version_hotspots)}",
        "- docs version hotspots: "
        f"{_format_items(release_versions.docs_version_hotspots)}",
        f"- prerelease hotspots: {_format_items(release_versions.prerelease_hotspots)}",
        "- release/tag hotspots: "
        f"{_format_items(release_versions.release_tag_hotspots)}",
        "- version consistency findings: "
        f"{_format_items(release_versions.version_consistency_findings)}",
        "",
        "Security / secrets / credential checks:",
        f"- text files scanned: {security_secrets.text_files_scanned}",
        "- security sensitive files: "
        f"{_format_items(security_secrets.security_sensitive_files)}",
        f"- env/key/cert files: {_format_items(security_secrets.env_key_cert_files)}",
        "- secret reference hotspots: "
        f"{_format_items(security_secrets.secret_reference_hotspots)}",
        "- hardcoded secret value hotspots: "
        f"{_format_items(security_secrets.hardcoded_secret_value_hotspots)}",
        "- broker/account/credential hotspots: "
        f"{_format_items(security_secrets.broker_account_credential_hotspots)}",
        "- CI secret usage hotspots: "
        f"{_format_items(security_secrets.ci_secret_usage_hotspots)}",
        "- config secret usage hotspots: "
        f"{_format_items(security_secrets.config_secret_usage_hotspots)}",
        "- source secret usage hotspots: "
        f"{_format_items(security_secrets.source_secret_usage_hotspots)}",
        "- .gitignore secret protection findings: "
        f"{_format_items(security_secrets.gitignore_secret_protection_findings)}",
        "",
        "Operations / runbook / recovery checks:",
        f"- text files scanned: {operations_runbooks.text_files_scanned}",
        "- operations/runbook files: "
        f"{_format_items(operations_runbooks.operations_runbook_files)}",
        f"- command hotspots: {_format_items(operations_runbooks.command_hotspots)}",
        "- start/stop/restart hotspots: "
        f"{_format_items(operations_runbooks.start_stop_restart_hotspots)}",
        "- recovery/rollback hotspots: "
        f"{_format_items(operations_runbooks.recovery_rollback_hotspots)}",
        "- destructive command hotspots: "
        f"{_format_items(operations_runbooks.destructive_command_hotspots)}",
        "- trading/broker/LIVE hotspots: "
        f"{_format_items(operations_runbooks.trading_broker_live_hotspots)}",
        "",
        "Safety:",
        "- mode: read-only",
        "- file writes: disabled",
        "- broker access: disabled",
        "- trading access: disabled",
        "- LIVE access: disabled",
    ]

    return "\n".join(lines)


def _documentation_report_to_dict(
    report: DocumentationCheckReport,
) -> dict[str, object]:
    return {
        "docs_directory_present": report.docs_directory_present,
        "agents_file_present": report.agents_file_present,
        "documentation_markdown_files": report.documentation_markdown_files,
        "present_important_documentation_paths": list(
            report.present_important_documentation_paths
        ),
        "missing_important_documentation_paths": list(
            report.missing_important_documentation_paths
        ),
        "empty_markdown_files": list(report.empty_markdown_files),
        "placeholder_markdown_files": list(report.placeholder_markdown_files),
        "generated_docs_ignored": True,
    }


def _architecture_report_to_dict(
    report: ArchitectureCheckReport,
) -> dict[str, object]:
    return {
        "architecture_source_files": report.architecture_source_files,
        "domain_files": report.domain_files,
        "application_files": report.application_files,
        "domain_import_violations": list(report.domain_import_violations),
        "application_import_violations": list(report.application_import_violations),
        "parse_errors": list(report.parse_errors),
    }


def _trading_safety_report_to_dict(
    report: TradingSafetyCheckReport,
) -> dict[str, object]:
    return {
        "source_files_scanned": report.source_files_scanned,
        "trading_related_files": list(report.trading_related_files),
        "order_hotspots": list(report.order_hotspots),
        "broker_hotspots": list(report.broker_hotspots),
        "live_environment_hotspots": list(report.live_environment_hotspots),
        "retry_hotspots": list(report.retry_hotspots),
        "reconciliation_hotspots": list(report.reconciliation_hotspots),
        "execution_hotspots": list(report.execution_hotspots),
    }


def _import_map_report_to_dict(report: ImportMapReport) -> dict[str, object]:
    return {
        "source_modules": report.source_modules,
        "internal_import_edges": list(report.internal_import_edges),
        "external_import_roots": list(report.external_import_roots),
        "module_dependency_counts": list(report.module_dependency_counts),
        "highly_coupled_modules": list(report.highly_coupled_modules),
        "parse_errors": list(report.parse_errors),
        "high_coupling_threshold": HIGH_COUPLING_THRESHOLD,
    }


def _test_structure_report_to_dict(
    report: TestStructureReport,
) -> dict[str, object]:
    return {
        "source_modules": report.source_modules,
        "test_files": report.test_files,
        "test_categories_present": list(report.test_categories_present),
        "test_categories_missing": list(report.test_categories_missing),
        "test_category_counts": list(report.test_category_counts),
        "source_modules_without_direct_tests": list(
            report.source_modules_without_direct_tests
        ),
        "direct_test_matches": list(report.direct_test_matches),
    }


def _configuration_safety_report_to_dict(
    report: ConfigurationSafetyReport,
) -> dict[str, object]:
    return {
        "configuration_files": list(report.configuration_files),
        "expected_configuration_files_present": list(
            report.expected_configuration_files_present
        ),
        "expected_configuration_files_missing": list(
            report.expected_configuration_files_missing
        ),
        "environment_hotspots": list(report.environment_hotspots),
        "secret_reference_hotspots": list(report.secret_reference_hotspots),
        "possible_plain_secret_value_hotspots": list(
            report.possible_plain_secret_value_hotspots
        ),
        "live_default_hotspots": list(report.live_default_hotspots),
    }


def _runtime_entrypoint_report_to_dict(
    report: RuntimeEntrypointReport,
) -> dict[str, object]:
    return {
        "runtime_python_files_scanned": report.runtime_python_files_scanned,
        "script_files": list(report.script_files),
        "tool_files": list(report.tool_files),
        "python_entrypoint_files": list(report.python_entrypoint_files),
        "cli_parser_files": list(report.cli_parser_files),
        "pyproject_script_entries": list(report.pyproject_script_entries),
        "entrypoint_trading_hotspots": list(report.entrypoint_trading_hotspots),
        "entrypoint_runtime_default_hotspots": list(
            report.entrypoint_runtime_default_hotspots
        ),
        "parse_errors": list(report.parse_errors),
    }


def _dependency_packaging_report_to_dict(
    report: DependencyPackagingReport,
) -> dict[str, object]:
    return {
        "pyproject_present": report.pyproject_present,
        "build_backend": report.build_backend,
        "requires_python": report.requires_python,
        "build_system_requires": list(report.build_system_requires),
        "dependency_files": list(report.dependency_files),
        "lock_files": list(report.lock_files),
        "packaging_tool_sections": list(report.packaging_tool_sections),
        "pyproject_dependency_entries": list(report.pyproject_dependency_entries),
        "requirement_file_entries": list(report.requirement_file_entries),
        "unpinned_dependency_entries": list(report.unpinned_dependency_entries),
        "editable_or_path_dependency_entries": list(
            report.editable_or_path_dependency_entries
        ),
        "parse_errors": list(report.parse_errors),
    }


def _persistence_state_report_to_dict(
    report: PersistenceStateReport,
) -> dict[str, object]:
    return {
        "database_files": list(report.database_files),
        "migration_files": list(report.migration_files),
        "persistence_directories": list(report.persistence_directories),
        "persistence_python_files": list(report.persistence_python_files),
        "persistence_import_hotspots": list(report.persistence_import_hotspots),
        "persistence_write_hotspots": list(report.persistence_write_hotspots),
        "trading_state_hotspots": list(report.trading_state_hotspots),
        "parse_errors": list(report.parse_errors),
    }


def _observability_logging_report_to_dict(
    report: ObservabilityLoggingReport,
) -> dict[str, object]:
    return {
        "observability_files": list(report.observability_files),
        "logging_config_files": list(report.logging_config_files),
        "logging_python_files": list(report.logging_python_files),
        "logging_import_hotspots": list(report.logging_import_hotspots),
        "logging_call_hotspots": list(report.logging_call_hotspots),
        "print_hotspots": list(report.print_hotspots),
        "exception_handler_hotspots": list(report.exception_handler_hotspots),
        "silent_exception_hotspots": list(report.silent_exception_hotspots),
        "pass_hotspots": list(report.pass_hotspots),
        "critical_event_hotspots": list(report.critical_event_hotspots),
        "parse_errors": list(report.parse_errors),
    }


def _external_interface_report_to_dict(
    report: ExternalInterfaceReport,
) -> dict[str, object]:
    return {
        "source_python_files_scanned": report.source_python_files_scanned,
        "external_interface_files": list(report.external_interface_files),
        "broker_import_hotspots": list(report.broker_import_hotspots),
        "network_import_hotspots": list(report.network_import_hotspots),
        "broker_term_hotspots": list(report.broker_term_hotspots),
        "network_term_hotspots": list(report.network_term_hotspots),
        "order_execution_interface_hotspots": list(
            report.order_execution_interface_hotspots
        ),
        "domain_external_import_violations": list(
            report.domain_external_import_violations
        ),
        "application_external_import_violations": list(
            report.application_external_import_violations
        ),
        "parse_errors": list(report.parse_errors),
    }


def _cicd_workflow_report_to_dict(report: CicdWorkflowReport) -> dict[str, object]:
    return {
        "workflow_files": list(report.workflow_files),
        "workflow_trigger_hotspots": list(report.workflow_trigger_hotspots),
        "job_hotspots": list(report.job_hotspots),
        "action_usage_hotspots": list(report.action_usage_hotspots),
        "run_command_hotspots": list(report.run_command_hotspots),
        "quality_gate_hotspots": list(report.quality_gate_hotspots),
        "risky_deploy_publish_hotspots": list(report.risky_deploy_publish_hotspots),
        "secret_usage_hotspots": list(report.secret_usage_hotspots),
        "permission_hotspots": list(report.permission_hotspots),
        "trading_broker_live_hotspots": list(report.trading_broker_live_hotspots),
    }


def _time_schedule_report_to_dict(report: TimeScheduleReport) -> dict[str, object]:
    return {
        "source_python_files_scanned": report.source_python_files_scanned,
        "time_schedule_files": list(report.time_schedule_files),
        "time_import_hotspots": list(report.time_import_hotspots),
        "timezone_hotspots": list(report.timezone_hotspots),
        "schedule_timer_hotspots": list(report.schedule_timer_hotspots),
        "market_calendar_hotspots": list(report.market_calendar_hotspots),
        "expiry_settlement_hotspots": list(report.expiry_settlement_hotspots),
        "naive_datetime_hotspots": list(report.naive_datetime_hotspots),
        "parse_errors": list(report.parse_errors),
    }


def _risk_strategy_decision_report_to_dict(
    report: RiskStrategyDecisionReport,
) -> dict[str, object]:
    return {
        "source_python_files_scanned": report.source_python_files_scanned,
        "risk_strategy_files": list(report.risk_strategy_files),
        "domain_strategy_files": list(report.domain_strategy_files),
        "application_strategy_files": list(report.application_strategy_files),
        "strategy_decision_hotspots": list(report.strategy_decision_hotspots),
        "risk_limit_sizing_hotspots": list(report.risk_limit_sizing_hotspots),
        "entry_exit_decision_hotspots": list(report.entry_exit_decision_hotspots),
        "pnl_position_state_hotspots": list(report.pnl_position_state_hotspots),
        "auto_decision_hotspots": list(report.auto_decision_hotspots),
        "parse_errors": list(report.parse_errors),
    }


def _cockpit_ui_surface_report_to_dict(
    report: CockpitUiSurfaceReport,
) -> dict[str, object]:
    return {
        "source_python_files_scanned": report.source_python_files_scanned,
        "cockpit_ui_files": list(report.cockpit_ui_files),
        "ui_framework_import_hotspots": list(report.ui_framework_import_hotspots),
        "ui_surface_hotspots": list(report.ui_surface_hotspots),
        "ui_action_hotspots": list(report.ui_action_hotspots),
        "read_only_ui_hotspots": list(report.read_only_ui_hotspots),
        "ui_trading_hotspots": list(report.ui_trading_hotspots),
        "direct_trading_action_hotspots": list(report.direct_trading_action_hotspots),
        "parse_errors": list(report.parse_errors),
    }


def _data_artifact_report_to_dict(report: DataArtifactReport) -> dict[str, object]:
    return {
        "metadata_files_scanned": report.metadata_files_scanned,
        "data_artifact_files": list(report.data_artifact_files),
        "artifact_directories": list(report.artifact_directories),
        "generated_export_report_artifacts": list(
            report.generated_export_report_artifacts
        ),
        "test_data_artifacts": list(report.test_data_artifacts),
        "runtime_data_artifacts": list(report.runtime_data_artifacts),
        "sensitive_artifact_hotspots": list(report.sensitive_artifact_hotspots),
        "versioned_runtime_artifacts": list(report.versioned_runtime_artifacts),
    }


def _release_version_report_to_dict(report: ReleaseVersionReport) -> dict[str, object]:
    return {
        "release_version_files": list(report.release_version_files),
        "pyproject_version": report.pyproject_version,
        "version_file_value": report.version_file_value,
        "changelog_present": report.changelog_present,
        "version_reference_hotspots": list(report.version_reference_hotspots),
        "changelog_version_hotspots": list(report.changelog_version_hotspots),
        "readme_version_hotspots": list(report.readme_version_hotspots),
        "docs_version_hotspots": list(report.docs_version_hotspots),
        "prerelease_hotspots": list(report.prerelease_hotspots),
        "release_tag_hotspots": list(report.release_tag_hotspots),
        "version_consistency_findings": list(report.version_consistency_findings),
    }


def _security_secrets_report_to_dict(
    report: SecuritySecretsReport,
) -> dict[str, object]:
    return {
        "text_files_scanned": report.text_files_scanned,
        "security_sensitive_files": list(report.security_sensitive_files),
        "env_key_cert_files": list(report.env_key_cert_files),
        "secret_reference_hotspots": list(report.secret_reference_hotspots),
        "hardcoded_secret_value_hotspots": list(report.hardcoded_secret_value_hotspots),
        "broker_account_credential_hotspots": list(
            report.broker_account_credential_hotspots
        ),
        "ci_secret_usage_hotspots": list(report.ci_secret_usage_hotspots),
        "config_secret_usage_hotspots": list(report.config_secret_usage_hotspots),
        "source_secret_usage_hotspots": list(report.source_secret_usage_hotspots),
        "gitignore_secret_protection_findings": list(
            report.gitignore_secret_protection_findings
        ),
    }


def _operations_runbook_report_to_dict(
    report: OperationsRunbookReport,
) -> dict[str, object]:
    return {
        "text_files_scanned": report.text_files_scanned,
        "operations_runbook_files": list(report.operations_runbook_files),
        "command_hotspots": list(report.command_hotspots),
        "start_stop_restart_hotspots": list(report.start_stop_restart_hotspots),
        "recovery_rollback_hotspots": list(report.recovery_rollback_hotspots),
        "destructive_command_hotspots": list(report.destructive_command_hotspots),
        "trading_broker_live_hotspots": list(report.trading_broker_live_hotspots),
    }


def collect_quality_gate_failures(report: ProjectAnalysisReport) -> tuple[str, ...]:
    documentation = report.documentation
    architecture = report.architecture
    failures: list[str] = []

    if not documentation.docs_directory_present:
        failures.append("docs directory missing")

    if not documentation.agents_file_present:
        failures.append("AGENTS.md missing")

    failures.extend(
        f"missing important documentation: {path}"
        for path in documentation.missing_important_documentation_paths
    )
    failures.extend(
        f"empty Markdown file: {path}" for path in documentation.empty_markdown_files
    )
    failures.extend(
        f"placeholder Markdown file: {path}"
        for path in documentation.placeholder_markdown_files
    )
    failures.extend(
        f"domain import violation: {violation}"
        for violation in architecture.domain_import_violations
    )
    failures.extend(
        f"application import violation: {violation}"
        for violation in architecture.application_import_violations
    )
    failures.extend(
        f"Python parse error: {parse_error}"
        for parse_error in architecture.parse_errors
    )

    return tuple(failures)


def render_quality_gate_report(report: ProjectAnalysisReport) -> str:
    failures = collect_quality_gate_failures(report)

    if not failures:
        return "Quality gate: passed"

    lines = [
        "Quality gate: failed",
        "",
        "Critical findings:",
    ]
    lines.extend(f"- {failure}" for failure in failures)

    return "\n".join(lines)


def report_to_dict(report: ProjectAnalysisReport) -> dict[str, object]:
    return {
        "root": str(report.root),
        "file_counts": {
            "total_files": report.total_files,
            "python_files": report.python_files,
            "markdown_files": report.markdown_files,
            "source_files": report.source_files,
            "test_files": report.test_files,
            "documentation_files": report.documentation_files,
            "script_files": report.script_files,
            "tool_files": report.tool_files,
        },
        "important_paths": {
            "present": list(report.present_important_paths),
            "missing": list(report.missing_important_paths),
        },
        "documentation": _documentation_report_to_dict(report.documentation),
        "architecture": _architecture_report_to_dict(report.architecture),
        "trading_safety": _trading_safety_report_to_dict(report.trading_safety),
        "import_map": _import_map_report_to_dict(report.import_map),
        "test_structure": _test_structure_report_to_dict(report.test_structure),
        "configuration_safety": _configuration_safety_report_to_dict(
            report.configuration_safety
        ),
        "runtime_entrypoints": _runtime_entrypoint_report_to_dict(
            report.runtime_entrypoints
        ),
        "dependency_packaging": _dependency_packaging_report_to_dict(
            report.dependency_packaging
        ),
        "persistence_state": _persistence_state_report_to_dict(
            report.persistence_state
        ),
        "observability_logging": _observability_logging_report_to_dict(
            report.observability_logging
        ),
        "external_interfaces": _external_interface_report_to_dict(
            report.external_interfaces
        ),
        "cicd_workflows": _cicd_workflow_report_to_dict(report.cicd_workflows),
        "time_schedule": _time_schedule_report_to_dict(report.time_schedule),
        "risk_strategy_decisions": _risk_strategy_decision_report_to_dict(
            report.risk_strategy_decisions
        ),
        "cockpit_ui_surfaces": _cockpit_ui_surface_report_to_dict(
            report.cockpit_ui_surfaces
        ),
        "data_artifacts": _data_artifact_report_to_dict(report.data_artifacts),
        "release_versions": _release_version_report_to_dict(report.release_versions),
        "security_secrets": _security_secrets_report_to_dict(report.security_secrets),
        "operations_runbooks": _operations_runbook_report_to_dict(
            report.operations_runbooks
        ),
        "quality_gate": {
            "passed": not collect_quality_gate_failures(report),
            "critical_failures": list(collect_quality_gate_failures(report)),
            "trading_safety_hotspots_are_report_only": True,
        },
        "safety": {
            "mode": "read-only",
            "file_writes": "disabled",
            "broker_access": "disabled",
            "trading_access": "disabled",
            "live_access": "disabled",
        },
    }


def render_json_report(report: ProjectAnalysisReport) -> str:
    return json.dumps(report_to_dict(report), indent=2, sort_keys=True)


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

    parser.add_argument(
        "--json",
        action="store_true",
        help="Render machine-readable JSON instead of the text report.",
    )

    parser.add_argument(
        "--fail-on-critical",
        action="store_true",
        help="Exit with status code 1 when critical quality findings exist.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = analyze_project(Path(args.project_root))

    if args.json:
        print(render_json_report(report))
    else:
        print(render_report(report))

    if args.fail_on_critical:
        failures = collect_quality_gate_failures(report)

        if failures:
            if not args.json:
                print()
                print(render_quality_gate_report(report))

            raise SystemExit(1)


if __name__ == "__main__":
    main()
