# AGENTS.md

# Trading Platform Pro

**Developer & AI Agent Guide**

Version: 1.0
Status: Active

---

# Purpose

This document defines the mandatory engineering rules for all contributors working on this repository, including human developers and AI coding agents.

It complements the project documentation and shall be followed for every implementation unless explicitly stated otherwise.

For project scope and business context see:

* `docs/product/Project_Overview.md`

---

# Mission

Maintain a professional, modular and maintainable trading platform while preserving architecture, software quality and long-term extensibility.

Every change shall improve the project without introducing unnecessary complexity.

---

# Core Principles

Always:

* Analyze before changing.
* Understand existing code.
* Make the smallest useful change.
* Preserve architecture.
* Keep documentation synchronized.
* Prefer clarity over cleverness.

Never:

* Guess missing requirements.
* Invent APIs or project structures.
* Rewrite unrelated code.
* Introduce hidden side effects.
* Duplicate existing functionality.

---

# Repository Rules

Before modifying code:

1. Read the complete file.
2. Understand surrounding modules.
3. Identify dependencies.
4. Check existing documentation.
5. Propose the implementation.
6. Implement.
7. Test.
8. Review.

Never skip analysis.

---

# Documentation First

Documentation is part of the implementation.

When behaviour, architecture or interfaces change:

* update the corresponding documentation
* avoid duplicated information
* reference the authoritative document instead of copying content

Single Source of Truth:

| Topic          | Document                           |
| -------------- | ---------------------------------- |
| Project        | `docs/product/Project_Overview.md` |
| Product Vision | `docs/product/Product_Vision.md`   |
| Architecture   | `docs/architecture/`               |
| API            | `docs/api/`                        |
| Specifications | `docs/specifications/`             |
| Operations     | `docs/operations/`                 |

---

# Architecture Rules

The project follows:

* Clean Architecture
* Domain-Driven Design (DDD)
* Event-Driven Architecture
* SOLID Principles

Respect dependency direction.

Do not introduce architecture violations.

---

# Development Workflow

Every task follows:

1. Analyze
2. Design
3. Implement
4. Test
5. Review
6. Commit
7. Push

Changes should remain:

* small
* atomic
* reviewable

---

# Coding Rules

Mandatory:

* Python 3.13
* Full type hints
* UTF-8
* Ruff compliant
* Meaningful naming
* Small functions
* Small classes

Avoid:

* dead code
* duplicated logic
* wildcard imports
* unnecessary abstractions
* speculative implementations

---

# Testing

Every implementation shall be verified.

Preferred order:

1. Unit Tests
2. Integration Tests
3. Smoke Tests

No implementation is complete without appropriate validation.

---

# Trading Safety

Safety has priority over convenience.

Never modify without explicit approval:

* trading logic
* execution workflow
* risk management
* broker integration
* position handling
* order management

Prefer PAPER mode during development.

---

# AI Agent Rules

AI agents shall:

* analyze before changing
* preserve architecture
* minimize modifications
* avoid assumptions
* ask when information is missing
* keep documentation synchronized

Never invent project files, interfaces or behaviour.

---

# Communication

Technical communication should be:

* concise
* factual
* actionable

Avoid:

* repetition
* speculation
* unnecessary explanations

---

# Definition of Done

A task is complete only if:

* implementation finished
* tests successful
* documentation updated
* architecture preserved
* review completed
* committed
* pushed

---

# Long-Term Goal

Trading Platform Pro shall evolve into a modular enterprise trading platform supporting multiple professional trading applications on a shared architectural foundation while maintaining high software quality, predictable behaviour and excellent developer experience.
