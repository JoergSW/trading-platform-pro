# User Guide

Version: 1.0

---

# Purpose

This guide explains how users work with Trading Platform Pro and its primary application, the Trading Cockpit.

The Trading Cockpit is a professional desktop workspace for observing markets, reviewing trading opportunities, preparing decisions, monitoring orders and tracking portfolio state.

This guide focuses on user-facing behaviour.

It does not describe internal architecture, source code or implementation details.

---

# Target Audience

This guide is intended for:

- traders
- portfolio users
- operators
- testers
- reviewers
- support users

The guide assumes that users understand basic trading concepts such as:

- instruments
- quotes
- orders
- positions
- portfolio value
- risk
- broker connectivity

---

# Product Overview

The Trading Cockpit helps users move through the trading workflow:

```text
Observe Market
        ↓
Select Instrument
        ↓
Evaluate Candidate
        ↓
Review Portfolio and Risk
        ↓
Make Decision
        ↓
Prepare Order
        ↓
Submit or Cancel
        ↓
Monitor Order
        ↓
Monitor Position
        ↓
Review Outcome
```

The application is designed to keep relevant information visible and to reduce unnecessary context switching.

---

# Important Safety Notice

Trading workflows may affect external broker state.

Users are responsible for reviewing all trading actions before submission.

The application shall make operational state visible, but it does not remove the need for user review.

Pay special attention to:

- selected environment
- selected account
- instrument
- order side
- quantity
- order type
- price parameters
- current market data state
- broker connection state
- portfolio and risk context

---

# PAPER and LIVE Modes

The application distinguishes between PAPER and LIVE operation.

PAPER mode is intended for testing, validation and practice.

LIVE mode may affect real broker accounts and real capital.

The active environment shall be visible in the application where operationally relevant.

---

# PAPER Mode

Use PAPER mode for:

- workflow validation
- broker connectivity testing
- order workflow testing
- training
- operational dry runs
- regression validation with external broker boundaries

PAPER mode may behave differently from LIVE trading due to broker simulation, market conditions or account configuration.

PAPER validation is not a replacement for careful review before LIVE operation.

---

# LIVE Mode

LIVE mode requires explicit user intention.

Before using LIVE mode verify:

- correct account
- correct environment
- correct instrument
- correct quantity
- correct order side
- correct order type
- current broker connection state
- current market data state
- available portfolio and risk context

Do not use LIVE trading to test basic application behaviour.

Basic workflow validation should be completed in deterministic tests and PAPER mode first.

---

# Starting the Application

When the application starts, users should verify:

1. Application opened successfully.
2. Runtime status is healthy or clearly degraded.
3. Broker connection state is visible.
4. Market data connection state is visible.
5. Active environment is correct.
6. Workspace was restored as expected.
7. Widgets show meaningful data states.

If startup fails or the application starts in a degraded state, review the visible status messages and logs where required.

---

# Main Workspace

The Trading Cockpit uses a configurable workspace.

Users may arrange widgets to support their workflow.

Typical workspace actions include:

- opening widgets
- closing widgets
- docking widgets
- resizing widgets
- moving widgets
- restoring layouts
- changing table columns
- applying filters
- switching context

The application should preserve the working context where technically and operationally safe.

When the Scanner workspace is taller than the available window area, use its vertical
scrollbar to reach the result details, Symbol history and safety information. The result
and history tables may also show their own scrollbars for longer row lists.

---

# Widgets

Widgets provide focused functionality.

A widget should have one primary responsibility.

Examples:

- Watchlist
- Market Overview
- Price Chart
- Candidate Review
- Decision Center
- Order Entry
- Orders
- Positions
- Portfolio
- Risk
- Notifications

Widgets may show loading, stale, unavailable, disconnected or error states.

Users should not assume displayed trading data is current unless the widget indicates a current or ready state.

---

# Shared Instrument Context

Some widgets may share the active instrument context.

Example:

```text
Watchlist
        ↓
Price Chart
        ↓
Decision Center
        ↓
Order Entry
```

When a user selects an instrument in one widget, other compatible widgets may update automatically.

Context-aware widgets should clearly show the active instrument.

If a widget changes context unexpectedly, verify the selected instrument before making decisions or preparing orders.

---

# Data States

Trading information can have different operational states.

Common states:

```text
Loading
Ready
Stale
Unavailable
Disconnected
Error
```

Users should understand these states before relying on displayed information.

---

# Loading

The widget or capability is retrieving or processing data.

Action:

- wait for the operation to complete
- avoid making decisions based on incomplete information

---

# Ready

The data is available according to the current application and provider state.

Action:

- continue normal workflow
- still verify timestamps and source where relevant

---

# Stale

The displayed value is no longer considered current.

The application may show the last available value with a stale indicator.

Action:

- verify whether the value is still useful
- refresh or wait for updated data
- avoid treating stale data as current

---

# Unavailable

The value is not currently available.

Examples:

```text
Unavailable
N/A
No data
```

Unavailable is not the same as zero.

Action:

- do not treat unavailable financial values as zero
- review source state
- continue only when the missing value is not required for the decision

---

# Disconnected

A required external connection is unavailable.

Examples:

- broker disconnected
- market data disconnected
- external service unavailable

Action:

- review affected capability
- avoid broker-dependent actions until connection state is understood
- verify whether displayed data is stale or unavailable

---

# Error

The application or widget encountered a failure.

Action:

- read the user-facing message
- identify whether user action is required
- review logs or support information where needed
- avoid repeating trading-critical actions until the state is understood

---

# Watchlists

Watchlists help users monitor selected instruments.

Current session workflow:

1. Select a visible row in the Scanner workspace.
2. Choose **Add to Watchlist**.
3. Confirm `ADDED`, or `ALREADY EXISTS` when the Symbol is already present.
4. Select a Symbol in the Quick Info Watchlist to publish source `Watchlist`.
5. Use **Remove Selected** to remove only that entry.

The current Watchlist preserves insertion order and prevents duplicates. It is
session-local and is not restored after application restart. Quotes, sorting,
filtering and named Watchlists are not yet implemented.

Before using a watchlist value for a decision, verify:

- quote state
- timestamp
- source
- stale or unavailable indicators

---

# Market Monitoring

Market monitoring widgets help users observe current market conditions.

Possible information includes:

- instrument prices
- price changes
- market state
- timestamps
- quote source
- stale indicators
- unavailable values

Market monitoring is informational.

It does not automatically create trading decisions or orders.

---

# Trading Candidates

Trading Candidates represent possible opportunities under review.

A candidate is not the same as a trading decision.

Users may review:

- selected instrument
- market context
- candidate rationale
- relevant indicators
- portfolio context
- risk context
- current data state

A candidate should not result in order submission unless the user or an explicit application workflow creates a Trading Decision and proceeds to order preparation.

---

# Decision Center

The Decision Center supports structured review before trading action.

Users may review:

- selected instrument
- candidate information
- market context
- portfolio context
- risk context
- decision rationale
- decision state

A Trading Decision should be traceable.

Before moving from decision to order preparation, verify that required information is current and complete.

---

# Order Entry

Order Entry is a trading-critical area.

Before submitting an order, review:

- environment
- account
- instrument
- action
- quantity
- order type
- price parameters
- time-in-force
- validation messages
- market data state
- broker connection state
- portfolio context
- risk context

Invalid orders shall not be submitted.

The user should not rely on visual assumptions.

Always review the explicit order parameters.

---

# Order Submission

Submitting an order may create an external broker side effect.

After submission, the application should distinguish between:

```text
Submission Requested
        ↓
Transmitted
        ↓
Broker Acknowledged or Rejected
        ↓
Partially Filled or Filled
```

A local submission action is not the same as broker acknowledgement.

Do not assume an order is accepted until broker acknowledgement is visible.

---

# Order Cancellation

Order cancellation is also trading-critical.

A cancellation request is not the same as broker-confirmed cancellation.

After requesting cancellation, monitor:

- cancellation pending state
- broker cancellation acknowledgement
- rejection
- possible execution during cancellation

Do not assume that an order is cancelled until the broker-derived state confirms it.

---

# Orders View

The Orders view may show:

- submitted orders
- working orders
- rejected orders
- cancelled orders
- partially filled orders
- filled orders

Review order state carefully.

Repeated broker messages, reconnects or refreshes should not be interpreted manually as separate intentional orders unless the application state confirms it.

---

# Positions View

The Positions view shows current or historical position state where available.

Users should verify:

- instrument
- quantity
- side
- average price
- market value
- unrealized profit or loss
- realized profit or loss where available
- source
- timestamp
- reconciliation state where relevant

Position state should not be inferred only from chart or order display.

---

# Portfolio View

The Portfolio view provides account-level or portfolio-level information.

Possible information includes:

- cash
- net liquidation value
- exposure
- unrealized profit or loss
- realized profit or loss
- allocation
- account state
- broker-derived values
- local values

Unavailable values shall not be treated as zero.

Broker-derived and locally calculated values may differ until reconciliation is complete.

---

# Risk View

Risk information supports trading review and operational awareness.

Possible information includes:

- position exposure
- portfolio exposure
- concentration
- order risk validation
- trading limits
- risk alerts

Risk information depends on available market, portfolio and position data.

If required data is stale or unavailable, risk information may also be incomplete.

---

# Reconciliation

Reconciliation compares local application state with broker-derived state.

Possible reconciliation outcomes:

- no discrepancy
- discrepancy detected
- action required
- reconciliation failed

A discrepancy may involve:

- missing local order
- missing broker order
- order state mismatch
- position state mismatch
- quantity mismatch

Reconciliation observation does not automatically mean repair.

Repair actions require explicit workflow support and user review where applicable.

---

# Notifications

Notifications communicate operationally relevant information.

Possible levels:

- Information
- Warning
- Error
- Critical

Examples:

- broker disconnected
- market data stale
- order rejected
- reconciliation discrepancy
- background service failure

Critical trading events should remain visible until appropriately handled.

Routine noise should not distract from operationally important information.

---

# Command Palette

The Command Palette supports keyboard-driven workflows.

Possible commands:

- open widget
- close widget
- switch workspace
- select instrument
- open settings
- refresh data
- execute application command

Unavailable commands should be disabled or omitted.

Commands should respect the current application state.

---

# Tables

Tables are used heavily throughout the Trading Cockpit.

Typical table capabilities may include:

- sorting
- filtering
- column resizing
- column reordering
- row selection
- multi-selection
- context menus
- persistent column state

Numeric and financial values should be formatted consistently.

---

# Financial Values

Financial values may include:

- prices
- quantities
- currency values
- percentages
- exposure
- profit and loss

Review precision, sign and availability.

Important distinction:

```text
Unavailable
        ≠
0
```

The application shall not invent missing financial information.

---

# Timestamps

Trading information may have multiple timestamp sources.

Examples:

- market timestamp
- broker timestamp
- local application timestamp

Users should verify timezone context where relevant.

Do not assume different timestamps refer to the same source or timezone.

---

# Workspace Persistence

The application may persist UI state such as:

- workspace layout
- widget visibility
- widget position
- widget size
- table columns
- sorting
- filters
- selected timeframe

Business data is separate from UI layout state.

A restored workspace does not necessarily mean all trading data is current.

Always verify data state after startup or reconnect.

---

# Error Handling

When an error occurs:

1. Read the visible error message.
2. Identify the affected capability.
3. Check whether user action is required.
4. Avoid repeating trading-critical actions until state is clear.
5. Review logs where needed.
6. Contact support or development with relevant context if required.

Useful information may include:

- time of error
- active environment
- affected instrument
- affected order or position
- visible application state
- relevant log file
- steps that led to the error

Do not share real credentials or sensitive account information unnecessarily.

---

# Logs

Logs are intended for diagnosis and operational review.

Logs may help explain:

- startup behaviour
- configuration loading
- broker connection state
- market data state
- order workflow events
- reconciliation events
- runtime failures

Logs are not a replacement for authoritative business state.

For trading-critical workflows, review the visible application state and broker state where applicable.

---

# Safe Operating Practices

Before trading-critical action:

- verify PAPER or LIVE mode
- verify account
- verify instrument
- verify current data state
- verify order parameters
- verify broker connection
- verify portfolio context
- verify risk context
- understand expected side effect

After trading-critical action:

- verify acknowledgement state
- monitor rejection or fill state
- review position impact
- review reconciliation state where relevant

---

# Troubleshooting

## Application does not start

Check:

- configuration
- runtime status
- logs
- recent changes
- dependency installation
- environment selection

---

## Broker disconnected

Check:

- broker application availability
- account login state
- network state
- configured host and port
- selected environment
- visible broker status

Avoid broker-dependent actions until the state is understood.

---

## Market data unavailable

Check:

- market data connection
- subscription state
- provider permissions
- selected instrument
- timestamp and source
- stale or unavailable indicators

Do not treat unavailable market data as zero.

---

## Order not acknowledged

Check:

- order state
- broker connection state
- broker application
- rejection messages
- timeout state
- orders view
- broker-side order list where applicable

Do not resubmit blindly.

Unknown external order state requires careful review.

---

## Position does not match expectation

Check:

- orders
- fills
- broker position state
- local position state
- reconciliation state
- timestamps
- account selection

Do not manually overwrite business state unless an explicit approved recovery process exists.

---

# User Review Checklist

Before normal operation verify:

- application started correctly
- active environment is correct
- broker state is understood
- market data state is understood
- workspace restored correctly
- required widgets are visible
- stale or unavailable data is identified

Before order submission verify:

- correct account
- correct environment
- correct instrument
- correct action
- correct quantity
- correct order type
- correct price parameters
- validation passed
- market data state acceptable
- broker state acceptable
- portfolio and risk context reviewed

After order submission verify:

- broker acknowledgement or rejection
- fill or partial fill state
- cancellation state where applicable
- position impact
- reconciliation state where relevant

---

# Related Documents

- Product_Vision.md
- Product_Roadmap.md
- Project_Overview.md
- UI_Guidelines.md
- Widget_Catalog.md
- Technical_Specifications.md
- Configuration.md
- Runtime.md
- Logging.md
- Monitoring.md
- Testing_Strategy.md
- AGENTS.md
