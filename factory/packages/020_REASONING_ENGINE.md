# Implementation Package 020 - Reasoning Engine

## Objective

Give ArgusOS a first-generation reasoning layer that consumes
information from the Knowledge Graph (Package 018) and Memory
Integration (Package 019) to produce structured, descriptive reasoning
results for future planners and autonomous agents - "It does not make
decisions. It does not execute plans. It performs deterministic
reasoning only." Per the Founder's Package 020 work order, the Planner
does not consume the Reasoning Engine yet; this package only
introduces the service.

```
Conversation -> Memory Service -> Memory Integration -> Knowledge Graph -> Reasoning Engine -> Planner -> Validated Plan -> Agent Runtime
```

The Reasoning Engine is the only component responsible for answering
structural questions about the graph - entity lookups, relationship
lookups, neighbor traversal, bounded path discovery, and count-based
summaries. It stores nothing itself; every call re-reads the live
Knowledge Graph (and, for descriptive metadata only, Memory
Integration's own synchronization bookkeeping).

---

## Specification Note

No `design/specifications/REASONING_ENGINE.md` exists in the
repository - the same situation as Packages 002, 009-019. This
package is built directly from the Founder's explicit work order.

---

## Query Model

`ReasoningQuery` (`argus/reasoning/query.py`) is an immutable request:

```
entity_type: Optional[str]        - restrict to Entities of this type
relationship_type: Optional[str]  - restrict to Relationships of this type
entity_id: Optional[str]          - resolve and traverse from this Entity
depth: int = 1                    - hops to traverse (only consulted when entity_id is set)
filters: Mapping[str, Any] = {}   - exact-match attribute subset test
```

`query()` interprets these fields across four mutually exclusive
branches, in this priority order (see Architectural Decision 1):

1. `entity_id` set - bounded breadth-first traversal outward from that
   Entity.
2. `entity_id` unset, both `entity_type` and `relationship_type` set -
   a simple graph pattern match.
3. `entity_id` unset, only `entity_type` set - entity type search.
4. `entity_id` unset, only `relationship_type` set - relationship type
   search.

At least one of `entity_id`/`entity_type`/`relationship_type` must be
set; a query with none of the three raises `InvalidReasoningQueryError`
- there is no "return everything" query.

---

## Result Model

`ReasoningResult` (`argus/reasoning/result.py`) is an immutable,
descriptive-only outcome:

```
matched_entities: Sequence[Entity]
matched_relationships: Sequence[Relationship]
reasoning_steps: Sequence[str]   - a factual, mechanical execution trace
metadata: Mapping[str, Any]      - counts, branch taken, path listings, etc.
```

"The result is descriptive only. No confidence scores. No AI-generated
explanations." `reasoning_steps` is never produced by an LLM or any
probabilistic process - both are forbidden outright by this package's
Constraints. `metadata` always includes the injected Memory
Integration's own `synchronization_status()` snapshot (see
Architectural Decision 7).

---

## Engine Architecture

`ReasoningEngine` (`argus/reasoning/engine.py`) implements
`IReasoningEngine` over an injected `IKnowledgeGraph` and
`IMemoryIntegration`:

```
query(reasoning_query)                              -> ReasoningResult
neighbors(entity_id)                                -> ReasoningResult
find_paths(source_entity_id, target_entity_id,
           *, max_depth=3)                           -> ReasoningResult
related_entities(entity_id, *, relationship_type)     -> ReasoningResult
entity_summary(entity_id)                             -> ReasoningResult
relationship_summary(relationship_type)                -> ReasoningResult
```

- `query()`'s `entity_id` branch performs bounded breadth-first
  reachability (bounded by `depth`), then reports every Relationship
  in the induced subgraph over the reachable Entities - not just the
  edges used for discovery (see Architectural Decision 2).
- `neighbors()`/`related_entities()` return an Entity's direct
  (single-hop) connections; `related_entities()` additionally accepts
  an optional `relationship_type` filter.
- `entity_summary()`/`relationship_summary()` return count-based
  descriptive summaries (outgoing/incoming/neighbor counts for an
  Entity; relationship count and distinct endpoint count for a
  relationship type).
- `find_paths()` deterministically enumerates every simple path (no
  repeated Entities) between two Entities, via bounded depth-first
  search, up to an explicit `max_depth` (default 3). An empty result
  means no path exists - not an error (see Architectural Decision 3).

All traversal (the `entity_id` branch of `query()`, and `find_paths()`)
treats every Relationship as traversable in either direction, matching
`IKnowledgeGraph.neighbors()`'s own established "connected... in
either direction" precedent from Package 018.

---

## Reasoning Lifecycle

```
        caller invokes any public method
                    |
                    v
        validate inputs (type/shape/existence)
           |                        |
      invalid                    valid
           |                        |
           v                        v
  REASONING_QUERY_FAILED    read-only IKnowledgeGraph /
    (raise, no result)      IMemoryIntegration calls complete
                                     |
                                     v
                          REASONING_QUERY_EXECUTED
                                     |
                                     v
                       assemble ReasoningResult
                                     |
                                     v
                          REASONING_RESULT_CREATED
                                     |
                                     v
                          return ReasoningResult
```

Every public method follows this same shape (see Architectural
Decision 6): validation failures publish `REASONING_QUERY_FAILED`
alone and raise; successful calls publish `REASONING_QUERY_EXECUTED`
then `REASONING_RESULT_CREATED`, in that order, and return a
`ReasoningResult`. No method mutates the Knowledge Graph, Memory
Integration, or Memory Service - every dependency call is one of that
dependency's own existing read-only methods.

---

## Dependency Graph

```
ReasoningEngine
    depends on -> IKnowledgeGraph      (Package 018; read-only)
    depends on -> IMemoryIntegration   (Package 019; read-only, metadata only)
    depends on -> IEventBus            (Package 003)

Planner
    does NOT depend on ReasoningEngine yet (explicit Version 1 scope limit)

AgentRuntime
    does NOT depend on ReasoningEngine (unchanged from Package 019)
```

Construction order in `bootstrap.py`: Capability Registry -> Intent
Dispatcher -> Planner -> Knowledge Graph -> Memory Integration ->
Reasoning Engine -> Agent Runtime -> Connector Manager. Unlike the
Knowledge Graph's and Connector Manager's own purely-positional
placements (Packages 017-018), this ordering IS dependency-driven,
exactly like Memory Integration's own placement (Package 019):
`ReasoningEngine` genuinely needs live `IKnowledgeGraph` and
`IMemoryIntegration` references, both already constructed by the time
it is built.

---

## Architectural Decisions

### 1. `query()`'s four branches are checked in a fixed priority order, not merged

`entity_id` takes priority over the `entity_type`+`relationship_type`
pattern branch, which takes priority over either type-only branch.
This is a deliberate, simple, fully deterministic rule rather than an
attempt to support every possible field combination uniformly -
`entity_id` implies "traverse from a specific starting point," which
is a fundamentally different operation from "search the whole graph by
type," and conflating the two into one combined algorithm would have
made the branch that actually runs, for a given query, harder to
predict from its fields alone.

### 2. The `entity_id` traversal branch reports the *induced subgraph*, not just discovery edges

`query()`'s bounded BFS collects the set of *reachable* Entity ids
within `depth` hops, then separately computes `matched_relationships`
as every Relationship (of the given `relationship_type`, if any) whose
*both* endpoints are in that reachable set - not just the specific
edges the BFS happened to use to first discover each Entity. This
means a Relationship connecting two already-discovered Entities (for
example, a second, parallel edge, or an edge closing a cycle) is
always included, giving callers the complete local subgraph rather
than an arbitrary spanning tree of it.

### 3. `find_paths()` is exhaustive within `max_depth`, not "first path found"

Every simple path (no repeated Entities) up to `max_depth` hops is
enumerated and returned, not just the shortest one - "No heuristic
algorithms" rules out preferring one path over another by any
criterion, so returning all of them, deterministically ordered by
discovery order, is the only interpretation consistent with
"deterministic reasoning only." A trivial single-Entity path (length
0) is returned when `source_entity_id == target_entity_id`, rather
than treated as degenerate or invalid.

### 4. Simple graph pattern evaluation: entity_type + relationship_type together

When `entity_type` and `relationship_type` are both set (and
`entity_id` is not), `query()` evaluates the pattern "Relationships of
`relationship_type` with at least one endpoint Entity of
`entity_type`" - this is the package's concrete answer to "evaluate
simple graph patterns," a Responsibility with no further specification
in the work order. Matched entities are exactly the endpoints that
satisfy the type constraint (not both endpoints indiscriminately),
keeping the result precise to what was actually asked for.

### 5. Bounded, deterministic multi-hop traversal is now in scope, where it wasn't for Package 018

Package 018's Knowledge Graph was deliberately built with "no graph
traversal algorithms... no shortest path" as an explicit constraint -
but its own wording was "No graph algorithms **yet**," a stated
deferral, not a permanent prohibition on the architecture as a whole.
This package's own explicit `find_paths()` method and "evaluate simple
graph patterns" Responsibility, read together with a Constraints list
that forbids LLMs, probabilistic reasoning, and graph mutation but
conspicuously not traversal algorithms, make Package 020 that deferred
future package - implementing bounded, exhaustive, deterministic BFS
(for `query()`) and DFS (for `find_paths()`), never anything
heuristic.

### 6. Every public method publishes the same three-event, two-outcome shape

`REASONING_QUERY_EXECUTED` and `REASONING_RESULT_CREATED` always fire
together, in that order, on success; `REASONING_QUERY_FAILED` fires
alone on failure - mutually exclusive outcomes for a single call,
matching `CONNECTOR_INVOKED`/`CONNECTOR_FAILED`'s (Package 017)
precedent, extended to three events only because this package's own
Events section names three. `EXECUTED` marks that the underlying
read-only `IKnowledgeGraph`/`IMemoryIntegration` calls completed;
`RESULT_CREATED` marks that a `ReasoningResult` was subsequently
assembled from them - two genuinely distinct steps per this package's
own Responsibilities, which separately name "query/search" operations
and "produce structured reasoning results."

### 7. Genuine use of the injected `IMemoryIntegration`: metadata only, never correlation

This package's own Objective states the Reasoning Engine "consumes
information from the Knowledge Graph and Memory Integration," and its
Bootstrap section lists both as real dependencies - stronger language
than Package 018's "the Planner *may* consult the Knowledge Graph," a
future capability that package deliberately left unexercised. Every
public method therefore genuinely calls the injected
`IMemoryIntegration`, attaching its `synchronization_status()`
snapshot (already ungated, already read-only) to the result's
`metadata` under `"memory_synchronization_status"`. This deliberately
does NOT attempt to correlate individual matched Entities back to
specific memory keys - `MemoryMapper`'s `f"memory:{key}"` id scheme is
that package's own private implementation detail, not part of either
dependency's public contract, and depending on it here would create a
hidden, fragile coupling this package's own "does not perform graph
reasoning [or] inference" boundary (which belongs to Memory
Integration, per Package 019) should not create.

### 8. `IReasoningEngine` inherits `IService`, but zero methods are gated

Per this package's explicit "Create: `IReasoningEngine` - Extend
`IService`" instruction. Applying ADR-0002's criterion independently
to the six actual methods would not have suggested adoption on its
own - all six are synchronous, read-only, in-memory operations with no
phase distinction any of them could plausibly be gated on,
architecturally identical to Package 018's Knowledge Graph. Gated
none of them, exactly mirroring `KnowledgeGraph`'s (018) and
`IntentRouter`'s (009) shape - the third such zero-gated case in this
codebase. See `design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`'s
newly appended Empirical Finding for the full reasoning, including how
this package and Package 019 together give ADR-0002 three consecutive
directed-adoption data points (two divergent, one convergent).

---

## Events

Exactly the three event types this package's own Events section
names: `REASONING_QUERY_EXECUTED`, `REASONING_RESULT_CREATED`,
`REASONING_QUERY_FAILED`. See Architectural Decision 6 and the
Reasoning Lifecycle diagram above for the exact firing rules.

---

## IService Adoption

`IReasoningEngine` DOES inherit `IService`, per this package's own
explicit work order instruction. Unlike Package 019's Memory
Integration, applying ADR-0002's criterion independently to this
package's actual methods would NOT have suggested adoption on its own
- all six public methods are read-only and ungated. See Architectural
Decision 8 and `design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`'s
newly appended Empirical Finding for the full reasoning.

---

## Repository Verification Note

The uploaded repository ("ArgusOS (19).zip") was verified against this
package's own general "verify repository state, verify version
consistency, verify HEAD/tag ancestry, run smoke validation"
pre-flight instruction. Findings: HEAD (`2e13d14`, "Synchronize
repository version with v0.1.9 release") is a clean, single-commit
descendant of tag `v0.1.9` (which points to `ed0332a`, "Implement
Package 019 Memory Integration"); `v0.1.8` confirmed an ancestor of
HEAD via `git merge-base --is-ancestor`; `git diff v0.1.8..HEAD --stat`
shows exactly the full Package 019 diff (17 files changed), matching
that package's own reported metrics. `git status --short` showed a
completely clean working tree. `argus/memory_integration/` (Package
019) present with all expected files; `python -m pytest` passing
(1119 passed, 38 subtests); `python -m unittest discover -s tests`
passing (1031); `python -m unittest discover -s argus/tests` passing
(64); `python main.py` starting and shutting down cleanly (exit 0);
`CORE_SERVICES_VERSION == "0.1.9"` matching tag `v0.1.9`. All
confirmed before any Package 020 code was written.

---

## Files Created

```
argus/
    reasoning/
        __init__.py
        query.py
        result.py
        engine.py
        interfaces.py
        exceptions.py
tests/
    test_reasoning_query.py
    test_reasoning_result.py
    test_reasoning_engine.py
```

## Files Modified

```
argus/bootstrap.py            (construct + register Reasoning Engine
                                as 20th core service, inserted between
                                Memory Integration and the Agent
                                Runtime, per the Bootstrap section's
                                explicit, dependency-driven
                                construction order; CORE_SERVICES_
                                VERSION left at "0.1.9" - not advanced
                                by this package)
argus/events/event_types.py   (3 new event types)
argus/tests/test_bootstrap.py (CORE_SERVICE_NAMES tuple only, per the
                                standing Package 011 rule)
tests/test_bootstrap.py       (CORE_SERVICE_NAMES tuple + 3 new tests)
design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md (Empirical Finding
                                appended; Status remains Proposed)
CHANGELOG.md, DEVLOG.md, IMPLEMENTATION_REPORT.md, factory/ROADMAP.md
```

`argus/knowledge_graph/`, `argus/memory_integration/`,
`argus/planner/`, `argus/runtime/`, `argus/dispatcher/`,
`argus/capability/`, `argus/workflow/`, `argus/plugins/`, and
`argus/connectors/` are unchanged - the Reasoning Engine consumes the
Knowledge Graph's and Memory Integration's existing, unmodified public
interfaces only. Per this package's own explicit instruction, the
Planner does not consume the Reasoning Engine yet.

---

## Test Totals

1,120 tests passing via `python -m unittest discover -s tests` (1,031
from Packages 002-019, plus 7 new in `test_reasoning_query.py`, 7 new
in `test_reasoning_result.py`, 72 new in `test_reasoning_engine.py`,
and 3 new in `test_bootstrap.py` [35->38]). `python -m unittest
discover -s argus/tests` remains at 64 (duplicate tree unaffected
beyond the standing `CORE_SERVICE_NAMES` sync). `python -m pytest`
also passes: 1,208 passed, 38 subtests passed.

---

## Coverage

100% line coverage on every new/modified module measured for this
package: `argus/reasoning/__init__.py`, `argus/reasoning/query.py`,
`argus/reasoning/result.py`, `argus/reasoning/engine.py`,
`argus/reasoning/interfaces.py`, `argus/reasoning/exceptions.py`,
`argus/bootstrap.py`, and `argus/events/event_types.py` - all 100%, no
accepted gaps. Overall repository coverage: 99% (unchanged from
Package 019; remaining gaps are pre-existing and out of scope).

---

## Known Limitations

- **No persistence** - the Reasoning Engine holds no state of its
  own; every call re-reads the live Knowledge Graph (and, for
  metadata, Memory Integration's own bookkeeping) fresh.
- **No graph algorithms beyond bounded, deterministic BFS reachability
  and bounded, deterministic simple-path DFS enumeration** - no
  shortest-path ranking, no edge weighting, no heuristics of any kind,
  per this package's own "No heuristic algorithms. No machine
  learning" constraint.
- **No AI reasoning, no probabilistic inference, no LLM invocation** -
  every `ReasoningResult` is descriptive and mechanically derived;
  `reasoning_steps` is a factual trace, never a generated explanation.
- **`find_paths()`'s exhaustive enumeration is combinatorially bounded
  by `max_depth` and the graph's own density** - a dense graph with a
  large `max_depth` could enumerate a large number of paths; no
  result-size limit exists in Version 1 beyond `max_depth` itself.
- **`ReasoningResult.metadata`'s `memory_synchronization_status` does
  not correlate individual matched Entities back to specific memory
  keys** - it is the whole-system snapshot only, by deliberate design
  (see Architectural Decision 7), not a per-Entity lookup.
- **The Planner does not yet consume the Reasoning Engine** - per this
  package's own explicit Version 1 scope limit; wiring that
  consumption is left to a future package.
- No concurrency - all operations are synchronous, single-threaded,
  single-process.
- The repository's stray `argus/` duplicate tree (beyond the one
  explicitly-required `test_bootstrap.py` sync) and legacy pre-Factory
  files remain unresolved, out of scope per the Founder's explicit
  repository rules.

---

## Future Expansion

- Wire the Planner to genuinely consult the Reasoning Engine (the
  diagram already places it directly upstream), once a future
  package's work order explicitly asks for that integration.
- Add graph pattern evaluation richer than the current
  entity_type+relationship_type combination, if a future package's
  Responsibilities call for it.
- Revisit whether `find_paths()` needs a result-size cap or a
  shortest-path-only mode for denser future graphs, without
  introducing heuristics into this package's own deterministic-only
  scope.
- Revisit whether ADR-0002 should formally separate "adoption"
  (directed or derived) from "gating" (always criterion-driven), per
  this package's own newly appended Empirical Finding.

---

## Release Rules

Per the Founder's explicit instruction: no commit, tag, or push was
performed. `CORE_SERVICES_VERSION` was not changed by this package -
it remains `"0.1.9"`. This package is not reported as complete or
released - implementation ends after successful local verification;
final validation, integration, release, version update, commit, and
tag are the Founder's responsibility against the live repository.
