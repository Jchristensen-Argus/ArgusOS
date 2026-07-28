# ArgusOS Architecture

Canonical, current. Replaces the stale content formerly at the repository root (`ARCHITECTURE.md`), which described a pre-Factory prototype retired per `design/decisions/0004_REMOVE_LEGACY_PROTOTYPE.md`. This document describes the real, verified state of the repository as of 2026-07-27, plus the governing philosophy it's built against. Where this document and a `factory/packages/0XX_*.md` framework document disagree on a specific package's detail, the framework document governs that package (per ADR-0003) — this document is the map, not the territory.

---

## Governing Philosophy: the Argus Canon

ArgusOS is the implementation of a separately maintained philosophical and architectural foundation, the Argus Canon:

- **Document I — The Constitution of Argus.** Supreme authority. Governs the relationship between Argus and the humans/organizations it serves: responsibility, trust, transparency, governance.
- **Document II — The Cognitive Architecture of Argus.** What Memory, Knowledge, Learning, Reasoning, and Decision are, how they differ, and how information moves between them. 18 Core Principles (CA-01–CA-18).
- **Document III — The Reasoning Engine.** The full mechanical specification of one concept Document II defines at the ontology level: how a single reasoning cycle works.

(Numbering per Canon ADR-0008 — reflects conceptual dependency order, not the order the documents were drafted in.)

As of Canon ADR-0009, the Canon is in **Architecture Freeze v1.0**: no new Core pillars or major architectural documents are created by default. New problems are solved within the existing Canon first; a new pillar is only proposed if implementation reveals a genuine deficiency that extension can't resolve.

---

## The Three-Tier Structure

**CORE** (`argus/`, minus `argus/modules/` and `argus/integrations/`) — general-purpose, permanently business-agnostic. Never imports or assumes a Module's, Business's, or Integration's concepts (Cognitive Architecture, CA-10).

**MODULES** (`argus/modules/`) — business-specific. Own expertise, not infrastructure (CA-11). Register with Core via `argus.plugins` (Package 014) — no Module invents its own registration mechanism. Currently: Sales (`argus/modules/sales/`, in progress).

**INTEGRATIONS** (`argus/integrations/`) — one external system per package, module-agnostic, extends `argus.connectors` (Package 017). None built yet; the Sales module's planned Dynamics integration will be the first.

The test this boundary must always pass: nothing in `argus/modules/` or `argus/integrations/` is importable from Core, and nothing in Core imports from either.

---

## Core: What's Actually Built

41 packages (001–041) implement Core. Verified directly against the repository, not assumed from prior design work:

- **26 services wired into `argus/bootstrap.py`**, constructed in dependency order: Configuration, Logger, Event Bus, Service Registry, Lifecycle Manager, Knowledge Service, Memory Service, Scheduler, Intent Router, Workflow Engine, Conversation Manager, Capability Registry, Plugin Manager, Intent Dispatcher, Planner, Knowledge Graph, Memory Integration, Reasoning Engine, Decision Engine, Agent Runtime, Connector Manager, Cognitive Pipeline, Capability Executor, Execution Engine, Response Engine, Agent Service.
- **A further set of packages that are deliberately not services** — passive value objects, transport objects, or builders with no lifecycle of their own: Cognitive Context (022), Planning Session (023), Execution Trace (028), Task Model (029), Task Relationships (031), Capability Context (035), Project/Workspace/Goal Frameworks (036–038), Decision Records/Policy/Automation Frameworks (039–041).
- Every package has a canonical framework document at `factory/packages/0XX_*.md`, **except 003–006** (Event Bus, Service Registry, Service Lifecycle, Knowledge Service) — the code and dated history exist, the design docs do not. Open item, not yet resolved.
- 124 test files, ~2,728 tests, spanning the full 001–041 range.

Each service's own lifecycle-adoption question (whether it implements `IService`) is governed by `design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md` — currently `Proposed`, not `Accepted`; do not treat it as settled.

---

## Modules: What's In Progress

**Sales** (`argus/modules/sales/`) — an AI Sales Operating System for a packaging salesperson. Architecture: see the Sales OS V1 architecture document (Canon-adjacent, not a numbered Core package). Sprint 1 scope: Lead Workspace foundation only — no browser automation, no live Dynamics sync yet.

Progress, updated as work lands:
- Lead value object (`argus/modules/sales/leads/`) — built, tested, verified.
- Contact, Company, Campaign, WorkItem — in progress.
- Plugin registration, spreadsheet importer, work queue, session persistence — not yet started.

---

## Repository Conventions

- **Framework documents are canonical** (`design/decisions/0003_FRAMEWORK_DOCUMENTS_AS_CANONICAL_SOURCE.md`). A package's design rationale lives in `factory/packages/0XX_*.md`, never duplicated into the package itself — see `factory/standards/FRAMEWORK_DOCUMENT_LOCATION_CONVENTION.md` for the pointer pattern.
- **Value objects follow one consistent shape** across every package: a frozen dataclass with every field defaulted, a dedicated Metadata value object (`created_at`/`version`/`correlation_id`/`extra`), a separate mutable Builder doing all validation, and an ABC interface the Builder implements. See `argus/task/` for the canonical example.
- **Reasoning, Decision, and Implementation stay separable** throughout the codebase (ADR-0003) — why, what, and how are never collapsed into one artifact.

---

## Known Gaps (Tracked, Not Yet Resolved)

- `factory/packages/003–006` design docs missing (code exists).
- `design/decisions/0002` (IService Adoption Criterion) still `Proposed`.
- Seven pre-Factory prototype files (`argus/ai.py` and siblings) retired in content per `design/decisions/0004_REMOVE_LEGACY_PROTOTYPE.md`, but not yet physically removed from the tree — this session's sandbox does not permit file deletion.
- Priority 1 (migrating `argus/reasoning`/`argus/decision` toward the Reasoning Engine's full specification) not yet implemented.
