# ArgusOS Implementation Report — Package 007: Memory Service

## 1. Package Overview

Package 007 adds `argus/memory/`, ArgusOS's short-term, expiry-aware working-memory layer. `MemoryService` provides create/read/update/delete/search access to `MemoryRecord` value objects, persisted as a single JSON file (`memory/memory_store.json`) via `JSONMemoryStorage`, with every write atomic (temp file + `os.replace`) and protected by a write lock. Every record may carry an optional `expires_at`; expired records are invisible to every read path (`get`/`exists`/`list`/`search`) without being physically deleted, and an explicit `purge_expired()` removes them. `MemoryService` publishes `EventType.MEMORY_UPDATED` (reserved since Package 003, unused until now) on every successful mutation, and is registered as ArgusOS's seventh core service. All 140 pre-existing tests still pass; 56 new tests were added (196 total), all passing under `python -m unittest discover`. No pytest anywhere. `python main.py` starts and shuts down cleanly.

## 2. Architectural Rationale

Before selecting a target, every unimplemented engine in `design/specifications/` (Atlas, Cortex, Hermes, Navigator, Scheduler, Sentinel, Memory) was audited against its own stated Required Dependencies:

| Engine | Required Dependencies | Satisfied today? |
|---|---|---|
| Memory | Logging, Configuration, Event Bus | Yes |
| Sentinel | Event Bus, Logging, Configuration | Yes |
| Atlas | **Memory Service**, Event Bus, Logging, Configuration | No |
| Scheduler | Event Bus, **Navigator**, Logging, Configuration | No |
| Hermes | **Cortex**, Event Bus, Logging, Configuration | No |
| Navigator | **Cortex**, **Hermes**, Event Bus, **Scheduler**, Logging, Configuration | No |
| Cortex | No specification file exists in `design/specifications/` | No |

Memory and Sentinel are the only two engines whose full dependency list is already satisfied by what's actually built. Memory was chosen over Sentinel because it sits on the critical path — Atlas's spec explicitly names Memory Service as a Required Dependency, so building Memory is the next concrete step toward every reasoning-capable engine ArgusOS will eventually need. Sentinel currently has nothing to govern: no engine that executes autonomous action (Navigator, Hermes) exists yet, so a security/governance layer would be built ahead of anything it protects. `EventType.MEMORY_UPDATED` has also sat reserved and unused in `argus/events/event_types.py` since Package 003 — the same kind of signal that correctly anticipated Package 006's `KNOWLEDGE_*` events.

The full audit, including the reasoning below, is recorded in `factory/packages/007_MEMORY_SERVICE.md`, this package's formal work order, so the decision is part of the repository's permanent record, not just this report.

## 3. Why Not the Alternatives

**Why not "Vision" as a package?** Every named engine in `design/specifications/` already operationalizes the long-term vision (business management, workflow automation, desktop interaction, communication). "Vision" isn't a buildable unit; it's the sum of these engines. The real question was which named engine to build next, answered by the dependency audit above.

**Why not Desktop Automation?** This maps to Navigator ("Argus's execution engine... invoking tools, monitoring execution"). Navigator's Required Dependencies are Cortex, Hermes, Event Bus, Scheduler, Logging, Configuration — three of which (Cortex, Hermes, Scheduler) don't exist. Building Navigator now would mean either inventing those three engines' contracts implicitly or building an execution engine with nothing to execute plans from and no scheduler to trigger it.

**Why not LLM Integration?** This maps most closely to Hermes ("Argus's communication engine... interface with external APIs") or, further out, Cortex itself. Hermes's Required Dependencies include Cortex, which has no specification file anywhere in the repository — not even a draft. Building Hermes or anything Cortex-adjacent now would require inventing Cortex's contract from scratch, directly conflicting with this project's standing rule to implement architecture faithfully rather than invent it.

**Why is Memory the highest-leverage next step?** It's the only engine that is simultaneously (a) fully unblocked today, (b) explicitly required by the next engine after it (Atlas), and (c) already signaled in the codebase itself via the reserved `MEMORY_UPDATED` event type. Every other viable path either invents missing architecture (Cortex-adjacent work) or builds a capability with no current consumer (Sentinel).

## 4. Directory Tree

```
argus/
    memory/
        __init__.py
        exceptions.py
        interfaces.py
        memory_record.py
        memory_service.py
        storage.py
    bootstrap.py                       (modified)
memory/
    memory_store.json                  (new, seeded [])
factory/
    packages/
        007_MEMORY_SERVICE.md          (new)
    ROADMAP.md                         (modified)
tests/
    test_bootstrap.py                  (modified)
    test_memory_record.py              (new)
    test_memory_service.py             (new)
    test_memory_storage.py             (new)
CHANGELOG.md                           (modified)
DEVLOG.md                              (modified)
```

## 5. Complete Source Code / 6. Complete Unit Tests

Delivered as file cards alongside this report (all 16 files, repository-structured, no ZIP, no `.git`). Every module carries full Purpose/Responsibilities/Non-Responsibilities/Dependencies docstrings and type hints throughout, per `factory/standards/CODING_STANDARD.md`.

## 7. Integration Notes

- `MemoryService(storage: IMemoryStorage, event_bus: IEventBus)` — constructed in `bootstrap.py` immediately after the Knowledge Service, since it depends only on the Event Bus (already constructed by that point).
- Registered in the Container as `"memory_service"`, in the Service Registry as a `ServiceDescriptor` (version `"0.0.7"`), and in the Lifecycle Manager as `LifecycleState.REGISTERED` — exactly matching the treatment of all six prior core services. Not initialized or started (see Engineering Decisions).
- No changes to `argus/events/event_types.py`: `EventType.MEMORY_UPDATED` already existed and was reused, with an `operation` field (`created`/`updated`/`deleted`/`purged`) in the event payload distinguishing the mutation kind.
- Fully backward compatible: no existing public interface, method signature, or stored data format was changed. `CORE_SERVICES_VERSION` bumped `"0.0.6"` → `"0.0.7"`, matching the version-target convention established in every prior package.
- Deliberately does **not** depend on `argus.knowledge` in any direction, despite the structural similarity between `JSONMemoryStorage` and `JSONKnowledgeStorage` — the two packages stay decoupled, per "no unnecessary dependencies."

## 8. Merge Instructions

1. Copy `argus/memory/` into the repository's `argus/` directory.
2. Copy `memory/memory_store.json` into the repository root.
3. Copy `factory/packages/007_MEMORY_SERVICE.md` into `factory/packages/`.
4. Replace `argus/bootstrap.py` with the version in this delivery.
5. Replace `tests/test_bootstrap.py` with the version in this delivery.
6. Copy `tests/test_memory_record.py`, `tests/test_memory_service.py`, `tests/test_memory_storage.py` into `tests/`.
7. Append the Package 007 sections already included in the delivered `CHANGELOG.md` and `DEVLOG.md` (or replace the files outright — they are cumulative supersets of your current versions through Package 006).
8. Replace `factory/ROADMAP.md` with the version in this delivery.
9. Run `python -m unittest discover` — expect `Ran 196 tests ... OK`.
10. Run `python main.py` — expect a clean start/shutdown log with exit code 0.
11. Tag the result `v0.0.7`.

## 9. Expected Test Count After Merge

**196 tests** (140 existing + 56 new): 13 in `test_memory_record.py`, 12 in `test_memory_storage.py`, 30 in `test_memory_service.py`, 1 added to `test_bootstrap.py`.

## 10. Engineering Decisions

- **Expiry differentiates Memory from Knowledge.** Both packages are JSON-backed, versioned, event-publishing CRUD stores; `expires_at` is the one field `KnowledgeRecord` doesn't have, and it's the basis for a clean, non-overlapping responsibility split: Memory = short-term/working data, Knowledge = durable, human-curated facts.
- **Lazy expiry, no background thread.** `get`/`exists`/`list`/`search` filter out expired records without mutating storage; only `purge_expired()` performs physical deletion, under the write lock. This keeps Memory Service consistent with the "no timers, no background workers" principle already established for the Event Bus and Lifecycle Manager.
- **`IService` adoption deliberately deferred.** Every `IService` implementer must track its own internal `LifecycleState` (required by `status()`), alongside whatever the Lifecycle Manager tracks by name for that same service — structurally the same duplicate-state shape the Package 005 revision eliminated for `ServiceDescriptor`. Adopting `IService` for the first time is a real architectural decision that deserves its own dedicated package, not an incidental side effect of a data-service package. `MemoryService` is registered `REGISTERED`-only, like every other core service to date.
- **Reused `EventType.MEMORY_UPDATED` rather than adding new members.** A single event type with an `operation` payload field covers create/update/delete/purge without touching `event_types.py` — a smaller footprint than Package 006's approach, and a direct response to the "only expected new files should appear" tension flagged in that package's report.
- **Exception base named `MemoryServiceError`, not `MemoryError`**, to avoid shadowing Python's built-in `MemoryError`.

## 11. Deviations from Established Pattern

None. This package follows the Container/DI, Event Bus, interface-first, and testing conventions established in Packages 002–006 exactly.

## 12. Test Results

```
Ran 196 tests in 0.024s
OK
```

`python main.py`:
```
2026-07-24 10:19:44 [INFO] argus: ArgusOS application started.
2026-07-24 10:19:44 [INFO] argus: ArgusOS application shutting down.
```
Exit code 0.

## 13. Coverage Summary

Measured with `coverage.py`, `python -m coverage run -m unittest discover`:

| Module | Stmts | Miss | Cover |
|---|---|---|---|
| `argus/bootstrap.py` | 37 | 0 | 100% |
| `argus/memory/__init__.py` | 6 | 0 | 100% |
| `argus/memory/exceptions.py` | 3 | 0 | 100% |
| `argus/memory/interfaces.py` | 25 | 0 | 100% |
| `argus/memory/memory_record.py` | 18 | 0 | 100% |
| `argus/memory/memory_service.py` | 83 | 0 | 100% |
| `argus/memory/storage.py` | 49 | 5 | 90% (lines 100-101, 116-117, 122 — `os.replace` failure and temp-file cleanup branches) |

Package 007 total: 221 statements, 98% covered. Full repository (`argus/*`): 724 statements, 97% covered.

## 14. Known Limitations

- `MemoryService` does not implement `IService`; registered but not initialized/started (deliberate, see Section 10).
- Expired-but-unpurged records remain physically on disk until `purge_expired()` is called.
- `search()` is a case-insensitive substring match on `key`, not semantic search.
- Two OS-failure branches in `JSONMemoryStorage.save` are untested (require mocking filesystem failures).

## 15. Repository-Derived Package Metrics (measured, not estimated)

Measured via `git diff --stat/--numstat/--name-status HEAD~2 HEAD` (commits `708630e` + `820a0c2` on top of `a7ce8d6`):

- Files Created: 11 (6 `argus/memory/*.py`, `memory/memory_store.json`, `factory/packages/007_MEMORY_SERVICE.md`, 3 new test files)
- Files Modified: 5 (`argus/bootstrap.py`, `tests/test_bootstrap.py`, `CHANGELOG.md`, `DEVLOG.md`, `factory/ROADMAP.md`)
- Lines Added: 1,341
- Lines Removed: 27
- Unit Tests: 196 passing (56 new)
- Coverage: 98% (Package 007 modules), 97% (full repository)
- Public Classes: 3 (`MemoryRecord`, `JSONMemoryStorage`, `MemoryService`)
- Public Interfaces: 2 (`IMemoryStorage`, `IMemoryService`)
- New Dependencies: 0
- External Libraries: 0 (standard library only)
- Technical Debt: 4 items (see Known Limitations)
- Architecture Deviations: 0

## 16. Package-Specific Technical Debt

1. `MemoryService` / `IService` integration deferred to a future, dedicated package decision.
2. No background expiry sweep; relies on explicit `purge_expired()` calls (a natural future integration point once Scheduler exists).
3. `search()` has no semantic capability; deferred to Atlas per its own Future Enhancements.
4. `JSONMemoryStorage.save`'s OS-failure branches lack test coverage.
