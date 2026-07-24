# Implementation Package 007 - Memory Service

## Objective

Build ArgusOS's short-term, expiry-aware memory layer: the working-memory
counterpart to Package 006's durable Knowledge Service, and the declared
Required Dependency that unblocks Atlas (per design/specifications/ATLAS.md's
"Required: Memory Service, Event Bus, Logging, Configuration").

---

## Why Package 007, Not an Alternative

A dependency-graph audit of every unimplemented engine in
design/specifications/ was performed before selecting this package. Required
Dependencies, as stated in each spec file:

| Engine | Required Dependencies | Satisfied today? |
|---|---|---|
| Memory | Logging, Configuration, Event Bus | Yes - all three exist (Packages 002, 003) |
| Sentinel | Event Bus, Logging, Configuration | Yes - all three exist |
| Atlas | **Memory Service**, Event Bus, Logging, Configuration | No - blocked on Memory |
| Scheduler | Event Bus, **Navigator**, Logging, Configuration | No - blocked on Navigator |
| Hermes | **Cortex**, Event Bus, Logging, Configuration | No - blocked on Cortex |
| Navigator | **Cortex**, **Hermes**, Event Bus, **Scheduler**, Logging, Configuration | No - blocked on three engines |
| Cortex | No specification file exists in design/specifications/ | No - cannot implement without inventing architecture |

Memory and Sentinel are the only two engines whose full dependency list is
already satisfied. Between them, Memory was chosen because:

- Atlas explicitly requires Memory Service before Atlas can be built, and
  Atlas is itself required by both Hermes and Cortex's eventual design.
  Building Memory is the next concrete step on the critical path toward
  every reasoning-capable engine (Atlas, then eventually Cortex). Sentinel
  has no current consumer: nothing in the running system yet executes
  autonomous actions for Sentinel to govern, since Navigator and Hermes do
  not exist. Building Sentinel now would be building a control ahead of
  anything it controls.
- `EventType.MEMORY_UPDATED` has been present, reserved, and unused in
  `argus/events/event_types.py` since Package 003 - the same signal that
  correctly anticipated Package 006's `KNOWLEDGE_*` events. No comparable
  Sentinel event type is reserved anywhere in the codebase.
- Desktop automation and LLM/external integration both map to engines
  (Navigator and Hermes, respectively) that are explicitly blocked on Cortex,
  which has no specification file at all. Building either now would mean
  inventing the missing Cortex contract implicitly, which conflicts with
  this project's standing rule: implement architecture faithfully, never
  invent it.
- A generic "Vision" package was considered and rejected: every named
  engine in design/specifications/ already operationalizes the long-term
  vision (business management, workflow automation, desktop interaction).
  None of them is ready to build except Memory and Sentinel, for the
  reasons above.

---

## Scope

Implement:

- `MemoryRecord`: an immutable value object with an optional `expires_at`,
  the one field that distinguishes it from Package 006's `KnowledgeRecord`
  and gives Memory Service its distinct, non-overlapping responsibility.
- `IMemoryStorage` / `JSONMemoryStorage`: single-file JSON persistence
  (`memory/memory_store.json`), atomic writes, mirroring Package 006's
  storage pattern without depending on `argus.knowledge`.
- `IMemoryService` / `MemoryService`: put / get / exists / delete / update /
  list / search / purge_expired. Expired records are treated as absent by
  every read path (lazy filtering) but are only physically removed by an
  explicit `purge_expired()` call - no background thread, no timer, per the
  "no timers, no background workers" principle already established for the
  Lifecycle Manager (Package 005) and the Event Bus (Package 003).
- Registration of Memory Service as ArgusOS's seventh core service in
  `argus/bootstrap.py`, immediately after the Knowledge Service.

## Specifications Referenced

- design/specifications/MEMORY.md
- design/specifications/INTERFACES.md
- design/specifications/EVENT_BUS.md
- factory/packages/006_KNOWLEDGE_SERVICE.md (precedent pattern)
- factory/standards/CODING_STANDARD.md

---

## Files to Create

argus/memory/
    __init__.py
    exceptions.py
    memory_record.py
    interfaces.py
    storage.py
    memory_service.py

memory/
    memory_store.json

tests/
    test_memory_record.py
    test_memory_storage.py
    test_memory_service.py

---

## Files to Modify

- argus/bootstrap.py (construct and register Memory Service as the seventh
  core service; bump CORE_SERVICES_VERSION to "0.0.7")
- tests/test_bootstrap.py (extend core-service assertions to seven services)
- CHANGELOG.md, DEVLOG.md, factory/ROADMAP.md

---

## Acceptance Criteria

- `python main.py` starts and shuts down cleanly.
- All pre-existing tests continue to pass.
- Memory Service resolves from the Container and appears in the Service
  Registry and Lifecycle Manager (LifecycleState.REGISTERED), alongside the
  six existing core services.
- put / get / exists / delete / update / list / search / purge_expired all
  behave per this document and design/specifications/MEMORY.md.
- Every successful mutation publishes `EventType.MEMORY_UPDATED` on the
  Event Bus, with an `operation` field in the payload distinguishing
  created / updated / deleted / purged.
- Data persists across `MemoryService` instances (survives a process
  restart), matching Package 006's persistence guarantee.

---

## Out of Scope

- Semantic search (Atlas's Future Enhancements, not Memory's).
- Cross-application memory sharing (Memory's own Future Enhancements).
- Automatic background expiry sweeping (explicitly deferred; see Scope).
- Retrofitting `IService` onto Memory Service or any other core service.
  This is a real, separate architectural question (each `IService`
  implementer would track its own internal `LifecycleState`, alongside the
  Lifecycle Manager's per-name tracking - structurally the same kind of
  duplicate-state risk the Package 005 revision eliminated for
  `ServiceDescriptor`). Adopting `IService` deserves its own dedicated,
  explicitly-scoped package and decision, not an incidental side effect of
  Package 007.
