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
* right quick-info area with an explicit session-local Watchlist
* native Project Analysis Dashboard widget as the Dashboard page
* read-only Market workspace backed by an immutable Application-owned snapshot
* vertically scrollable, refreshable, filterable and sortable read-only Scanner workspace backed by validated Application-owned results
* explicit Scanner-to-Watchlist add workflow with ordered duplicate prevention
* shared session-local instrument context from Scanner or Watchlist selection to the read-only Analysis workspace
* read-only Analysis price chart backed by strictly validated local OHLCV JSON data
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
visually distinct, while a missing value in either snapshot remains `NO DATA`. A
bounded in-memory table keeps the newest 20 distinct successful `READY` snapshots for
the current cockpit session. It displays UTC observation time, metrics and exact deltas;
unchanged reloads, `NO DATA`, unavailable results and failed refreshes do not add rows. The
workspace also derives snapshot age from the UTC observation timestamp and updates it
once per second without reloading the source. Freshness is shown as `FRESH`, `AGING` or
`STALE` using explicit thresholds. Defaults are 60 seconds for the end of `FRESH` and
300 seconds for the start of `STALE`; both can be overridden with startup arguments. If
a later refresh becomes unavailable, the last successful snapshot remains visible but
is marked `STALE`; it is never presented as current data. Missing values are never
estimated, replaced with zero or silently reused.

The Scanner page is the second dedicated read-only product slice. It consumes an
immutable Application-owned `ScannerResults` result set through an Application port.
Without explicit configuration it remains `UNAVAILABLE`. A local JSON result file can be
selected only with `--scanner-results-json <path>`. Infrastructure validates the exact
state-specific schema, uppercase symbols, decimal-string scores from 0 through 100 and
UTC observation timestamps before the presentation receives any row. The workspace shows
state, source, result count and a non-editable table with Symbol, Signal, Score and UTC
time. A manual refresh is available only for an explicitly configured source; recurring
refresh can be enabled with `--scanner-results-refresh-seconds <5-3600>`. Successful
reloads distinguish `UPDATED` from `UNCHANGED`. If a later reload fails, the last
successful result set remains visible but is marked `STALE`. Missing, malformed or invalid
files remain explicit `UNAVAILABLE` outcomes when no prior result set exists; no scanner
candidates are inferred or generated by the UI. Selecting a visible result opens a read-only
detail panel with Symbol, Signal, Score, UTC observation time, data source and change
classification; with no row selected, every detail field explicitly shows `NO SELECTION`.
Rows are classified as `NEW`, `CHANGED` or `UNCHANGED` against the immediately prior
successful `READY` result set. Failed refreshes never replace that comparison basis. A
bounded in-memory history stores the newest 20 successful observations per Symbol for the
current cockpit session. Selecting a row shows its UTC observation time, Signal, exact
Score and comparison state; non-`READY` and failed refresh outcomes add no history entry.
The selected Symbol history or the complete current session can be exported explicitly as
CSV with Symbol, Observed UTC, Signal, Score and Change columns. Export requires a user-
selected file path, reports success, cancellation or errors in the workspace and never
changes the source results or enables automatic persistence.

Selecting a visible Scanner result publishes an immutable session-local instrument
context with state `SELECTED`, the uppercase Symbol and source `Scanner`. The dedicated
read-only Analysis workspace follows that Application-owned context and displays the
active Symbol, context source and explicit state. With no valid Scanner selection it
shows `NO SELECTION`; filtering, sorting or refreshing the Scanner cannot leave a hidden
stale selection. Workspace navigation preserves the active context without triggering
automatic navigation.

Historical OHLCV data can be enabled only through
`--price-history-json <path>`. The Analysis workspace then loads the selected Symbol from
the strictly validated local file and displays price candles plus volume. It exposes
`NO SELECTION`, `LOADING`, `READY`, `NO DATA`, `UNAVAILABLE` and `ERROR` states, a fixed
source-defined timeframe, source metadata, UTC period and bar count. Manual Refresh
reloads only the current selected Symbol. Missing Symbols never reuse another series and
invalid payloads never reach the chart. The included
`resources/examples/price-history.json` file is synthetic manual-test data and is loaded
only when selected explicitly. The context and price history are not persisted and do
not connect to a broker or perform order, trading or LIVE actions.

Persistent Trading Candidate intake can be enabled only through
`--trading-candidates-db <path>`. Scanner- or Watchlist-originated Symbols can then be
added explicitly from Analysis to the Decision Center with initial status `NEW`. The
SQLite-backed list stores a canonical candidate UUID, Symbol, origin and UTC creation and
update timestamps. A duplicate Symbol returns `ALREADY EXISTS` without replacing the
stored origin or timestamps. Selecting a Decision Center row publishes the shared
instrument context with source `Decision Center`. Without the explicit option, no
candidate database is created and the Decision Center remains `UNAVAILABLE`. This slice
does not create Trading Decisions, prepare orders, connect to a broker or perform trading
or LIVE actions.

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

Start with explicitly configured local scanner results:

```bash
trading-cockpit --scanner-results-json temp/scanner-results.json
```

Start Scanner and Analysis with the explicit synthetic OHLCV example:

```bash
trading-cockpit --scanner-results-json temp/scanner-results.json --price-history-json resources/examples/price-history.json
```

Start Scanner, Analysis and persistent Trading Candidate intake with explicit local
sources:

```bash
trading-cockpit --scanner-results-json temp/scanner-results.json --price-history-json resources/examples/price-history.json --trading-candidates-db temp/trading-candidates.db
```

The database parent directory must already exist. No candidate database path is inferred.

Start with a recurring 30-second Scanner refresh:

```bash
trading-cockpit --scanner-results-json temp/scanner-results.json --scanner-results-refresh-seconds 30
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
