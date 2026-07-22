# ArgusOS Coding Standard

## Purpose

This document defines the coding standards for all ArgusOS development.

The objective is to ensure the codebase remains consistent, maintainable, readable, and aligned with the Argus architecture.

---

# General Principles

- Readability over cleverness.
- Simplicity over complexity.
- Explicit over implicit.
- Composition over inheritance.
- Small modules with single responsibilities.
- Every file should have a clear purpose.

---

# Python Standards

- Follow PEP 8.
- Use type hints.
- Use dataclasses when appropriate.
- Prefer pathlib over os.path.
- Avoid global state.
- Prefer dependency injection.

---

# Naming Conventions

Classes:
PascalCase

Functions:
snake_case

Variables:
snake_case

Constants:
UPPER_CASE

Private members:
_prefix

---

# Documentation

Every public class requires:

- Purpose
- Responsibilities
- Dependencies

Every public function requires:

- Description
- Parameters
- Returns
- Exceptions (if applicable)

---

# Logging

Never use print().

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

---

# Dependencies

Every dependency must be injected.

Avoid direct imports between engines.

Communicate through published interfaces.

---

# Testing

Every implementation package should include:

- Unit tests
- Integration tests (when appropriate)

No feature is complete without tests.

---

# Architecture Compliance

Implementation must never violate:

- Charter
- Principles
- Architecture
- Interface Contracts

If code conflicts with architecture, the architecture wins.