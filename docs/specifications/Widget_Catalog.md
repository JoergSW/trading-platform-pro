# Widget Catalog

Version: 1.0

---

# Purpose

This document defines the standard widgets of the Trading Cockpit.

Widgets are reusable presentation components that support defined trading workflows within configurable workspaces.

The catalog defines:

- widget responsibility
- workflow role
- roadmap phase
- shared instrument context behaviour
- core functional expectations

Widgets shall not be introduced as isolated UI features without a defined product workflow.

---

# Widget Architecture Principles

Every widget shall:

- have one primary responsibility
- expose explicit dependencies
- remain independently testable where practical
- support application theming
- support docking and resizing
- support workspace state persistence where applicable
- provide visible loading states
- provide visible error states
- avoid direct infrastructure access
- avoid domain business rules

Widgets shall interact through application services, presentation adapters and explicit context mechanisms.

---

# Shared Instrument Context

Compatible widgets may participate in the shared instrument context.

A widget may:

- publish instrument context
- follow instrument context
- publish and follow instrument context
- remain context-independent

Context propagation shall be explicit.

A widget that follows shared context shall clearly reflect the currently selected instrument.

Examples:

- Watchlist → Price Chart
- Market Scanner → Price Chart
- Market Scanner → Decision Center
- Positions → Price Chart
- Decision Center → Order Entry

---

# Widget Lifecycle

Widgets shall support a controlled lifecycle where applicable:

1. Create
2. Initialize
3. Load state
4. Enter active state
5. Receive updates
6. Persist state
7. Dispose

Widgets shall release subscriptions and resources during disposal.

Widget lifecycle failures shall not silently destabilize the complete workspace.

---

# Phase 2 – Trading Cockpit Shell

## Project Analysis Dashboard

**Category:** Workspace / Diagnostics
**Roadmap Phase:** 1 / 2
**Status:** Implemented
**Context:** Context-independent

Responsibility:

Provide a read-only view of project quality and safety information inside the
native Trading Cockpit.

Current capabilities:

- display Project Analysis quality-gate state
- display file counts
- display read-only safety state
- display important analysis hotspots
- expose `AVAILABLE`, `UNAVAILABLE` and `ERROR` states
- show the configured source path and last successful load time
- load the generated report automatically during cockpit startup
- manually reload the configured report

Default data source:

```text
temp/project-analysis-agent-report.json
```

The widget consumes the existing Project Analysis Agent JSON contract.

During cockpit startup, the Project Analysis Report application service shall:

- coordinate generation independently from the desktop UI
- use the read-only Project Analysis Agent infrastructure adapter
- generate the JSON report under `temp/`
- validate the generated JSON before it becomes the dashboard data source
- expose generation failures as explicit dashboard error state
- remain reusable by future presentation clients such as a web API
- avoid broker, trading and LIVE access

The Refresh action shall:

- reload the configured JSON file
- update visible dashboard state
- preserve read-only behaviour

The Refresh action shall not:

- execute the Project Analysis Agent
- write or repair project files
- connect to a broker
- submit, modify or cancel orders
- activate PAPER or LIVE trading

This widget is a diagnostics capability and does not participate in shared
instrument context.

---

## Market Overview

**Category:** Market
**Roadmap Phase:** 2 / 3
**Context:** Context-independent

Responsibility:

Provide a compact overview of the current market state.

Initial capabilities:

- market status
- major market indicators
- data availability state
- data freshness state

Current implementation:

- read-only Market workspace
- immutable Application-owned `MarketSnapshot` input
- provider-independent snapshot loading through an Application port
- safe `UNAVAILABLE` infrastructure adapter until a source is configured
- optional read-only JSON adapter selected only by explicit startup argument
- strict state-specific JSON validation and UTC timestamp validation
- explicit `UNAVAILABLE` diagnostic state for missing or invalid configured files
- explicit market status card
- explicit data source card
- explicit last-update card
- optional SPX and VIX index-point cards using exact decimal values
- optional ATM Straddle percentage card using exact decimal values
- explicit `NO DATA` rendering for every missing metric
- explicit snapshot-age card updated once per second
- explicit data-freshness card with `FRESH`, `AGING` and `STALE` states
- configurable ordered freshness thresholds with safe defaults of 60 and 300 seconds
- manual read-only Refresh for an explicitly configured source
- visible `REFRESHING`, `UPDATED`, `UNCHANGED`, `ERROR` and `UNAVAILABLE` refresh feedback
- `UPDATED` only when state, market status, source, observation timestamp or metrics changed
- optional explicit auto-refresh interval from 5 through 3600 seconds
- duplicate refresh suppression while one attempt is pending
- `STALE` presentation when a later unavailable refresh retains the last successful snapshot
- `UNAVAILABLE` when no source is configured
- `NO DATA` when a configured source has not supplied a market state

Placeholder, estimated or silently reused market values are not allowed. Retained values
shall be marked `STALE` and keep their original observation timestamp. Broker,
order, trading and LIVE capabilities are outside this implementation.

---

## Watchlist

**Category:** Market
**Roadmap Phase:** 2 / 3
**Context:** Publish instrument context

Responsibility:

Maintain and display user-defined instrument lists.

Capabilities:

- display instruments
- select instrument
- add instrument
- remove instrument
- reorder instruments
- persist watchlist state
- display quote state where available

Selecting an instrument shall publish shared instrument context.

---

## Portfolio Overview

**Category:** Portfolio
**Roadmap Phase:** 2 / 5
**Context:** Context-independent

Responsibility:

Provide a compact overview of the current portfolio state.

Capabilities may include:

- account context
- portfolio value
- cash information
- unrealized P&L
- realized P&L
- broker state
- data timestamp

Unavailable financial values shall remain explicitly unavailable.

---

## Risk Overview

**Category:** Risk
**Roadmap Phase:** 2 / 5
**Context:** Context-independent

Responsibility:

Provide a compact overview of available portfolio risk information.

Capabilities may include:

- exposure
- concentration
- margin information
- risk availability state
- risk data timestamp

The widget shall not silently estimate unavailable risk values.

---

## Notifications

**Category:** Workspace
**Roadmap Phase:** 2
**Context:** Context-independent

Responsibility:

Display operational and user-relevant notifications.

Notification types may include:

- information
- warning
- error
- critical

Notifications shall communicate operational impact clearly.

---

## Command Palette

**Category:** Workspace
**Roadmap Phase:** 2
**Context:** Context-independent

Responsibility:

Provide keyboard-driven access to application commands.

Capabilities:

- command search
- command execution
- keyboard navigation
- context-aware command availability

Commands shall use the application command infrastructure.

---

# Phase 3 – Market Observation Workflow

## Price Chart

**Category:** Charts
**Roadmap Phase:** 3
**Context:** Follow instrument context

Responsibility:

Display price history for the active instrument.

Capabilities:

- price visualization
- volume visualization
- timeframe selection
- data loading state
- stale data indication
- active instrument display

Future capabilities may include:

- indicators
- drawing tools
- multi-timeframe views

---

## Market Status

**Category:** Market
**Roadmap Phase:** 3
**Context:** Context-independent

Responsibility:

Display market and market-data operational state.

Capabilities:

- market session state
- market data connection state
- last update timestamp
- freshness state

---

## Instrument Details

**Category:** Market
**Roadmap Phase:** 3
**Context:** Follow instrument context

Responsibility:

Display core information for the active instrument.

Capabilities may include:

- symbol
- instrument name
- instrument type
- exchange
- currency
- market state

---

# Phase 4 – Trading Candidate Workflow

## Market Scanner

**Category:** Market
**Roadmap Phase:** 4
**Context:** Publish instrument context

Responsibility:

Display reproducible scanner results and support candidate discovery.

Capabilities:

- scanner selection
- result display
- filtering
- sorting
- instrument selection
- result timestamp
- scanner state

Selecting a result shall publish instrument context.

---

## Trading Candidates

**Category:** Decision Center
**Roadmap Phase:** 4
**Context:** Publish and follow instrument context

Responsibility:

Maintain instruments currently under trading evaluation.

Capabilities:

- candidate list
- candidate status
- tags
- notes indicator
- creation timestamp
- last update timestamp

Candidate state shall be persistent.

---

## Candidate Context

**Category:** Decision Center
**Roadmap Phase:** 4
**Context:** Follow instrument context

Responsibility:

Provide consolidated context for the active trading candidate.

Capabilities may include:

- instrument information
- market context
- scanner origin
- watchlist membership
- candidate state

---

# Phase 5 – Portfolio and Risk Context

## Positions

**Category:** Portfolio
**Roadmap Phase:** 5
**Context:** Publish instrument context

Responsibility:

Display current portfolio positions.

Capabilities:

- instrument
- quantity
- average price where available
- current value where available
- unrealized P&L where available
- data timestamp
- source state

Selecting a position shall publish instrument context.

---

## Position Details

**Category:** Portfolio
**Roadmap Phase:** 5
**Context:** Follow instrument context

Responsibility:

Display detailed information for the selected portfolio position.

The widget shall distinguish between local and broker-derived state where relevant.

---

## Exposure

**Category:** Risk
**Roadmap Phase:** 5
**Context:** Context-independent

Responsibility:

Display available portfolio exposure information.

Capabilities may include:

- gross exposure
- net exposure
- instrument exposure
- sector exposure
- concentration

Unavailable values shall remain explicitly unavailable.

---

## Margin

**Category:** Risk
**Roadmap Phase:** 5
**Context:** Context-independent

Responsibility:

Display broker-provided margin information where available.

The widget shall identify the data source and timestamp.

---

## Reconciliation Status

**Category:** Portfolio
**Roadmap Phase:** 5
**Context:** Context-independent

Responsibility:

Display discrepancies between local and external broker state.

Capabilities:

- reconciliation state
- discrepancy count
- affected capability
- last reconciliation timestamp

Discrepancies shall remain visible until resolved or explicitly acknowledged.

---

# Phase 6 – Order and Position Workflow

## Order Entry

**Category:** Trading
**Roadmap Phase:** 6
**Context:** Follow instrument context

Responsibility:

Prepare and validate an order for the active instrument.

Capabilities:

- instrument
- action
- quantity
- order type
- price parameters
- validation state
- submission readiness

Order Entry shall not submit invalid orders.

Order submission requires an explicit user action.

---

## Order Review

**Category:** Trading
**Roadmap Phase:** 6
**Context:** Follow instrument context

Responsibility:

Present final order parameters before submission where required by the workflow.

Capabilities:

- order summary
- validation result
- warnings
- broker context
- submission confirmation

---

## Open Orders

**Category:** Trading
**Roadmap Phase:** 6
**Context:** Publish instrument context

Responsibility:

Display active orders and their lifecycle state.

Capabilities:

- instrument
- order action
- quantity
- order type
- order state
- broker acknowledgement state
- last update timestamp

Selecting an order may publish instrument context.

---

## Order History

**Category:** Trading
**Roadmap Phase:** 6
**Context:** Publish instrument context

Responsibility:

Display historical order lifecycle information.

Order history shall remain traceable.

---

## Execution Monitor

**Category:** Trading
**Roadmap Phase:** 6
**Context:** Publish instrument context

Responsibility:

Display execution information and broker execution feedback.

Capabilities may include:

- execution state
- filled quantity
- remaining quantity
- execution price
- broker timestamp
- rejection information

---

# Phase 7 – Integrated Decision Center

## Decision Center

**Category:** Decision Center
**Roadmap Phase:** 7
**Context:** Publish and follow instrument context

Responsibility:

Support the complete trading decision lifecycle.

Capabilities:

- active instrument
- candidate status
- market context
- portfolio context
- risk context
- notes
- tags
- signals
- strategy evaluation
- decision status

Decision state shall be persistent and reviewable.

---

## Signals

**Category:** Decision Center
**Roadmap Phase:** 7
**Context:** Follow instrument context

Responsibility:

Display available deterministic trading signals for the active instrument.

Signals shall expose:

- source
- timestamp
- state

Future AI-generated information shall remain distinguishable from deterministic signals.

---

## Strategy Evaluation

**Category:** Decision Center
**Roadmap Phase:** 7
**Context:** Follow instrument context

Responsibility:

Display available strategy evaluations for the active candidate.

Strategy evaluation shall not submit orders directly.

---

# Phase 8 – Trading Review and Analytics

## Trading Journal

**Category:** Reporting
**Roadmap Phase:** 8
**Context:** Publish instrument context

Responsibility:

Provide reviewable historical trading records.

Capabilities:

- trade history
- decision references
- notes
- tags
- outcome information

---

## Performance

**Category:** Reporting
**Roadmap Phase:** 8
**Context:** Context-independent

Responsibility:

Display reproducible trading performance information.

---

## Statistics

**Category:** Reporting
**Roadmap Phase:** 8
**Context:** Context-independent

Responsibility:

Display statistical trading information derived from recorded trading activity.

---

## Equity Curve

**Category:** Reporting
**Roadmap Phase:** 8
**Context:** Context-independent

Responsibility:

Display portfolio or trading performance over time.

The underlying data source and calculation period shall be identifiable.

---

# Future Widgets

Potential future widgets include:

- Options Chain
- Market Breadth
- Sector Performance
- Heat Map
- Economic Calendar
- Advanced Chart
- Greeks
- Strategy Builder
- Backtesting
- Plugin Widgets
- AI Assistant
- News Feed

Future widgets require:

- defined user problem
- defined trading workflow
- product roadmap alignment
- architecture review where required

---

# Widget State Requirements

Persistent widget state may include:

- size
- docking position
- visibility
- widget-specific settings
- selected view
- filter state
- sorting state

Business data shall not be stored as widget layout state.

Workspace state and business persistence shall remain separate.

---

# Widget Error States

Widgets shall explicitly represent:

- loading
- ready
- stale
- unavailable
- disconnected
- error

Widgets shall not silently display outdated information as current information.

---

# Widget Review Checklist

Before introducing or changing a widget verify:

- primary responsibility defined
- trading workflow identified
- roadmap phase identified
- shared context behaviour defined
- dependencies explicit
- loading state defined
- error state defined
- stale data behaviour defined where relevant
- persistence requirements defined
- business logic remains outside presentation
- automated tests added where practical
- documentation updated

---

# Related Documents

- Product_Vision.md
- Product_Roadmap.md
- Project_Overview.md
- Technical_Specifications.md
- Architecture.md
- Domain_Model.md
- UI_Guidelines.md
- API_Guidelines.md
- Testing_Strategy.md
- AGENTS.md
