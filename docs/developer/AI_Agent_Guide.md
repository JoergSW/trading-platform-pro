# AI Agent Guide

**Project:** Trading Platform Pro
**Application:** Trading Cockpit
**Version:** 1.0
**Status:** Active

---

# Purpose

This guide defines the project-specific operating rules for AI coding agents working on the Trading Platform Pro repository.

It complements `AGENTS.md` by providing implementation-specific guidance.

---

# Project Mission

Trading Platform Pro is a modular software platform.

The first application is the **Trading Cockpit**, providing an integrated workspace for:

* Market Monitoring
* Decision Center
* Portfolio Management
* Order Management
* Risk Management
* Reporting
* Workspace Management

Project overview:

* `docs/product/Project_Overview.md`

---

# Mandatory Workflow

Every task shall follow this sequence:

1. Understand the request.
2. Analyze the affected code.
3. Read related documentation.
4. Identify impacted components.
5. Propose the implementation.
6. Wait for approval if required.
7. Implement.
8. Test.
9. Update documentation.
10. Commit.

---

# Analysis Before Implementation

Before changing code:

* read the complete file
* inspect neighbouring modules
* understand dependencies
* preserve public interfaces
* avoid unnecessary refactoring

Never modify code based on assumptions.

---

# Documentation First

Before implementing new functionality verify whether documentation already exists.

Relevant locations:

* `docs/product/`
* `docs/specifications/`
* `docs/architecture/`
* `docs/api/`
* `docs/operations/`
* `docs/developer/`

Documentation is part of the implementation.

---

# Architecture Rules

Always preserve:

* Clean Architecture
* Domain-Driven Design
* Event-Driven Architecture
* Dependency direction
* Modular boundaries

Never introduce architecture violations.

---

# Implementation Rules

Prefer:

* small changes
* focused commits
* explicit code
* reusable components
* deterministic behaviour

Avoid:

* duplicated logic
* speculative code
* unnecessary abstractions
* breaking existing behaviour

---

# Trading Safety

Without explicit approval, never modify:

* execution logic
* broker integration
* order workflow
* risk management
* position management
* live trading behaviour

Development should target PAPER mode whenever possible.

---

# Quality Requirements

Every change should:

* compile successfully
* pass relevant tests
* preserve existing behaviour
* update documentation when required

---

# Communication

Responses should be:

* concise
* factual
* implementation-oriented

Avoid repetition and speculation.

---

# Definition of Success

A task is complete only when:

* requested functionality is implemented
* tests pass
* documentation is updated
* architecture remains consistent
* changes are ready for review
