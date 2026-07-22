# Interface Contracts

## Purpose

This document defines how Argus subsystems communicate.

Every engine may only communicate through published interfaces.

No subsystem may directly manipulate another subsystem's internal data.

---

## Communication Principles

- Loose coupling
- Single responsibility
- Explicit contracts
- Versioned interfaces
- Observable interactions

---

## Atlas

Provides:

- Store Knowledge
- Retrieve Knowledge
- Search Knowledge
- Update Knowledge
- Delete Knowledge

Consumes:

- Memory Service
- Event Bus

---

## Cortex

Provides:

- Analyze
- Plan
- Decide
- Explain

Consumes:

- Atlas
- Memory
- Event Bus

---

## Hermes

Provides:

- Send Message
- Receive Message
- Call External API

Consumes:

- Cortex
- Event Bus

---

## Navigator

Provides:

- Execute Plan
- Execute Task
- Get Status

Consumes:

- Cortex
- Scheduler
- Event Bus

---

## Sentinel

Provides:

- Authenticate
- Authorize
- Audit
- Evaluate Risk

Consumes:

- Event Bus
- Logging

---

## Memory

Provides:

- Store
- Retrieve
- Search

Consumes:

- Logging

---

## Event Bus

Provides:

- Publish
- Subscribe

Consumes:

- Logging

---

## Scheduler

Provides:

- Schedule
- Cancel
- Trigger

Consumes:

- Navigator
- Event Bus

---

## Configuration

Provides:

- Get
- Set
- Validate

Consumes:

- Event Bus

---

## Logging

Provides:

- Log
- Query

Consumes:

- Configuration

---

## Rules

No engine may bypass another engine's published interface.

No subsystem may access another subsystem's internal storage directly.

All cross-subsystem communication must occur through defined contracts.