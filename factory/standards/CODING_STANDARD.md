# Argus Coding Standard

Version: 1.0
Status: Active

---

# Purpose

This document defines the coding standard for all ArgusOS development.

It is the single canonical source of coding standards for the project. It
consolidates and supersedes the previous `CODING_STANDARDS.md` and
`coding.md` documents.

The objective is to ensure the codebase remains consistent, readable,
maintainable, and aligned with the Argus architecture.

---

# General Principles

- Write code for humans first.
- Readability over cleverness.
- Simplicity over complexity.
- Explicit over implicit.
- Composition over inheritance.
- Favor simple designs; avoid premature optimization.
- Small modules with single responsibilities.
- Every file should have a clear purpose and contain one primary concept.

---

# Python Standards

- Follow PEP 8.
- Use type hints.
- Use dataclasses when appropriate.
- Prefer `pathlib` over `os.path`.
- Avoid global state.
- Prefer dependency injection.

---

# Naming

Use descriptive names. Avoid abbreviations unless universally understood.

Good:

```
calculate_quote()
PackagingSpecification
customer_memory
```

Avoid:

```
calc()
pkgSpec
tmp
```

Naming conventions:

| Element | Convention |
|---|---|
| Classes | PascalCase |
| Functions | snake_case |
| Variables | snake_case |
| Constants | UPPER_CASE |
| Private members | _prefix |

---

# Single Responsibility

Functions should perform one logical task.

Classes should have one primary purpose.

Large functions should be decomposed into smaller units.

---

# File Organization

Each file should contain one primary concept.

Avoid mixing unrelated functionality.

---

# Documentation

Every public module should describe its purpose, inputs, outputs, and
dependencies.

Every public class requires:

- Purpose
- Responsibilities
- Dependencies

Every public function requires:

- Description
- Parameters
- Returns
- Exceptions (if applicable)

Complex logic should explain *why*, not merely *what*.

---

# Logging

Never use `print()`.

Use the Logging Service.

Log:

- Startup
- Shutdown
- Errors
- Warnings
- Major events

Do not log secrets.

---

# Error Handling

Raise meaningful exceptions.

Catch exceptions only when recovery is possible.

Never silently ignore errors.

Return meaningful error information and log unexpected conditions when
appropriate.

---

# Dependencies

Every dependency must be injected.

Avoid direct imports between engines. Communicate through published
interfaces.

Minimize external dependencies. Prefer the standard library when
practical. New dependencies must have a clear justification.

---

# Backwards Compatibility

Changes to public interfaces require architectural review.

Breaking changes should be deliberate and documented.

---

# Performance

Optimize only after correctness and clarity. Measure performance before
making optimization decisions.

---

# Security

Never expose sensitive information in logs.

Validate external input.

Follow the principle of least privilege.

---

# Testing

Every implementation package should include unit tests, and integration
tests when appropriate. No feature is complete without tests.

Tests should verify:

- Expected behavior
- Edge cases
- Invalid input
- Regressions

---

# Code Reviews

Every implementation should answer:

- Is the code correct?
- Is it understandable?
- Is it maintainable?
- Does it follow the specification?
- Does it follow Argus principles?

---

# Architecture Compliance

Implementation must never violate:

- Charter
- Principles
- Architecture
- Interface Contracts

If code conflicts with architecture, the architecture wins.

---

# Guiding Principle

Readable code is easier to improve than clever code.
