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

Install dependencies:

```bash
pip install -r requirements.txt
```

Run tests:

```bash
pytest
```

Run linting:

```bash
ruff check .
ruff format .
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
