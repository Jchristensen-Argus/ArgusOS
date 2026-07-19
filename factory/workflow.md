# Argus Factory Workflow

Version: 1.0  
Status: Active

---

# Purpose

This document defines the standard engineering workflow used to build every subsystem within ArgusOS.

Every engineer—human or AI—follows this workflow.

The goal is repeatability, quality, and continuous improvement.

---

# Engineering Lifecycle

Every feature progresses through the following stages.

```
Vision
   ↓
Specification
   ↓
Architecture Review
   ↓
Implementation
   ↓
Testing
   ↓
Documentation
   ↓
Architect Review
   ↓
Git Commit
   ↓
Release
```

Skipping stages is discouraged and should only occur with explicit approval.

---

# Stage 1 — Vision

Owner:
Founder

Deliverable:

- Problem statement
- Desired outcome
- Business value

Questions:

- Why are we building this?
- Who benefits?
- How will success be measured?

---

# Stage 2 — Specification

Owner:
Chief Systems Architect

Deliverable:

Subsystem specification.

The specification defines:

- Purpose
- Responsibilities
- Public API
- Inputs
- Outputs
- Dependencies
- Definition of Done

No implementation details belong here.

---

# Stage 3 — Architecture Review

Owner:
Founder + Architect

Purpose:

Verify that the proposed subsystem:

- aligns with ARGUS.md
- follows PRINCIPLES.md
- fits the overall architecture
- does not duplicate existing functionality

---

# Stage 4 — Implementation

Owner:
Software Engineer

Current Engineer:
Claude

Future Engineer:
Argus

Deliverables:

- Production code
- Unit tests
- Updated documentation

---

# Stage 5 — Testing

Every implementation should verify:

- Expected behavior
- Edge cases
- Invalid input
- Regression protection

---

# Stage 6 — Documentation

Documentation is updated before the task is considered complete.

Documentation includes:

- Architecture
- Public APIs
- CHANGELOG
- Design updates when required

---

# Stage 7 — Architect Review

The Architect verifies:

- Simplicity
- Maintainability
- Standards compliance
- Architectural integrity

Possible outcomes:

- Approved
- Revision Requested

---

# Stage 8 — Git

Only approved work is committed.

Each commit should represent one logical engineering change.

---

# Stage 9 — Release

A release should provide a meaningful improvement to either:

- ArgusOS
- Argus Factory

Every release should leave the project in a better state than before.

---

# Guiding Principle

Never optimize for writing more code.

Optimize for increasing engineering leverage.