# AGENTS.md

# Trading Platform Pro

**Developer & AI Agent Guide**

Version: 1.0
Status: Active

---

# Purpose

This document defines mandatory engineering rules for all contributors working on this repository, including human developers and AI coding agents.

It is the operational entry point for repository work.

It complements the detailed project documentation under:

```text
docs/
```

When this document and detailed documentation appear to conflict, stop and resolve the inconsistency before implementation.

Do not guess.

---

# Product Direction

Trading Platform Pro currently develops the Trading Cockpit as its primary product.

The Trading Cockpit is a professional desktop workspace for:

- observing markets
- reviewing instruments
- evaluating trading candidates
- preparing trading decisions
- validating orders
- monitoring orders
- monitoring positions
- reviewing portfolio and risk state

Architecture and implementation decisions shall optimize for concrete Trading Cockpit requirements.

Shared platform capabilities may evolve when multiple implemented product capabilities require them.

Do not introduce generic platform infrastructure solely for hypothetical future applications.

---

# Mission

Deliver a safe, deterministic and maintainable Trading Cockpit while preserving clear architecture boundaries, operational transparency and trading workflow safety.

Every change shall:

- solve a concrete requirement
- preserve existing behaviour unless intentionally changed
- avoid unnecessary complexity
- keep documentation synchronized
- maintain PAPER and LIVE safety
- protect trading-critical workflows

---

# Core Principles

Always:

- analyze before changing
- inspect the current implementation
- understand existing callers and dependencies
- make the smallest useful change
- preserve architecture boundaries
- keep documentation synchronized
- write or update tests where required
- prefer explicit state over implicit behaviour
- prefer clarity over cleverness

Never:

- guess missing requirements
- invent files, APIs, classes or project structure
- rewrite unrelated code
- introduce hidden side effects
- duplicate existing functionality
- bypass safety checks
- treat logs as authoritative business state
- silently change trading behaviour
- silently activate LIVE mode

---

# Current Implementation Is Authoritative

Before modifying existing code, inspect the actual repository state.

Do not rely on assumptions from documentation, memory or naming conventions alone.

For every code change:

1. Read the complete target file.
2. Inspect nearby files.
3. Inspect imports and dependencies.
4. Inspect existing tests.
5. Inspect relevant documentation.
6. Identify the owning capability.
7. Identify runtime, persistence and external side effects.
8. Propose the smallest safe change.
9. Implement.
10. Test.
11. Update documentation.
12. Review diff before commit.

If required information is missing, ask before changing.

---

# Documentation Source of Truth

Markdown files under:

```text
docs/
```

are the documentation source of truth.

Generated DOCX and PDF files are derived artifacts.

Do not manually edit generated DOCX or PDF output.

When Markdown documentation changes, run:

```bash
python scripts/generate_docs.py
```

The generation command shall complete successfully before commit.

Generated DOCX and PDF files shall not be re-read for content validation.

Validate the Markdown source and generation success.

---

# Documentation Map

Primary documentation locations:

| Topic | Document |
|---|---|
| Product vision | `docs/product/Product_Vision.md` |
| Product roadmap | `docs/product/Product_Roadmap.md` |
| Project overview | `docs/product/Project_Overview.md` |
| Technical specifications | `docs/specifications/Technical_Specifications.md` |
| Widget catalog | `docs/specifications/Widget_Catalog.md` |
| Architecture | `docs/architecture/Architecture.md` |
| Domain model | `docs/architecture/Domain_Model.md` |
| Infrastructure | `docs/architecture/Infrastructure.md` |
| Project structure | `docs/architecture/Project_Structure.md` |
| API guidelines | `docs/api/API_Guidelines.md` |
| Configuration | `docs/operations/Configuration.md` |
| Runtime | `docs/operations/Runtime.md` |
| Logging | `docs/operations/Logging.md` |
| Monitoring | `docs/operations/Monitoring.md` |
| CI/CD | `docs/operations/CI_CD.md` |
| Coding standards | `docs/developer/Coding_Standards.md` |
| Development workflow | `docs/developer/Development_Guidelines.md` |
| Git workflow | `docs/developer/Git_Workflow.md` |
| Testing strategy | `docs/developer/Testing_Strategy.md` |
| AI agent guide | `docs/developer/AI_Agent_Guide.md` |
| Decision log | `docs/decisions/Decision_Log.md` |
| Technical roadmap | `docs/decisions/Roadmap.md` |
| ADR rules | `docs/adr/README.md` |
| User guide | `docs/user/User_Guide.md` |

Reference the authoritative document instead of duplicating detailed content.

---

# Architecture Rules

The project uses explicit architecture boundaries.

Architecture is defined by concrete rules, not by slogans.

Mandatory dependency direction:

```text
Domain
    ↑
Application
    ↑
Infrastructure / Presentation
```

Domain shall not depend on:

- Infrastructure
- Presentation
- broker SDKs
- SQLAlchemy
- PySide6
- provider models
- persistence models

Application shall coordinate workflows through project-owned ports.

Infrastructure shall implement technical adapters.

Presentation shall invoke Application behaviour and display Application state.

Presentation shall not own Domain business rules.

---

# Capability Ownership

Every change shall belong to a concrete capability.

Examples:

- Instruments
- Watchlists
- Market Data
- Trading Candidates
- Trading Decisions
- Orders
- Positions
- Portfolio
- Risk
- Reconciliation
- Runtime
- Configuration
- Logging
- Monitoring
- Workspace
- Widgets

Do not create cross-cutting abstractions without real consumers.

Do not introduce generic shared services before a concrete capability requires them.

---

# Domain Rules

Domain code shall own business concepts and invariants.

Domain code may include:

- Entities
- Value Objects
- Domain Services
- Domain Events
- Domain Exceptions

Domain code shall use project-owned types.

Domain code shall not use provider-specific models.

Financial values shall preserve:

- precision
- currency where relevant
- sign
- unavailable state
- zero as a real value only when zero is known

Do not treat unavailable financial data as zero.

---

# Application Rules

Application code owns use cases and workflow coordination.

Application workflows shall make side effects explicit.

Application code may:

- validate commands
- coordinate Domain behaviour
- call ports
- manage workflow state
- persist business state
- publish project events
- translate technical failures into application outcomes

Application code shall not hide trading side effects behind generic helper calls.

---

# Infrastructure Rules

Infrastructure code owns external and technical integration.

Examples:

- broker adapters
- market data adapters
- persistence implementations
- file system access
- configuration loading
- logging setup
- monitoring adapters

Infrastructure shall translate external models into project-owned models.

Provider payloads shall not leak into Domain.

Infrastructure shall not own trading decisions.

---

# Presentation Rules

Presentation code owns user interaction and rendering.

Presentation may:

- display Application state
- invoke Application commands
- show operational state
- preserve UI state
- present validation feedback

Presentation shall not:

- implement trading rules
- directly use broker adapters
- infer business state from UI state
- silently submit trading actions
- silently repair business state

---

# Trading Safety

Trading safety has priority over convenience.

The following areas are trading-critical:

- trading decisions
- order creation
- order validation
- order submission
- order cancellation
- broker acknowledgement
- execution processing
- position lifecycle
- portfolio state
- risk management
- reconciliation
- PAPER and LIVE environment selection

Changes in trading-critical areas require explicit review and appropriate regression coverage.

Do not modify trading-critical behaviour without clear approval.

---

# PAPER and LIVE Rules

PAPER and LIVE must remain explicitly separated.

Mandatory rules:

- PAPER shall not silently use LIVE configuration.
- LIVE shall never be activated by fallback.
- LIVE requires explicit selection.
- invalid LIVE configuration shall fail validation.
- automated tests shall not execute LIVE orders.
- CI shall not require LIVE trading.
- user-facing state shall make the active environment visible where operationally relevant.

Do not introduce convenience shortcuts that weaken PAPER/LIVE separation.

---

# Order Workflow Rules

Order workflows are external side-effect workflows.

A local method return is not the same as broker acknowledgement.

The order lifecycle shall preserve relevant distinctions, for example:

```text
Submission Requested
        ↓
Validated
        ↓
Transmitted
        ↓
Acknowledged or Rejected
        ↓
Partially Filled or Filled
```

Rules:

- do not collapse lifecycle states into one generic submitted state
- do not infer broker acknowledgement from adapter success
- do not infer fills from UI state
- do not resubmit on unknown external state
- do not implement automatic order retry unless explicitly approved by the owning workflow
- persist authoritative business state where required
- handle repeated broker messages deterministically

---

# Duplicate Submission Protection

Duplicate order submission risk must be considered for every order-related change.

Evaluate:

- stable order identity
- stable submission identity
- repeated application callback
- repeated broker message
- timeout
- disconnect
- reconnect
- application restart
- recovery

Unknown external order state shall not automatically result in repeated submission.

Required duplicate-submission regression tests must block integration when failing.

---

# Reconciliation Rules

Reconciliation compares local state with broker-derived state.

Reconciliation observation is not repair.

Separate:

```text
Observe
    ↓
Compare
    ↓
Classify
    ↓
Expose Action Required
    ↓
Repair only through explicit workflow
```

Monitoring and logging shall never repair business state.

Do not silently rewrite business history.

Repair workflows require explicit authorization, tests and documentation.

---

# Runtime and Async Rules

Runtime behaviour shall be explicit and deterministic.

Long-running tasks require ownership.

Async code shall handle:

- cancellation
- timeout
- task failure
- task cleanup
- shutdown
- event loop responsiveness

Avoid unmanaged fire-and-forget tasks.

Do not block the UI thread with external integrations.

Do not use arbitrary sleeps to hide timing problems.

Use deterministic synchronization where practical.

---

# Logging Rules

Logging shall support diagnosis, auditability and operational review.

Logs shall be structured where practical.

Logs shall not become authoritative business state.

Trading-critical workflows require persisted or Application-owned state where business state matters.

Logs shall not contain:

- credentials
- secrets
- unnecessary account details
- unsanitized provider payload dumps
- sensitive personal information

---

# Monitoring Rules

Monitoring is observational.

Monitoring may detect:

- degraded state
- failed background task
- broker disconnect
- market data failure
- stale data
- reconciliation discrepancy
- runtime health issue

Monitoring shall not:

- submit orders
- cancel orders
- repair positions
- mutate Domain state
- override Application workflows

---

# Coding Rules

Mandatory:

- Python 3.13
- full type hints where practical
- UTF-8
- meaningful naming
- small focused functions
- small focused classes
- explicit errors
- deterministic behaviour
- Ruff-compliant formatting and linting

Required checks:

```bash
ruff check .
ruff format --check .
```

Avoid:

- dead code
- duplicated logic
- wildcard imports
- speculative abstractions
- hidden global state
- ambiguous names
- broad exception swallowing
- provider models in Domain
- UI types in Domain
- persistence models in Domain

---

# Testing Rules

Every implementation shall be verified according to risk.

Relevant test categories:

```text
Unit Tests
    ↓
Integration Tests
    ↓
Trading Workflow Regression Tests
    ↓
Runtime and System Tests
    ↓
Explicit PAPER Validation
```

Trading-critical changes require stronger regression protection than presentation-only changes.

Tests shall be:

- deterministic
- isolated where appropriate
- explicit
- readable
- maintainable
- risk-oriented

Tests shall not depend on:

- uncontrolled wall-clock time
- LIVE broker services
- current market state
- developer-local configuration
- random data
- timing luck

---

# Required Trading Tests

Where implemented, tests shall cover relevant scenarios for:

- order lifecycle
- order validation
- broker acknowledgement
- broker rejection
- duplicate submission prevention
- timeout
- disconnect
- reconnect
- partial fill
- repeated provider messages
- cancellation
- position lifecycle
- reconciliation
- PAPER and LIVE separation

Automatic order submission retry requires explicit tests and explicit approval.

---

# Test Doubles

Use controlled test doubles for boundaries.

Allowed patterns include:

- fake repositories
- fake broker ports
- fake market data ports
- fake clocks
- fake event dispatchers
- controlled runtime services

Do not mock away the business rule being tested.

If testing duplicate submission prevention, exercise the actual duplicate prevention rule.

Fake or mock the broker boundary instead.

---

# Git Workflow

Normal development uses dedicated branches.

Direct commits to `main` are not part of the normal workflow.

Before commit:

1. Review the diff.
2. Run focused tests.
3. Run required quality checks.
4. Run documentation generation when Markdown changed.
5. Verify no unrelated files are included.
6. Verify no secrets are included.

Code and documentation should be committed together when they describe the same coherent change.

---

# Project Analysis Agent

The repository includes a read-only Project Analysis Agent:

```bash
python tools/project_analysis_agent.py .
```

Machine-readable output:

```bash
python tools/project_analysis_agent.py . --json
```

Critical quality gate:

```bash
python tools/project_analysis_agent.py . --fail-on-critical
```

The agent checks:

- project structure
- important documentation paths
- empty Markdown files
- placeholder Markdown files
- architecture import boundaries
- Python parse errors
- trading safety hotspots

Critical findings block CI.

Trading safety hotspots are report-only and require review.

The agent shall remain:

- read-only
- non-trading
- broker-disconnected
- LIVE-disabled

---

# Development Workflow

Every task follows:

1. Analyze.
2. Identify owning capability.
3. Identify affected layers.
4. Identify side effects.
5. Identify tests.
6. Design the smallest safe change.
7. Implement.
8. Run focused validation.
9. Update documentation.
10. Review diff.
11. Commit.
12. Push.

For trading-critical changes, explicitly evaluate:

- external side effects
- duplicate submission risk
- retry behaviour
- broker acknowledgement semantics
- disconnect and reconnect behaviour
- persistence impact
- reconciliation impact
- PAPER/LIVE impact

---

# AI Agent Rules

AI agents shall:

- inspect before changing
- preserve architecture boundaries
- minimize modifications
- avoid assumptions
- ask when information is missing
- provide exact file paths
- provide exact replacement locations
- avoid generic patches when exact changes are required
- keep documentation synchronized
- identify trading-critical impact
- identify required tests
- avoid invented repository details

AI agents shall not:

- invent project files
- invent interfaces
- invent configuration keys
- invent commands
- invent test results
- claim a directory is complete without checking
- skip safety analysis for order workflows
- silently change LIVE behaviour

---

# Communication Rules

Technical communication should be:

- concise
- factual
- actionable
- specific to the current repository state

When giving implementation guidance, provide:

- exact file path
- exact search location
- exact replacement or insertion
- required tests
- required documentation updates

Avoid:

- speculation
- unnecessary explanations
- broad alternatives when a direct change is needed
- unsupported claims
- hidden assumptions

---

# Definition of Done

A task is complete only when:

- implementation is finished
- relevant tests pass
- required regression tests pass
- source quality checks pass
- documentation is updated
- documentation generation passes when Markdown changed
- architecture boundaries are preserved
- trading safety impact is reviewed
- diff is reviewed
- change is committed
- change is pushed

For trading-critical tasks, also verify where relevant:

- duplicate submission protection
- broker acknowledgement semantics
- timeout behaviour
- disconnect behaviour
- reconnect behaviour
- reconciliation impact
- PAPER validation requirement
- LIVE safety

---

# Stop Conditions

Stop and ask before continuing when:

- required files are missing
- current implementation contradicts the requested change
- public API or workflow ownership is unclear
- order side effects are unclear
- LIVE impact is unclear
- duplicate submission risk is unresolved
- reconciliation impact is unresolved
- tests cannot be identified
- documentation would become inconsistent
- a requested change requires inventing repository details

Do not continue by guessing.

---

# Long-Term Direction

Trading Platform Pro shall evolve through concrete Trading Cockpit capabilities.

The long-term direction is a safe, maintainable and extensible trading system whose shared capabilities emerge from real product requirements.

Future applications, public APIs, plugin systems or cloud capabilities may be considered only when concrete requirements and real consumers exist.

The project shall not optimize for hypothetical platform extensibility at the expense of current Trading Cockpit safety, clarity and delivery.
