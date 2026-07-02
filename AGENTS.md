# AGENTS.md

# Trading Platform Pro

**Developer & AI Agent Operating System**

Version: 1.0

---

# 1. Purpose

This document defines the mandatory engineering rules for everyone working on this repository, including human developers and AI coding agents.

Its purpose is to ensure:

- consistent architecture
- predictable implementations
- maintainable code
- high software quality
- long-term scalability

These rules apply to every change unless explicitly documented otherwise.

---

# 2. Project Vision

Trading Platform Pro is a professional-grade trading platform built using modern software engineering practices.

The project focuses on:

- reliability
- deterministic behaviour
- modular architecture
- clean separation of concerns
- long-term maintainability
- enterprise-grade quality

The software is designed to evolve over many years.

---

# 3. Core Principles

Always prefer:

- simplicity
- readability
- explicitness
- maintainability
- consistency

Avoid:

- unnecessary abstractions
- premature optimization
- duplicated logic
- hidden side effects
- speculative development

---

# 4. Development Workflow

Every task follows the same sequence:

1. Analyze the existing implementation.
2. Understand the surrounding architecture.
3. Propose the smallest useful change.
4. Implement.
5. Run tests.
6. Review the result.
7. Commit.
8. Push.

Do not skip steps.

---

# 5. File Modification Rules

Before modifying any file:

- read the complete file
- understand its purpose
- preserve existing public APIs whenever reasonable
- keep changes focused

Never rewrite code simply because another implementation looks "better".

---

# 6. Architecture Rules

The project follows **Clean Architecture** and **Domain-Driven Design (DDD)**.

Dependency direction is mandatory:

```
Infrastructure
        ↓
Application
        ↓
Domain
```

The Domain layer must not depend on any other project layer.

---

# 7. Coding Standards

Mandatory:

- Python 3.13
- UTF-8
- `from __future__ import annotations`
- full type hints
- Ruff compliant
- small functions
- small classes
- meaningful names

Avoid:

- wildcard imports
- unused code
- global mutable state
- magic numbers

---

# 8. Error Handling

Errors shall:

- be explicit
- provide meaningful messages
- never fail silently

Exceptions must only be caught when there is a clear recovery strategy.

---

# 9. Logging

Logging must:

- be structured
- be deterministic
- avoid duplicated entries
- never expose secrets

Use project logging infrastructure only.

---

# 10. Testing

Every implementation change requires testing.

Preferred order:

1. unit tests
2. integration tests
3. system tests

Tests must remain deterministic.

---

# 11. Git Workflow

Preferred workflow:

```
Implement

↓

pytest

↓

git add

↓

git commit

↓

git push
```

Commits should be:

- small
- atomic
- reviewable

Do not mix unrelated changes.

---

# 12. Documentation

Documentation is part of the software.

Whenever architecture or behaviour changes:

- update the corresponding documentation
- keep examples synchronized
- avoid outdated information

---

# 13. AI Agent Rules

AI agents shall:

- analyze before changing
- avoid guessing
- preserve architecture
- minimize code changes
- respect project conventions
- ask when required information is missing

Never invent project files or structures.

---

# 14. Communication Style

Technical communication should be:

- concise
- precise
- factual

Avoid:

- repetition
- unnecessary explanations
- speculation

---

# 15. Definition of Done

A task is complete only if:

- implementation finished
- tests passed
- Ruff passes
- architecture respected
- documentation updated (if required)
- committed
- pushed

---

# 16. Long-Term Goal

Trading Platform Pro shall evolve into a professional, enterprise-grade trading platform with:

- excellent architecture
- high maintainability
- comprehensive documentation
- predictable behaviour
- outstanding developer experience
