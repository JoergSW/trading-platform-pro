# Trading Platform Pro

> Enterprise-grade modular trading platform for building professional trading applications.

Trading Platform Pro provides a scalable software platform for developing, operating and evolving modern trading solutions.

The first application built on the platform is the **Trading Cockpit**, an integrated workspace for market analysis, decision support, portfolio management, trade execution and risk monitoring.

---

# Overview

Trading Platform Pro follows modern software engineering principles including:

* Clean Architecture
* Domain-Driven Design (DDD)
* Event-Driven Architecture
* SOLID Principles
* Dependency Injection
* Automated Testing
* Comprehensive Documentation

For a complete project description see:

* `docs/product/Project_Overview.md`

---

# Trading Cockpit

The Trading Cockpit is the primary application of the Trading Platform.

It combines the complete trading workflow within a single workspace:

* Market Monitoring
* Decision Center
* Watchlists
* Portfolio Management
* Position Monitoring
* Order Management
* Risk Management
* Reporting & Analytics
* Workspace Management
* Command Palette

## Current Desktop Application

The current Trading Cockpit is a native **PySide6 desktop application**.

Implemented foundation:

* visible startup status dialog
* top application status strip
* left application navigation
* central workspace with one dedicated page per navigation item
* right quick-info area
* native Project Analysis Dashboard widget as the Dashboard page
* read-only Market workspace backed by an immutable Application-owned snapshot
* automatic read-only Project Analysis report generation at startup
* manual reload of the generated Project Analysis Agent JSON report

Start the desktop application with:

```bash
trading-cockpit
```

The startup dialog immediately exposes the active startup phase: application
startup, Project Analysis report generation and dashboard loading. Report generation
runs outside the GUI thread so the dialog remains responsive. It closes when the
main cockpit window is ready.

If report generation fails, the startup dialog remains visible and exposes two
explicit recovery actions. **Retry** repeats report generation. **Continue** opens
the cockpit with the Project Analysis Dashboard in an explicit `ERROR` state.

At startup, the reusable Project Analysis Report application service coordinates
the read-only Project Analysis Agent adapter and writes the generated JSON report to:

```text
temp/project-analysis-agent-report.json
```

The dashboard then loads that generated report automatically. Its Refresh action
reloads the existing report only; it does not execute project analysis, modify
project source files, connect to a broker or enable trading. Navigation routes to
distinct workspace pages so later product slices can be added without embedding
page construction and switching logic in the main window. The Market page is the
first dedicated product slice. It renders an immutable, provider-independent
`MarketSnapshot` loaded through an Application port. The default composition uses a
safe infrastructure adapter that returns `UNAVAILABLE` until a market-data source is
configured. A local read-only JSON snapshot can be selected explicitly with
`--market-snapshot-json <path>`. The JSON file is validated strictly and is never loaded
implicitly. The Market workspace can reload the configured file with its manual Refresh
action. An optional interval can be enabled explicitly with
`--market-snapshot-refresh-seconds <5-3600>`. While a refresh is pending the action is
disabled and a visible loading state is shown. A successful reload reports `UPDATED`
only when state, market status, source or observation timestamp changed; otherwise it reports
`UNCHANGED`. A `READY` snapshot may also contain optional decimal metrics for SPX and
VIX index points plus ATM Straddle percent. Each metric has an explicit unit and missing
metrics are rendered as `NO DATA`; values are never inferred or replaced with zero. After
another successful `READY` snapshot is loaded, the workspace shows the exact change from
the immediately preceding successful snapshot. Positive, negative and unchanged deltas are
visually distinct, while a missing value in either snapshot remains `NO DATA`. The
workspace also derives snapshot age from the UTC observation timestamp and updates it
once per second without reloading the source. Freshness is shown as `FRESH`, `AGING` or
`STALE` using explicit thresholds. Defaults are 60 seconds for the end of `FRESH` and
300 seconds for the start of `STALE`; both can be overridden with startup arguments. If
a later refresh becomes unavailable, the last successful snapshot remains visible but
is marked `STALE`; it is never presented as current data. Missing values are never
estimated, replaced with zero or silently reused.

The current application is not a browser application. A future web presentation
may be added through a separate web API and frontend. Domain and Application code
must therefore remain independent from PySide6 and other presentation frameworks.

---

# Repository Structure

```
config/         Runtime profiles and configuration
docs/           Project documentation
logs/           Runtime logs
resources/      Static resources
scripts/        Utility scripts
src/            Source code
tests/          Test suites
tools/          Development tools
```

---

# Documentation

Project documentation is organized by domain.

| Area                   | Location               |
| ---------------------- | ---------------------- |
| Product                | `docs/product/`        |
| Architecture           | `docs/architecture/`   |
| API                    | `docs/api/`            |
| Specifications         | `docs/specifications/` |
| UI                     | `docs/ui/`             |
| Operations             | `docs/operations/`     |
| Developer              | `docs/developer/`      |
| Architecture Decisions | `docs/decisions/`      |

Key documents:

* Project Overview
* Product Vision
* Software Architecture Document (SAD)
* Trading Cockpit Specification (TCS)
* API Specification
* Widget Catalog
* Operations Manual

---

# Technology Stack

* Python 3.13
* PySide6
* Clean Architecture
* Domain-Driven Design
* Dependency Injection
* Event-Driven Architecture
* Pytest
* Ruff
* GitHub Actions
* YAML Configuration

---

# Quick Start

Create and activate a Python 3.13 virtual environment, then install the project
including development dependencies:

```bash
python -m pip install -e ".[dev]"
```

Start the desktop application. The read-only Project Analysis report is generated
and loaded automatically during startup:

```bash
trading-cockpit
```

Start with an explicitly configured local JSON market snapshot:

```bash
trading-cockpit --market-snapshot-json temp/market-snapshot.json
```

Start with an explicit 30-second read-only refresh interval:

```bash
trading-cockpit --market-snapshot-json temp/market-snapshot.json --market-snapshot-refresh-seconds 30
```

Start with custom snapshot freshness thresholds:

```bash
trading-cockpit --market-snapshot-json temp/market-snapshot.json --market-snapshot-fresh-seconds 45 --market-snapshot-stale-seconds 180
```

Run tests:

```bash
python -m pytest -p no:cov -q
```

Run linting and formatting verification:

```bash
python -m ruff check .
python -m ruff format --check .
```

---

# Development Workflow

Every implementation follows the same workflow:

1. Analyze
2. Design
3. Implement
4. Test
5. Review
6. Commit
7. Push

Development rules are documented in:

* `AGENTS.md`
* `docs/developer/`

---

# Trading Safety

General principles:

* Prefer PAPER over LIVE during development.
* Validate every architectural change.
* Preserve deterministic behaviour.
* Keep documentation synchronized with implementation.
* Never introduce breaking changes without documentation and review.

---

# Contributing

Every contribution should:

* Follow `AGENTS.md`.
* Preserve the established architecture.
* Keep documentation up to date.
* Include tests where appropriate.
* Maintain backward compatibility whenever possible.

---

# License

Internal project.
