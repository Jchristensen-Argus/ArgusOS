# Implementation Package 018 - Knowledge Graph

## Objective

Give ArgusOS a structured semantic layer for persistent knowledge -
an in-memory graph of Entities connected by typed, directed
Relationships, available as a core service to higher-level reasoning
components. Per the Founder's Package 018 work order:

```
... -> Planner -> Knowledge Graph -> Validated Plan -> Agent Runtime -> ...
```

The Knowledge Graph is not a database, not long-term storage, and not
vector search - "It is an in-memory semantic graph that future
services can query." It stores relationships between entities rather
than simple records, but performs no graph traversal algorithms (no
shortest path), no inference, and no persistence. "The Planner may
consult the Knowledge Graph. The Runtime must not modify it."

---

## Specification Note

No `design/specifications/KNOWLEDGE_GRAPH.md` exists in the repository
- the same situation as Packages 002, 009-017. This package is built
directly from the Founder's explicit work order.

---

## Entity Model

Immutable (`argus/knowledge_graph/entity.py`):

```
Entity
    id              str    - auto-generated uuid4; the model's own
                              identity field (see Naming Note below)
    entity_type     str    - required, non-empty; a plain string, not
                              a closed enum (for example, "person",
                              "workflow", "concept")
    name            str    - required, non-empty; human-readable, not
                              enforced unique
    attributes      Mapping[str, Any] - arbitrary descriptive data,
                              defaults to empty, coerced to an
                              immutable MappingProxyType
```

Pure data - holds no live reference to any Relationship and does not
know what it is connected to.

---

## Relationship Model

Immutable (`argus/knowledge_graph/relationship.py`):

```
Relationship
    id                  str  - auto-generated uuid4; the model's own
                                identity field
    source_entity_id    str  - required, non-empty; the id of the
                                Entity this edge originates from
    target_entity_id    str  - required, non-empty; the id of the
                                Entity this edge points to (may equal
                                source_entity_id - self-loops are
                                permitted)
    relationship_type   str  - required, non-empty; a plain string,
                                not a closed enum (for example,
                                "reports_to", "depends_on")
    attributes          Mapping[str, Any] - arbitrary descriptive
                                data, defaults to empty, coerced to an
                                immutable MappingProxyType
```

Pure data - holds only its two endpoints' `id`s, never live `Entity`
references, matching `Execution.plan_id`'s identical "reference by id
only" precedent (Package 016).

---

## Lifecycle

```
        add_entity(entity)
                |
                v
       Entity registered  --publish ENTITY_ADDED-->
                |
    +-----------+-----------+
    |                       |
add_relationship          remove_entity(entity_id)
(source/target must              |
 already be registered,          v
 or EntityNotFoundError)   cascade: every Relationship
    |                      referencing entity_id as
    v                      source or target is also
Relationship registered    removed (no separate event
--publish                  per cascaded removal)
RELATIONSHIP_ADDED-->            |
    |                            v
    v                      Entity removed
remove_relationship(id)    --publish ENTITY_REMOVED--
    |
    v
Relationship removed
--publish RELATIONSHIP_REMOVED--

        neighbors(entity_id) / find_by_type(entity_type)
                |
                v
        read-only queries over current Entities/
        Relationships; no state change, no event
```

`get_entity()`/`list_entities()`/`list_relationships()` are likewise
pure, read-only, unstated-event operations.

---

## Dependency Graph

```
KnowledgeGraph
    depends on -> IEventBus   (publish entity/relationship lifecycle events)

KnowledgeGraph does NOT depend on:
    argus.runtime      (AgentRuntime is never referenced)
    argus.planner       (Planner is never referenced)
    argus.dispatcher     (IntentDispatcher is never referenced)
    argus.plugins        (PluginManager is never referenced)
    argus.capability     (CapabilityRegistry is never referenced)
    argus.workflow        (WorkflowEngine is never referenced)
    argus.connectors       (ConnectorManager is never referenced)
```

Construction order in `bootstrap.py` follows the Bootstrap section's
explicit sequence - Capability Registry -> Intent Dispatcher ->
Planner -> Knowledge Graph -> Agent Runtime -> Connector Manager -
with Knowledge Graph inserted between Planner and Agent Runtime. Like
Connector Manager's own placement (Package 017), this is **not
dependency-driven**: the dependency graph above shows `KnowledgeGraph`
depends on nothing but the Event Bus. Unlike every prior purely
positional insertion, however, this one lands in the *middle* of the
existing construction sequence rather than being appended at the end
- Agent Runtime's and Connector Manager's own construction is
unaffected in every respect except now following the Knowledge Graph
rather than the Planner directly.

---

## Architectural Decisions

### 1. `remove_entity()` cascades to remove referencing Relationships

Neither the work order's Responsibilities nor its Graph Service
section states what happens to a Relationship whose Entity is removed.
Two options were considered: forbid removal while Relationships still
reference the Entity (a foreign-key-style constraint), or cascade -
remove every Relationship that references the removed Entity as
`source_entity_id` or `target_entity_id` at the same time. Cascading
was chosen: it actively guarantees graph integrity by construction (no
Relationship can ever outlive either Entity it connects, so `neighbors()`
never needs to defensively check that a resolved id still exists - see
`graph.py`'s own `neighbors()` docstring), it requires no new
exception type or extra caller step, and it matches "the graph must
remain lightweight infrastructure" better than a constraint that would
make removal cumbersome. Cascaded Relationship removals do not each
publish their own `RELATIONSHIP_REMOVED` event - only the single
`ENTITY_REMOVED` for the call that triggered them - matching
`ConnectorManager.unregister_connector()`'s (Package 017) "one call,
one event" precedent.

### 2. `IKnowledgeGraph` inherits `IService`, but no method is gated

Unlike every prior IService-adoption decision in this codebase (all
judgment calls applying ADR-0002), this package's work order
explicitly instructs "Extend `IService`" - not a judgment call this
time. Applying ADR-0002's criterion to the actual methods
independently would not have suggested adoption: none of
`add_entity`/`remove_entity`/`get_entity`/`list_entities`/
`add_relationship`/`remove_relationship`/`list_relationships`/
`neighbors`/`find_by_type` involve any external call, dispatch, or
phase distinction - "No graph algorithms yet... Only foundational
graph operations." Rather than inventing a "must be RUNNING to query"
gate the work order never asked for (which would also sit awkwardly
against "The Planner may consult the Knowledge Graph" - a consultation
that should not spuriously fail merely because bootstrap.py's own
"register only, never start" rule left the graph un-started), the full
IService lifecycle boilerplate was implemented with zero gated
methods - exactly mirroring `IntentRouter`'s (Package 009) identical
shape. See `design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`'s
newly appended Empirical Finding, which records this as the first case
in this codebase where an explicit instruction to adopt `IService`
does not align with what the criterion would independently conclude.

### 3. `id`, not `entity_id`/`relationship_id`, for each model's own identity

The work order's suggested fields list `entity_id`/`relationship_id`,
but every other value object in this codebase (`Capability`, `Plugin`,
`Plan`, `PlanStep`, `Execution`, `Connector`) uses a plain `id` field
for its own identity. `Entity.id`/`Relationship.id` follow that same
established convention; `entity_id`/`relationship_id` remain the
parameter names used throughout `KnowledgeGraph`'s public API.

### 4. `source_entity_id`/`target_entity_id`, not the work order's literal `source_entity`/`target_entity`

Every prior reference-to-another-model field in this codebase carries
an explicit `_id` suffix (`Capability.workflow_id`, `Execution.plan_id`)
specifically to make unambiguous that the field holds an id string,
not a live object reference. A `Relationship` holding live `Entity`
objects would violate this package's own "pure data" requirement and
would go stale the moment an Entity were removed and a new one
registered under a different identity. `source_entity_id`/
`target_entity_id` follow the established `_id`-suffix convention
instead.

### 5. Neither `argus/planner/` nor `argus/runtime/` is modified by this package

"The Planner may consult the Knowledge Graph. The Runtime must not
modify it" describes what the target architecture now *permits*, not
a requirement to wire the Planner to the Knowledge Graph in this
package - this package's own New Package/Responsibilities/Testing
sections make no mention of touching `argus/planner/` or
`argus/runtime/` at all, and its Constraints explicitly limit scope to
"lightweight infrastructure." This is the same category of judgment
already applied to `PluginManager`'s (014) diagram positioning: the
diagram describes a capability a *future* package may exercise, not a
concrete integration this package must build. "The Runtime must not
modify it" is trivially satisfied here, since `AgentRuntime` is not
given any reference to `KnowledgeGraph` at all in this package.

### 6. Lookup is `id`-based; `find_by_type()` is the only supported query beyond direct lookup and `neighbors()`

Every prior registry in this codebase (`Capability`, `Plugin`, `Plan`,
`Execution`, `Connector`) is looked up by a generated `id`, never by a
non-unique descriptive field. `get_entity(entity_id)` follows that
convention; `Entity.name` remains purely descriptive, not enforced
unique. `find_by_type()` filters `Entity.entity_type` only - the work
order names no analogous relationship-type query method, so none was
added, matching this codebase's established precedent of treating an
explicit method list as closed (for example, `ConnectorManager`'s own
closed method list, Package 017).

### 7. Multiple Relationships between the same pair of Entities are permitted

`add_relationship()` only rejects a duplicate `id` - it does not
reject a second Relationship with the same `source_entity_id`/
`target_entity_id`/`relationship_type` triple. Real-world graphs
often have legitimately distinct edges between the same two nodes (for
example, two "cites" edges with different `attributes`), and nothing
in the work order asks for semantic-content deduplication - matching
`CapabilityRegistry`/`PluginManager`/`ConnectorManager`'s identical
"duplicate id only" precedent.

---

## Events

Exactly the four event types this package's own Events section names:
`ENTITY_ADDED`, `ENTITY_REMOVED`, `RELATIONSHIP_ADDED`,
`RELATIONSHIP_REMOVED`. `ENTITY_REMOVED` fires once per
`remove_entity()` call regardless of how many Relationships it
cascades to remove (see Architectural Decision 1); cascaded removals
publish nothing of their own. None of the four fire for a failed
(validation error, duplicate, not-found, or invalid-reference) call.

---

## IService Adoption

`IKnowledgeGraph` DOES inherit `IService`, per this package's own
explicit work order instruction - not a judgment call, unlike every
prior adoption decision in this codebase. None of its own methods are
gated on the `RUNNING` state, making `KnowledgeGraph` the second
IService adopter in this codebase (after `IntentRouter`, Package 009)
with zero gated methods. See Architectural Decision 2 and
`design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`'s newly
appended Empirical Finding for the full reasoning, including the
observation that applying ADR-0002's criterion independently to this
package's own methods would not have suggested adoption at all.

---

## Repository Verification Note

The uploaded repository ("ArgusOS (17).zip") was verified against this
package's own general "verify repository state, verify version
consistency, run smoke validation" pre-flight instruction. Findings:
HEAD (`0b1ae78`, "Synchronize repository version with v0.1.7 release")
is a clean, single-commit descendant of tag `v0.1.7` (which points to
`7d5a5fa`, "Implement Package 017 Connector Framework"); `git diff
v0.1.7..HEAD --stat` shows exactly 1 file changed (`argus/bootstrap.py`,
1 insertion/1 deletion) - a minimal, standard version-only sync, no
anomaly. `git status --short` showed a completely clean working tree.
`argus/connectors/` (Package 017) present with all expected files;
`python -m pytest` passing (982 passed, 38 subtests); `python -m
unittest discover -s tests` passing (894); `python main.py` starting
and shutting down cleanly (exit 0); `CORE_SERVICES_VERSION == "0.1.7"`
matching tag `v0.1.7`. All confirmed before any Package 018 code was
written.

---

## Files Created

```
argus/
    knowledge_graph/
        __init__.py
        entity.py
        relationship.py
        graph.py
        interfaces.py
        exceptions.py
tests/
    test_entity.py
    test_relationship.py
    test_knowledge_graph.py
```

## Files Modified

```
argus/bootstrap.py            (construct + register Knowledge Graph
                                as 18th core service, inserted between
                                the Planner and the Agent Runtime, per
                                the Bootstrap section's explicit
                                construction order; CORE_SERVICES_
                                VERSION left at "0.1.7" - not advanced
                                by this package)
argus/events/event_types.py   (4 new event types)
argus/tests/test_bootstrap.py (CORE_SERVICE_NAMES tuple only, per the
                                standing Package 011 rule)
tests/test_bootstrap.py       (CORE_SERVICE_NAMES tuple + 3 new tests)
design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md (Empirical Finding
                                appended; Status remains Proposed)
CHANGELOG.md, DEVLOG.md, IMPLEMENTATION_REPORT.md, factory/ROADMAP.md
```

`argus/runtime/`, `argus/planner/`, `argus/dispatcher/`,
`argus/capability/`, `argus/workflow/`, `argus/plugins/`, and
`argus/connectors/` are unchanged - the Knowledge Graph has no
dependency on, and no touchpoint with, any of them; its only
dependency is `IEventBus`.

---

## Test Totals

967 tests passing via `python -m unittest discover -s tests` (894 from
Packages 002-017, plus 6 new in `test_entity.py`, 7 new in
`test_relationship.py`, 57 new in `test_knowledge_graph.py`, and 3 new
in `test_bootstrap.py` [29->32]). `python -m unittest discover -s
argus/tests` remains at 64 (duplicate tree unaffected beyond the
standing `CORE_SERVICE_NAMES` sync). `python -m pytest` also passes:
1,055 passed, 38 subtests passed.

---

## Coverage

100% line coverage on every new/modified module measured for this
package: `argus/knowledge_graph/__init__.py`,
`argus/knowledge_graph/entity.py`, `argus/knowledge_graph/relationship.py`,
`argus/knowledge_graph/graph.py`, `argus/knowledge_graph/interfaces.py`,
`argus/knowledge_graph/exceptions.py`, `argus/bootstrap.py`, and
`argus/events/event_types.py` - all 100%, no accepted gaps. Overall
repository coverage: 99% (measured with `coverage run -m pytest`
followed by `coverage report`), unchanged from Package 017.

---

## Known Limitations

- **No persistence** - Entities and Relationships are held only in
  memory; nothing survives a process restart, per this package's
  explicit "It is not long-term storage" Objective.
- **No graph traversal algorithms** - `neighbors()` is a single-hop
  lookup only; no shortest path, no multi-hop queries, per this
  package's explicit Constraints.
- **No inference, no AI reasoning** - the graph stores and returns
  exactly what was registered; it draws no new conclusions.
- **No vector search** - `find_by_type()` is an exact-match filter
  only, not a similarity search of any kind.
- **Not yet consulted by the Planner or any other component** - "The
  Planner may consult the Knowledge Graph" describes a capability the
  target architecture now permits, not something this package wires
  up; see Architectural Decision 5.
- **`find_by_type()` has no relationship-type analogue** - only
  Entities can be queried by type; see Architectural Decision 6.
- No concurrency - all operations are synchronous, single-threaded, in
  a single process.
- The repository's stray `argus/` duplicate tree (beyond the one
  explicitly-required `test_bootstrap.py` sync) and legacy pre-Factory
  files remain unresolved, out of scope per the Founder's explicit
  repository rules.

---

## Future Expansion

- Wire the Planner to optionally consult the Knowledge Graph during
  plan creation or validation, per this package's own "The Planner may
  consult the Knowledge Graph" Architectural Position - explicitly out
  of bounds for this package.
- Add graph traversal algorithms (shortest path, multi-hop queries)
  once a future package's scope calls for them.
- Add a relationship-type query method (`find_relationships_by_type()`
  or similar), if a future package's Responsibilities call for it.
- Add persistence, once a future package's Constraints permit it -
  Version 1 is explicitly in-memory only.
- Revisit whether `KnowledgeGraph` should gain a genuinely gated
  method as its responsibilities grow, and whether ADR-0002 itself
  should be revised to address "directed" (Founder-instructed) versus
  "derived" (criterion-applied) IService adoption - see this package's
  own ADR-0002 Empirical Finding.

---

## Release Rules

Per the Founder's explicit instruction: no commit, tag, or push was
performed. `CORE_SERVICES_VERSION` was not changed by this package -
it remains `"0.1.7"`. This package is not reported as complete or
released - implementation ends after successful local verification;
final validation, integration, release, version update, commit, and
tag are the Founder's responsibility against the live repository.
