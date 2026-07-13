# Infrastructure

Version: 1.0

---

# Purpose

This document defines the Infrastructure layer of Trading Platform Pro and its primary application, the Trading Cockpit.

Infrastructure provides technical capabilities, external integrations and adapter implementations required by application workflows.

Infrastructure shall remain isolated from domain business rules and trading decisions.

---

# Infrastructure Responsibilities

Infrastructure is responsible for technical capabilities including:

- Configuration
- Structured Logging
- Dependency Injection
- Persistence
- Broker Integration
- Market Data Integration
- File System Access
- Messaging
- Runtime Services
- Scheduling
- Monitoring
- Health Checks
- Serialization
- Security Integration
- External APIs

Infrastructure implements ports and technical abstractions defined by the Application or Domain layers where appropriate.

The initial Market Data infrastructure contains two read-only adapters:

- `UnavailableMarketSnapshotProvider` for the safe no-source default
- `JsonMarketSnapshotProvider` for an explicitly selected local JSON snapshot file

The JSON adapter performs file access and provider-payload validation inside
Infrastructure, then returns only the Application-owned `MarketSnapshot`. It does not
connect to a broker, subscribe to market data or expose executable actions.

The initial Scanner infrastructure also contains two read-only adapters:

- `UnavailableScannerResultsProvider` for the safe no-source default
- `JsonScannerResultsProvider` for an explicitly selected local JSON result file

The Scanner JSON adapter owns file access and strict payload validation, then returns only
the Application-owned `ScannerResults`. It does not execute a scan, connect to a broker,
request market data or expose trading actions.

---

# Infrastructure Principles

Infrastructure shall:

- isolate external dependencies
- implement explicit ports
- remain replaceable where practical
- contain no trading decisions
- contain no domain business rules
- expose operational state
- expose technical failures
- support deterministic testing
- support controlled lifecycle management

Infrastructure shall not silently alter business state.

---

# Infrastructure Boundaries

Infrastructure may translate:

- external data
- provider identifiers
- transport errors
- persistence records
- technical connection state

Infrastructure shall not decide:

- whether a trading candidate is accepted
- whether a trading decision is valid
- whether portfolio risk is acceptable
- whether an order should be submitted
- whether a position should be closed

These decisions belong to Domain or Application workflows.

---

# Adapter Architecture

External systems shall be accessed through explicit adapters.

```text
Application Port
      │
      ▼
Infrastructure Adapter
      │
      ▼
External System
