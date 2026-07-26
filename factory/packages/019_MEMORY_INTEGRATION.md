# Implementation Package 019 - Memory Integration

## Objective

Give ArgusOS a controlled bridge between two systems that already
exist independently - the Memory Service (Package 007) and the
Knowledge Graph (Package 018) - so that memory records can become
semantic knowledge through explicit, on-demand synchronization,
without changing either system's own responsibilities. Per the
Founder's Package 019 work order: "This package owns the bridge - not
memory, not knowledge."

```
Conversation -> Memory Service -> Memory Integration -> Knowledge Graph -> Planner -> Validated Plan -> Agent Runtime
```

Memory Integration is the only component responsible for translating
memory records into graph entities and relationships. It stores
nothing itself beyond lightweight synchronization bookkeeping (see
Architectural Decision 6).

---

## Specification Note

No `design/specifications/MEMORY_INTEGRATION.md` exists in the
repository - the same situation as Packages 002, 009-018. This
package is built directly from the Founder's explicit work order.

---

## Mapper Architecture

`MemoryMapper` (`argus/memory_integration/mapper.py`) performs pure,
side-effect-free translation only - it never calls `IMemoryService` or
`IKnowledgeGraph`:

```
memory_to_entity(record)        -> Entity   (fresh; id = f"memory:{key}")
memory_to_relationship(record)  -> Sequence[Relationship]  (from "related_keys")
update_entity(existing, record) -> Entity   (same id, refreshed attributes)
remove_entity(key)              -> str      (the deterministic entity id for `key`)
```

Every Entity `MemoryMapper` produces for a given memory `key` carries
the id `f"memory:{key}"` - a pure function of the key alone (see
Architectural Decision 1). `memory_to_relationship()` recognizes
exactly one simple, mechanical convention: if `record.value` is a
Mapping with a `"related_keys"` entry (an iterable of strings), each
entry becomes one `Relationship` (`relationship_type="related_to"`)
from this record's Entity to the referenced key's Entity. A record
with no such convention produces no Relationships - the default,
common case, not an error (see Architectural Decision 2).

---

## Synchronization Lifecycle

```
       synchronize_memory(key)
                |
                v
       record = memory_service.get(key)   [InvalidMemoryRecordError if unknown]
                |
                v
       candidate = mapper.memory_to_entity(record)   [id = f"memory:{key}"]
                |
                v
       existing = graph.get_entity(candidate.id)?
          |                              |
        found                       not found
          |                              |
          v                              v
   graph.remove_entity(existing.id)   (nothing to remove)
   [cascades away every Relationship  final_entity = candidate
    referencing this Entity - see
    Package 018's own Cascading
    Removal]
   final_entity =
     mapper.update_entity(existing, record)
          |                              |
          +--------------+---------------+
                         |
                         v
              graph.add_entity(final_entity)
                    |            |
                 succeeds      raises
                    |            |
                    v            v
          --publish        --publish MEMORY_MAPPING_FAILED--
          MEMORY_           (raise MemoryMappingError)
          SYNCHRONIZED--
                    |
                    v
     for relationship in mapper.memory_to_relationship(record):
         try: graph.add_relationship(relationship)   (best-effort;
         except: publish MEMORY_MAPPING_FAILED         does not raise,
                 (continue)                             does not undo
                                                         the Entity sync)

       remove_memory(key)
                |
                v
       entity_id = mapper.remove_entity(key)   [pure - no lookup needed]
                |
                v
       key in self._synchronized?  -> no: raise MemoryNotSynchronizedError
                |
              yes
                |
                v
       graph.remove_entity(entity_id)   [tolerates EntityNotFoundError -
                                          bookkeeping still clears]
                |
                v
       --publish MEMORY_DESYNCHRONIZED--

       synchronize_all()
                |
                v
       for record in memory_service.list():
           try: synchronize_memory(record.key)   (one failure does not
           except MemoryIntegrationError: continue  abort the batch)
                |
                v
       return the keys that succeeded
```

Every `synchronize_memory(key)` call is fully idempotent: the same key
always resolves to the same Entity id, so re-synchronizing never
creates a duplicate, and always reconciles the Entity (and its
Relationships) to the record's *current* state - see Architectural
Decision 3.

---

## Dependency Graph

```
MemoryIntegration
    depends on -> IEventBus         (publish synchronization events)
    depends on -> IMemoryService    (read-only: get() / list())
    depends on -> IKnowledgeGraph   (add_entity / remove_entity /
                                      get_entity / add_relationship)

MemoryIntegration does NOT depend on:
    argus.planner     (Planner is never referenced or modified)
    argus.runtime     (AgentRuntime is never referenced or modified)
    argus.dispatcher  (IntentDispatcher is never referenced)
    argus.plugins     (PluginManager is never referenced)
    argus.capability  (CapabilityRegistry is never referenced)
    argus.workflow    (WorkflowEngine is never referenced)
    argus.connectors  (ConnectorManager is never referenced)
```

Construction order in `bootstrap.py` follows the Bootstrap section's
explicit sequence - Capability Registry -> Intent Dispatcher ->
Planner -> Knowledge Graph -> Memory Integration -> Agent Runtime ->
Connector Manager - with Memory Integration inserted between the
Knowledge Graph and the Agent Runtime. Unlike the Knowledge Graph's
and Connector Manager's own purely positional placements (Packages
017-018), this one **is** dependency-driven: Memory Integration
genuinely needs live `IMemoryService` and `IKnowledgeGraph` references
to do its job at all, and both must already exist by construction
time (Memory Service since step 8; Knowledge Graph since the
immediately preceding step).

---

## Architectural Decisions

### 1. Deterministic `f"memory:{key}"` Entity ids, with no separate lookup table

"Prevent duplicate graph entities" needs some way to recognize "this
memory key already has a graph Entity." Rather than maintaining a
separate id-lookup table (which would risk becoming a second,
competing source of truth - see Decision 6), `MemoryMapper` derives
every Entity's `id` purely from the memory `key`: `f"memory:{key}"`.
The same key always produces the same id, so re-synchronizing
naturally resolves to the same Entity, and `remove_memory(key)` can
compute the id to remove directly from a bare key string, without
first needing to fetch a (possibly already-deleted) MemoryRecord.

### 2. `related_keys` is the only relationship convention recognized

`MemoryRecord.value` is untyped `Any` with no relationship concept of
its own, and this package "shall NOT perform graph reasoning."
Rather than attempting any inference, `memory_to_relationship()`
recognizes exactly one simple, mechanical convention: `value` is a
Mapping with a `"related_keys"` entry (an iterable of strings). This
is parsing a well-known field name, not reasoning - a record without
this convention simply produces no Relationships, the default case.

### 3. Synchronization is reconcile, not merge: remove-then-rebuild on every call

`IKnowledgeGraph` has no `update_entity()` method (Package 018's own
closed method list: only `add_entity`/`remove_entity`). Rather than
extending `KnowledgeGraph`'s own contract (out of this package's
scope - "not... knowledge"), `synchronize_memory()` treats every call
as a full reconciliation: if the Entity already exists, remove it
(which cascades away its stale Relationships, per Package 018) and
rebuild it and its current Relationships fresh from the record's
present state. This single mechanism satisfies both "prevent duplicate
graph entities" and "synchronize updates" without a separate code path
for either - see Known Limitations for the resulting, load-bearing
consequence for *other* entities' inbound Relationships.

### 4. Entity-level failures raise; Relationship-level failures are best-effort

`add_entity()` failing means the primary translation itself failed -
`synchronize_memory()` raises `MemoryMappingError` in that case (after
publishing `MEMORY_MAPPING_FAILED`). A `related_keys` entry pointing
at an unsynchronized key, by contrast, is expected and common (order
of synchronization is not guaranteed) - each relationship is attempted
independently, a failure publishes `MEMORY_MAPPING_FAILED` and moves
on, and does not undo the Entity sync that already succeeded in the
same call, per "graph consistency."

### 5. `synchronize_all()` is best-effort across the whole batch

One record's failure must not prevent every other record's
synchronization. `synchronize_all()` calls `synchronize_memory()` per
record, catching and continuing past any `MemoryIntegrationError` -
the failure is already recorded in `synchronization_status()` and
published as `MEMORY_MAPPING_FAILED` by `synchronize_memory()` itself.

### 6. "It owns no data itself": exactly two small bookkeeping dicts, cleared by `reset()`, touching neither dependency

`MemoryIntegration` keeps `self._synchronized` (key -> Entity id) and
`self._failed` (key -> last failure message) purely to support
`synchronization_status()` and idempotent re-synchronization - neither
is a competing copy of memory values or graph structure (Entity ids
are always recoverable via Decision 1's own deterministic scheme
without this bookkeeping at all). `reset()` clears only these two
dicts - it does not remove anything from the Memory Service or the
Knowledge Graph, matching this package's explicit "It owns no data
itself" and "not memory, not knowledge" boundary. This mirrors the
same "lightweight bookkeeping, not a competing source of truth"
category already established by `AgentRuntime`'s Execution tracking
(016) and `ConnectorManager`'s Connector-metadata tracking (017).

### 7. `synchronization_status()`, not `status()` - an unavoidable naming collision

This package's own Responsibilities list `status()` as one of
`MemoryIntegration`'s five methods, but `IService.status()` is already
a fixed abstract method returning `LifecycleState`, used identically
by every other `IService` adopter in this codebase. A method cannot
satisfy two incompatible contracts under one name without breaking
Liskov substitution for any caller treating `MemoryIntegration`
polymorphically as an `IService`. Resolved by naming the domain method
`synchronization_status()` instead, preserving `status()` exclusively
for lifecycle reporting everywhere in this codebase, with no
exception - a deliberate, necessary deviation from the work order's
literal method name, forced by a collision between two of that same
work order's own instructions ("Extend IService" and "status()" as a
domain Responsibility).

### 8. `IMemoryIntegration` inherits `IService`, and this time the criterion agrees

Like Package 018, this package's work order explicitly instructs
"Extend IService" - not a judgment call. Unlike Package 018, applying
ADR-0002's criterion *independently* to this package's actual methods
would also have suggested adoption: `synchronize_memory()`/
`synchronize_all()`/`remove_memory()` each perform genuine, effectful
cross-system coordination (reading `IMemoryService`, writing
`IKnowledgeGraph`, in the same call) - closer to
`AgentRuntime.start_execution()`/`ConnectorManager.invoke()` than to
`KnowledgeGraph`'s own single-system operations. These three methods
are gated on `RUNNING`; `synchronization_status()`/`reset()` remain
ungated. See `design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`'s
newly appended Empirical Finding, which records this as the first case
where an explicit instruction and the criterion's own independent
conclusion agree, directly contrasting with Package 018's divergent
case.

---

## Events

Exactly the three event types this package's own Events section
names: `MEMORY_SYNCHRONIZED`, `MEMORY_DESYNCHRONIZED`,
`MEMORY_MAPPING_FAILED`. `MEMORY_SYNCHRONIZED` fires once per
successful `synchronize_memory()` call, regardless of whether any of
that record's Relationships also succeeded. `MEMORY_MAPPING_FAILED`
fires for both Entity-level failures (which also raise
`MemoryMappingError`) and individual Relationship-level failures
(which do not raise). `MEMORY_DESYNCHRONIZED` fires once per
successful `remove_memory()` call. None of the three fire for a
failure that occurs before any Memory Service or Knowledge Graph call
is attempted (for example, an unknown key).

---

## IService Adoption

`IMemoryIntegration` DOES inherit `IService`, per this package's own
explicit work order instruction. Unlike Package 018's Knowledge Graph,
applying ADR-0002's criterion independently to this package's actual
methods would also have suggested adoption on its own -
`synchronize_memory()`, `synchronize_all()`, and `remove_memory()` are
genuinely gated on the `RUNNING` state; `synchronization_status()` and
`reset()` remain ungated. See Architectural Decisions 7-8 and
`design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`'s newly
appended Empirical Finding for the full reasoning, including the
observation that Packages 018 and 019 together give ADR-0002 its
first paired evidence that "directed" and "derived" IService adoption
are separate questions that can agree or disagree independently of one
another.

---

## Repository Verification Note

The uploaded repository ("ArgusOS (18).zip") was verified against this
package's own general "verify repository state, verify version
consistency, run smoke validation" pre-flight instruction. Findings:
HEAD (`680e729`, "Synchronize repository version with v0.1.8 release")
is a clean, single-commit descendant of tag `v0.1.8` (which points to
`8fe244e`, "Implement Package 018 Knowledge Graph"); `git diff
v0.1.8..HEAD --stat` shows exactly 1 file changed (`argus/bootstrap.py`,
1 insertion/1 deletion) - a minimal, standard version-only sync, no
anomaly. `git status --short` showed a completely clean working tree.
`argus/knowledge_graph/` (Package 018) present with all expected
files; `python -m pytest` passing (1055 passed, 38 subtests); `python
-m unittest discover -s tests` passing (967); `python main.py`
starting and shutting down cleanly (exit 0); `CORE_SERVICES_VERSION ==
"0.1.8"` matching tag `v0.1.8`. All confirmed before any Package 019
code was written.

---

## Files Created

```
argus/
    memory_integration/
        __init__.py
        mapper.py
        integration.py
        interfaces.py
        exceptions.py
tests/
    test_memory_mapper.py
    test_memory_integration.py
```

## Files Modified

```
argus/bootstrap.py            (construct + register Memory Integration
                                as 19th core service, inserted between
                                the Knowledge Graph and the Agent
                                Runtime, per the Bootstrap section's
                                explicit, dependency-driven
                                construction order; CORE_SERVICES_
                                VERSION left at "0.1.8" - not advanced
                                by this package)
argus/events/event_types.py   (3 new event types)
argus/tests/test_bootstrap.py (CORE_SERVICE_NAMES tuple only, per the
                                standing Package 011 rule)
tests/test_bootstrap.py       (CORE_SERVICE_NAMES tuple + 3 new tests)
design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md (Empirical Finding
                                appended; Status remains Proposed)
CHANGELOG.md, DEVLOG.md, IMPLEMENTATION_REPORT.md, factory/ROADMAP.md
```

`argus/memory/`, `argus/knowledge_graph/`, `argus/planner/`,
`argus/runtime/`, `argus/dispatcher/`, `argus/capability/`,
`argus/workflow/`, `argus/plugins/`, and `argus/connectors/` are
unchanged - Memory Integration consumes the Memory Service's and
Knowledge Graph's existing, unmodified public interfaces only.

---

## Test Totals

1,031 tests passing via `python -m unittest discover -s tests` (967
from Packages 002-018, plus 20 new in `test_memory_mapper.py`, 41 new
in `test_memory_integration.py`, and 3 new in `test_bootstrap.py`
[32->35]). `python -m unittest discover -s argus/tests` remains at 64
(duplicate tree unaffected beyond the standing `CORE_SERVICE_NAMES`
sync). `python -m pytest` also passes: 1,119 passed, 38 subtests
passed.

---

## Coverage

100% line coverage on every new/modified module measured for this
package: `argus/memory_integration/__init__.py`,
`argus/memory_integration/mapper.py`,
`argus/memory_integration/integration.py`,
`argus/memory_integration/interfaces.py`,
`argus/memory_integration/exceptions.py`, `argus/bootstrap.py`, and
`argus/events/event_types.py` - all 100%, no accepted gaps. Overall
repository coverage: 99% (unchanged from Package 018; remaining gaps
are pre-existing and out of scope).

---

## Known Limitations

- **Resynchronizing an Entity can silently drop *inbound* Relationships
  created by other entities' syncs.** `synchronize_memory(key)`
  rebuilds only `key`'s own outgoing Relationships (from its current
  `related_keys`) after a remove-then-rebuild cycle; a Relationship
  that another entity C pointed at this one (C -> this Entity) is
  cascade-removed along with the old Entity and is *not* restored
  unless C is also resynchronized. This is a genuine, load-bearing
  consequence of Architectural Decision 3, not an oversight - reversing
  it would require MemoryIntegration to track reverse (inbound)
  references for every Entity, a form of bookkeeping well beyond
  "infrastructure only" Version 1 scope.
- **No persistence** - `self._synchronized`/`self._failed` bookkeeping
  is held only in memory; nothing survives a process restart (the
  underlying Memory Service and Knowledge Graph have their own,
  independent persistence characteristics, unaffected by this).
- **No AI reasoning, no graph inference** - `related_keys` is the only
  relationship signal recognized; nothing is inferred from a record's
  `value` beyond that one convention.
- **No vector search** - out of scope, per this package's Constraints.
- **`synchronize_all()` order follows `IMemoryService.list()`'s own
  order**, which is not guaranteed - a record whose `related_keys`
  references a not-yet-synchronized key will have that specific
  Relationship fail (published as `MEMORY_MAPPING_FAILED`) on this
  pass; a subsequent `synchronize_all()` call resolves it once both
  keys have been synchronized at least once.
- No concurrency - all operations are synchronous, single-threaded,
  single-process.
- The repository's stray `argus/` duplicate tree (beyond the one
  explicitly-required `test_bootstrap.py` sync) and legacy pre-Factory
  files remain unresolved, out of scope per the Founder's explicit
  repository rules.

---

## Future Expansion

- Track inbound references (or adopt a non-destructive update
  mechanism on `IKnowledgeGraph` itself, in a future package explicitly
  scoped to revisit its contract) to resolve the resynchronization
  limitation above.
- Add a scheduled or event-driven trigger for `synchronize_all()`
  (for example, on `MEMORY_UPDATED`), rather than requiring an
  explicit caller - out of this package's "infrastructure only" scope.
- Recognize additional relationship conventions beyond `related_keys`,
  if a future package's Responsibilities call for them.
- Revisit whether ADR-0002 should formally separate "adoption"
  (directed or derived) from "gating" (always criterion-driven), per
  this package's own newly appended Empirical Finding.

---

## Release Rules

Per the Founder's explicit instruction: no commit, tag, or push was
performed. `CORE_SERVICES_VERSION` was not changed by this package -
it remains `"0.1.8"`. This package is not reported as complete or
released - implementation ends after successful local verification;
final validation, integration, release, version update, commit, and
tag are the Founder's responsibility against the live repository.
