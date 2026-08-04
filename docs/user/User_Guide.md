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

# Analysis Price Chart

The Analysis workspace can display read-only historical price and volume data for the
Symbol selected in Scanner or Watchlist. Start the cockpit with an explicit local source:

```bash
trading-cockpit --scanner-results-json temp/scanner-results.json --price-history-json resources/examples/price-history.json
```

The included file is synthetic manual-test data. Select a Scanner result or Watchlist
entry, then open Analysis. The Price History panel shows the source, source-defined
timeframe, number of bars and UTC date range. At narrower widths, context and metadata cards
stack into one column. At reduced window heights, use the Analysis workspace's vertical
scrollbar; the workspace does not scroll horizontally and the chart keeps its readable minimum
height. Use **Refresh** to reload the current Symbol.

States:

- `NO SELECTION`: no active Symbol
- `LOADING`: the configured local file is being read and validated
- `READY`: validated OHLCV data is displayed
- `NO DATA`: the selected Symbol is absent or has an empty bar list
- `UNAVAILABLE`: no source is configured or the file cannot be read
- `ERROR`: JSON or OHLCV validation failed

The chart does not estimate missing values, reuse another Symbol, connect to a broker or
perform any order, trading or LIVE action.

To enable persistent Trading Candidate intake at the same time, provide an explicit local
SQLite path:

```bash
trading-cockpit --scanner-results-json temp/scanner-results.json --price-history-json resources/examples/price-history.json --trading-candidates-db temp/trading-candidates.db
```

The parent directory must already exist. The application does not infer a database path or
create missing directories.

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

Trading Candidates represent persistent opportunities under review. A candidate is not a
Trading Decision and does not authorize an order.

With `--trading-candidates-db <path>` configured:

1. Select a visible Symbol in Scanner or Watchlist.
2. Open Analysis.
3. Verify that candidate intake shows `READY`.
4. Select **Add to Decision Center**.
5. Confirm `ADDED` or, for a previously stored Symbol, `ALREADY EXISTS`.

A new row stores:

- canonical candidate identity
- uppercase Symbol
- origin `Scanner` or `Watchlist`
- status `NEW`
- Created UTC and Updated UTC timestamps

Adding the same Symbol again does not create a second row or overwrite its original origin
or timestamps. Without the database option, candidate intake remains `UNAVAILABLE` and no
database file is created.

---

# Decision Center

The Decision Center is a persistent candidate list with explicit review lifecycle actions.

Visible states:

- `UNAVAILABLE`: no candidate database was configured
- `LOADING`: the candidate collection is being read
- `EMPTY`: the configured database contains no candidates
- `READY`: persistent candidates are displayed
- `ERROR`: storage could not be read

The table shows Symbol, Origin, Status, Created UTC and Updated UTC. Select one row to
publish the Symbol with source `Decision Center`; Analysis then follows that context.
Navigation is not changed automatically.

Available actions are:

- **Start Review**: `NEW → REVIEWING`
- **Reject**: `NEW` or `REVIEWING → REJECTED`
- **Archive**: `NEW`, `REVIEWING` or `REJECTED → ARCHIVED`

Only actions valid for the current status are enabled. Every successful change displays
`UPDATED`, preserves the selected row and context, and replaces Updated UTC while leaving
Created UTC unchanged. Invalid transitions are rejected rather than stored. Use **Refresh**
to reload the configured database.

## Trading Decision Draft and Acceptance

A selected candidate with status `REVIEWING` exposes an editable required-rationale field and
**Create Decision Draft**. The action creates one linked decision with status `DRAFT` and
shows its Decision ID, rationale, Created UTC and Updated UTC.

A second decision is not created for the same candidate. The original rationale and timestamps
remain unchanged. Draft creation leaves the candidate in `REVIEWING` and does not navigate
automatically. Selecting the same candidate after a restart restores the decision read-only
when the same database path is used.

For a `REVIEWING` Candidate with a linked `DRAFT`, **Accept Decision** becomes available. The
explicit action changes both records to `ACCEPTED` in one transaction. Candidate and Decision
receive the same Updated UTC value; their identities, rationale, creation timestamps and
selection remain unchanged. A conflict or missing record rolls the complete update back.

Acceptance records the professional trading decision only. It does not prepare or submit an
order, connect to a broker or perform a PAPER or LIVE trading action. Restarting with the same
database path restores the accepted statuses. Later decision transitions, tags, order
preparation, broker access and LIVE actions are not part of this slice.

## Decision History

The read-only **Decision History** panel loads every stored Trading Decision from the configured
SQLite database. Visible states are `UNAVAILABLE`, `LOADING`, `EMPTY`, `READY` and `ERROR`.
The table is ordered by Updated UTC with the newest decision first and shows Symbol, Decision
Status, Created UTC, Updated UTC and Decision ID.

Select a history row to display its Candidate ID and complete stored rationale. This selection
is informational: it does not change the selected Trading Candidate, shared instrument context,
Decision status or Portfolio state. Use **Refresh Decision History** to reload the database. The
table retains its own horizontal scrollbar at narrow widths.

## Portfolio Context for the Selected Candidate

When `--portfolio-snapshot-json` is configured, selecting a Candidate displays the current
read-only Portfolio state in the Decision Center. The panel shows source, Observed UTC, account
reference, currency and available account values. It then searches the supplied positions for the
selected Candidate Symbol.

- `EXISTING POSITION` shows the exact supplied quantity, prices, current value and unrealized P&L.
- `NO EXISTING POSITION` means the valid snapshot contains no Position for that Symbol.
- `UNAVAILABLE` means no reliable snapshot or position data is available.

Missing values remain `UNAVAILABLE`; they are not calculated or treated as zero. Use **Refresh
Portfolio Context** to reload the configured source. Refresh preserves the selected Candidate and
the Analysis source `Decision Center`. It does not change Candidate or Decision status and does
not perform a risk approval, order, broker or trading action.

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

The current implementation is enabled only with:

```bash
trading-cockpit --portfolio-snapshot-json <path>
```

It shows account reference, currency, source, Observed UTC, optional Cash, Net Liquidation
Value and Unrealized P&L, plus current positions. Missing financial fields display
`UNAVAILABLE`; a source-provided zero displays as zero. `EMPTY` means valid account context
with no current positions. A snapshot loaded at least 300 seconds after its observation is
shown as `STALE`. Use **Refresh** to reload the same explicit file. Account, financial and
exposure cards reflow from two columns to one at narrower widths. Use the Portfolio workspace's
vertical scrollbar to reach lower sections. The workspace itself does not scroll horizontally;
use the independent horizontal scrollbars inside **Current Positions** and **Position Exposure
Breakdown** to reach all columns when needed. Selecting a position publishes its
Symbol with source `Portfolio`; navigation is not changed automatically. The same
validated snapshot is also available as informational context for an explicitly selected Candidate
in the Decision Center.

The **P&L Summary** uses only source-provided position `Unrealized P&L` fields. It shows
positive P&L, negative P&L as a loss amount, net position P&L, largest winner, largest loser and
P&L coverage. Missing position P&L remains `UNAVAILABLE` and marks the summary `INCOMPLETE`; it is
not reconstructed from Average Price, Current Price or Current Value. Account Unrealized P&L is
shown separately and is not used to replace or reconcile the position summary. A valid empty
Portfolio shows known zero position P&L. Snapshot source, Observed UTC and `STALE` state remain
visible. The Decision Center shows the same compact P&L summary for the selected Candidate without
changing Candidate or Decision state.

The **Exposure Summary** uses only source-provided `Current Value` fields. Positive values
contribute to Long Exposure; negative values contribute by absolute magnitude to Short Exposure.
Gross Exposure is long plus short, while Net Exposure is long minus short. The view also shows
the largest valued position, its concentration within valued Gross Exposure and valuation
coverage. The **Position Exposure Breakdown** shows each Symbol, `LONG`, `SHORT` or `FLAT`
direction, signed Current Value, absolute exposure, share of valued Gross Exposure and valuation
state. Missing Current Value fields display `UNAVAILABLE`; direction and contribution are not
reconstructed from Quantity or Current Price. A valid empty Portfolio shows known zero exposure.
Snapshot source, Observed UTC and `STALE` state remain visible.

The view does not issue a risk approval, calculate missing values, connect to a broker, modify
positions, prepare orders or perform trading or LIVE actions.

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

The dedicated **Risk** navigation workspace currently reuses the configured read-only Portfolio
Snapshot. It shows Snapshot state and exposure completeness separately, source, Observed UTC,
long, short, gross and net exposure, largest Position, concentration, valuation coverage,
explicit unvalued Symbols and the Position Exposure Breakdown. Metadata and exposure cards use
a readable two-column layout at the supported minimum window size, so fields do not require
manual column-like resizing; only the wide Position Exposure table scrolls horizontally when
needed. **Refresh** reloads only the same configured local Portfolio source. Missing Current Values
remain `UNAVAILABLE`; they are not reconstructed from Quantity or Current Price.

If required data is stale or unavailable, risk information may also be incomplete. `STALE` remains
visible independently from `COMPLETE` or `INCOMPLETE`. The current Decision Center shows the same
compact Portfolio exposure summary and selected-position exposure contribution for the explicitly
selected Candidate without changing Candidate, Decision or acceptance state. The Risk workspace
adds no risk verdict, limit evaluation, order gate, broker, trading or LIVE action.

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


# Candidate Tags

Select a persistent Trading Candidate in the Decision Center to load its Candidate Tags.
Enter a value and use **Add Tag** while the Candidate is `NEW` or `REVIEWING`. Surrounding
whitespace is removed, repeated whitespace is reduced to one space and the normalized value
may contain at most 32 characters. A tag that differs only by letter case is treated as an
existing tag.

Select a stored tag and use **Remove Tag** to delete it. **Refresh Candidate Tags** reloads
the persistent alphabetical list without changing the selected Candidate or the shared
Instrument Context. Tags remain visible after the Candidate becomes `REJECTED`, `ACCEPTED`
or `ARCHIVED`, but Add Tag and Remove Tag are disabled.

# Candidate Notes

Select a persistent Trading Candidate in the Decision Center to load its Candidate Notes.
Use **Add Note** to append evidence or review context while the Candidate is NEW or REVIEWING.
Notes are immutable in this product slice: they cannot be edited or deleted. The newest note
is shown first, and selecting a row displays the complete stored text. Notes remain readable
after the Candidate is rejected, accepted or archived.
