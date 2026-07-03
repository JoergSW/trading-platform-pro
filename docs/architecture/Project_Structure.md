# Project Structure

Version: 1.0

---

# Purpose

This document describes the physical structure of the Trading Platform Pro repository.

A consistent project structure improves maintainability, discoverability and scalability.

---

# Repository Layout

```
project/
│
├── docs/
├── src/
├── tests/
├── config/
├── scripts/
├── tools/
├── .github/
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── README.md
└── AGENTS.md
```

---

# Source Code

All production code resides in:

```
src/
```

The source code is organized by architectural responsibility rather than technical framework.

Example:

```
src/
└── trading_platform/
    ├── application/
    ├── domain/
    ├── infrastructure/
    ├── presentation/
    └── shared/
```

---

# Documentation

All documentation is located in:

```
docs/
```

Structure:

```
architecture/
product/
developer/
operations/
adr/
api/
ui/
user/
specifications/
decisions/
```

Each directory has a single responsibility.

---

# Tests

Automated tests reside in:

```
tests/
```

Typical structure:

```
tests/

├── unit/
├── integration/
├── system/
└── performance/
```

Tests mirror the production structure where practical.

---

# Configuration

Configuration files reside in:

```
config/
```

Configuration is externalized and environment-specific.

Examples:

- development
- testing
- production

---

# Scripts

Reusable automation scripts are stored in:

```
scripts/
```

Examples:

- build
- maintenance
- release
- utilities

---

# GitHub

Repository automation resides in:

```
.github/
```

Including:

- CI/CD
- Workflows
- Templates

---

# Naming Conventions

Directories:

- lowercase
- singular where appropriate
- descriptive names

Python files:

- snake_case

Classes:

- PascalCase

Functions:

- snake_case

Constants:

- UPPER_CASE

---

# Design Principles

The repository structure shall:

- remain simple
- be easy to navigate
- scale with project growth
- reflect the architecture
- minimize unnecessary nesting

---

# Evolution Rules

When introducing new modules:

- preserve architectural boundaries
- keep related functionality together
- avoid duplication
- document structural changes

---

# Repository Organization Rules

The repository shall follow these principles:

- one responsibility per directory
- clear separation of source code and documentation
- consistent naming conventions
- minimal directory depth
- avoid duplicated structures

---

# Documentation Structure

Documentation shall be organized by domain:

- product
- architecture
- specifications
- api
- ui
- operations
- developer
- user
- decisions

Each document shall have a single authoritative location.

---

# Repository Growth

As the project evolves:

- extend existing structures before creating new ones
- preserve architectural consistency
- avoid parallel implementations
- review the overall structure regularly

---

# Structure Review Checklist

Before introducing new folders verify:

- existing location cannot be reused
- architecture remains consistent
- naming follows conventions
- documentation is updated
- no duplicate responsibility is introduced

---

# Related Documents

- Architecture.md
- Infrastructure.md
- AGENTS.md
