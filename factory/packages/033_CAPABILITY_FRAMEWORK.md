# Implementation Package 033 - Capability Framework

## Objective

Introduce the Capability Framework. "A Capability represents a
pluggable unit of functionality that can eventually execute specific
types of Tasks. For Package 033: No real work is performed. No tools
are invoked. No AI is called. No external APIs are used. The
framework simply establishes the contracts and registration
mechanism."

---

## Critical Pre-Implementation Finding: Package 013 Already Owns
`argus/capability/`

Before writing any code, verifying this package's own work order
against the actual repository surfaced a direct naming collision:
`argus/capability/` already exists, introduced by Package 013 (the
Capability Registry), and is deeply integrated - consumed directly by
`IntentDispatcher`, `Planner`, `PluginManager`, `ConnectorManager`,
`AgentRuntime`, and `KnowledgeGraph`, registered in `bootstrap.py` as
the `capability_registry` core service, and covered by its own
pre-existing `tests/test_capability.py` and
`tests/test_capability_registry.py`. Package 013's own `Capability` is
intent-routing metadata (`name, description, intent_types, action_kind,
id, workflow_id, enabled, metadata`) - a different concept from this
package's own "pluggable unit of functionality that can eventually
execute specific types of Tasks," despite sharing the exact same class
name, package path, and (for `capability.py`/`registry.py`/
`interfaces.py`/`exceptions.py`) even the exact same file names this
package's own "New Package" section lists.

This was surfaced to the Founder directly rather than resolved
silently, per this codebase's own standing "flag genuine ambiguities
rather than guess" discipline. The Founder's explicit direction,
given in two messages: **extend the existing package in place; do not
create a parallel package or replace the existing implementation;
evolve `Capability`/`CapabilityRegistry` to support the new
requirements while preserving backward compatibility wherever
practical; keep `argus/capability/` the single source of truth.**
Every decision in this document follows from that direction. See
"Engineering Decisions" below for how each individual field/method
collision was resolved.

---

## Architectural Position

Prior architecture:

```
Planner -> Plan -> Execution Engine
```

New architecture:

```
Planner -> Plan -> Execution Engine -> Capability Registry -> Capability
```

Per the Founder's own resolution, "Capability Registry" in this
diagram is `argus.capability.registry.CapabilityRegistry` - the same
registry Package 013 already built, not a second, parallel one. The
new arrow is a constructor-only reference: `ExecutionEngine` now holds
`self._capability_registry`, but `execute()` itself never calls it -
"the dependency exists only to establish future wiring."

---

## Package Extended, Not Created

```
argus/capability/
    __init__.py        (modified - new re-exports)
    capability.py       (modified - two new fields)
    registry.py         (modified - get_by_name(), duplicate-name rejection)
    metadata.py          (new)
    builder.py            (new)
    interfaces.py       (modified - ICapabilityBuilder, get_by_name())
    exceptions.py       (unchanged - InvalidCapabilityError/
                          DuplicateCapabilityError already covered
                          every failure mode this package needed)
```

---

## Capability

Package 033's own Requirements list a five-field shape: `capability_id,
name, description, version, metadata`, "immutable, default values,
metadata last, value object only." Reconciled against Package 013's
own pre-existing eight-field `Capability` (`name, description,
intent_types, action_kind, id, workflow_id, enabled, metadata`) as
follows - see "Engineering Decisions" for the full reasoning behind
each:

- **`capability_id`** -> understood to refer to the pre-existing `id`
  field. Not renamed - every existing consumer/test keys and reads by
  `.id`.
- **`name`, `description`** -> already present, unchanged.
- **`version`** -> genuinely new. Added as `version: str = "1.0"`.
- **`metadata`** -> Package 013's own `metadata: Mapping[str, Any]`
  field (arbitrary caller data, no dedicated value-object type) is
  left completely untouched in type, position, and behavior. A
  *second*, new field, `capability_metadata: CapabilityMetadata`, is
  added and declared last - satisfying "metadata last" from the
  perspective of the dedicated-metadata-object family this new field
  belongs to.

No pre-existing field was renamed, retyped, removed, or repositioned
relative to the others. Every `Capability(...)` call site that worked
before this package still works unchanged, since both new fields
default. `Capability` still performs no field validation of its own -
unchanged since Package 013.

---

## CapabilityMetadata

New. Immutable. Fields: `created_at`, `version`, `correlation_id`,
`extra` - mirrors `ContextMetadata`/`PlanningMetadata`/`TraceMetadata`/
`TaskMetadata`/`RelationshipMetadata`/`ExecutionMetadata`'s shape and
field names exactly, continuing the identical field-order-
normalization resolution Packages 028/029/031/032 already applied.
Populated only via `CapabilityBuilder.with_metadata()` - see below -
never via `Capability`'s own pre-existing `metadata` field, which this
new type does not replace.

---

## CapabilityBuilder

New. Mutable, fluent builder - "Builder is the only mutable object" -
the first dedicated builder `Capability` has ever had. Full method
surface, beyond the work order's own six-item Responsibilities list
("assign id, assign name, assign description, assign version, assign
metadata, build immutable Capability") for the identical
"Responsibilities list under-specifies the method surface a builder
actually needs" reason already resolved three times before (029, 031,
032): `with_id()`, `with_name()`, `with_description()`,
`with_intent_type()`/`with_intent_types()`/`clear_intent_types()`,
`with_action_kind()`, `with_workflow_id()`, `with_enabled()`,
`with_version()`, `with_metadata(key, value)` (populates
`CapabilityMetadata.extra`, not the pre-existing bare `metadata`
field), `build()`. `with_id()` is notable: no other builder in this
codebase exposes an equivalent for its own object's identity field
(`RelationshipBuilder`/`ExecutionResultBuilder`/`TaskBuilder` all let
identity auto-generate only) - included here because this package's
own Responsibilities list explicitly names "assign id," unlike any of
those three. `build()` performs no completeness check, mirroring every
other builder in this codebase - a `Capability` built without calling
`with_name()`/`with_intent_type()`/`with_action_kind()` still
succeeds, holding empty-string/empty-tuple placeholders, since
`Capability` itself validates nothing (that remains
`CapabilityRegistry.register()`'s job, unchanged).

---

## CapabilityRegistry

Extended in place, not replaced. New: `get_by_name(name) -> Capability`
("lookup by name"), mirroring `get(capability_id)`'s own shape and
error contract exactly. Changed: `register()` now also rejects a
`name` that is already registered under a *different* id, raising the
same pre-existing `DuplicateCapabilityError` `register()` already
raises for a duplicate id - no new exception type needed. Unchanged:
`register`/`unregister`/`get`/`find_by_intent_type`/
`list_capabilities`/`contains`, insertion-order preservation, the
`CAPABILITY_REGISTERED`/`CAPABILITY_UNREGISTERED` event publication,
and `CapabilityRegistry`'s own non-`IService` status (see
interfaces.py's own pre-existing Architectural Note, unchanged).

Re-registering under a name freed by a prior `unregister()` still
succeeds, mirroring the pre-existing (013) duplicate-id-after-
unregister behavior exactly.

---

## Engineering Decisions

Five design questions in this package had no single, unambiguous
answer directly stated by either the work order or the Founder's own
clarifying messages, and each was resolved by reasoning from this
codebase's own established precedent, the Founder's own explicit
"backward compatibility wherever practical" instruction, and (where
genuinely ambiguous) verification against the actual test suite.

**Should `Capability.id` be renamed to `capability_id`?** No.
`CapabilityRegistry`, `IntentDispatcher`, `Planner`, `PluginManager`,
every existing test, and `bootstrap.py` itself all key and read by
`.id` today. Renaming would touch every one of those call sites - a
far larger, riskier change than "extend the existing package... while
preserving backward compatibility wherever practical" calls for.
Package 033's own "capability_id" is treated as referring to this
pre-existing field - a documented naming-convention reconciliation,
the same "work order names differ from the established convention;
normalize to the convention and document it" resolution applied
repeatedly in this codebase (most recently the metadata field-order
normalization in Packages 028/029/031/032).

**Should `Capability.metadata`'s type change from `Mapping[str, Any]`
to `CapabilityMetadata`?** No. `tests/test_capability.py`'s own
pre-existing `MappingProxyType`/subscript/defensive-copy assertions
depend on `metadata` staying a plain mapping; retyping it would be a
real, not cosmetic, backward-compatibility break for every existing
`Capability(metadata={...})` caller. Instead, `capability_metadata:
CapabilityMetadata` was added as a *second*, new, additively-defaulted
field - see "Capability" above.

**Should `CapabilityRegistry.register()` reject duplicate names,
given this breaks a real, pre-existing, passing test?**
`tests/test_planner.py` registered three Capabilities sharing the same
default name ("Answer") under three different ids within a single
registry, across two test methods. Rather than skip the work order's
own explicit "Duplicate names are rejected" requirement to preserve
that test unmodified, or silently make `register()` diverge from what
was asked, the requirement was implemented as specified and the two
affected test fixtures were given distinct names
(`"Answer 1"`/`"Answer 2"`/`"Answer 3"`) - the same "the test itself,
not the design, needed to change" resolution Package 031 already
applied to `tests/test_task.py`'s own `NoExecutableLogicTests`. A full
`python -m pytest` run before and after this change confirmed these
were the *only* two pre-existing tests affected anywhere in the
repository - the authoritative check, not a manual trace.

**Should `CapabilityBuilder` expose `with_intent_type()`/
`with_action_kind()`/`with_workflow_id()`/`with_enabled()`, none of
which the work order's own Responsibilities list names?** Yes - see
"CapabilityBuilder" above. Without them, a `CapabilityBuilder` could
never set `intent_types`/`action_kind`, both required (no-default)
fields on the pre-existing `Capability` constructor, making the
builder unable to build a usable `Capability` for the one use case
(`action_kind="workflow"`, the only kind Version 1's Intent Dispatcher
actually resolves) that matters most.

**Should `ExecutionEngine.__init__()`'s new `capability_registry`
parameter be optional (defaulting to `None`) or required?** Required,
with no default. The work order's own Integration section states
plainly "Accept: CapabilityRegistry" as a constructor change, with no
mention of optionality, and every call site in this codebase
(`bootstrap.py`, every test) always has a real `CapabilityRegistry`
available to pass - there is no genuine "no registry yet" case for
this constructor to accommodate defensively, unlike `Plan`'s own
optionality on `ExecutionResult` (032), which exists because a
not-yet-executed `ExecutionResult` is a real, meaningful state.

---

## Integration

`ExecutionEngine.__init__()` (`argus/execution_engine/engine.py`)
gains a new, required parameter, `capability_registry:
ICapabilityRegistry`, stored as `self._capability_registry` and never
read anywhere in this module - "No dispatch. No execution. No lookup.
No behavior changes." `execute()`'s own four-step sequence, unchanged
since Package 032, is completely untouched; only `__init__()` changed,
confirmed via `git diff` touching exactly one method. This ends
`ExecutionEngine`'s own brief run (027-032) as this codebase's second
fully-empty-constructor core service - `ResponseEngine` (027) remains
the sole surviving example - but does not change `execute()`'s own
gating status: `IExecutionEngine` remains the sixth zero-gated
`IService` adopter and the fifth divergent ADR-0002 case, both facts
established at Package 032 and unchanged here (a constructor gaining a
stored-but-unused dependency is not the same thing as a method gaining
a gate).

`argus/bootstrap.py` passes the already-constructed
`capability_registry` (constructed early, alongside `Planner`'s own
dependencies, well before `ExecutionEngine`) into `ExecutionEngine`'s
new constructor parameter - genuine dependency injection of the same
singleton the container itself resolves under `"capability_registry"`,
not a second, separate instance. No new core service was registered -
`CapabilityRegistry` has been a core service since Package 013; this
package only changes what one *other* core service's constructor
receives.

No Task changes. No Plan changes. No Pipeline redesign. No Response
redesign. No Runtime redesign. No ExecutionTrace changes. No plugins.
No persistence. No AI. No tools or APIs called - confirmed via `git
diff --stat` showing zero lines changed in `argus/task/`,
`argus/task_relationship/`, `argus/planner/`, `argus/planning/`,
`argus/pipeline/`, `argus/response/`, `argus/trace/`, `argus/runtime/`,
and every `argus/execution_engine/` file other than `engine.py` and
`interfaces.py`'s own docstring amendment.

---

## Dependency Graph

```
argus.capability.metadata (CapabilityMetadata)
    [pure, dependency-free leaf - new]

argus.capability.capability (Capability)
    -> argus.intent.intent (IntentType)                    [pre-existing]
    -> argus.capability.metadata (CapabilityMetadata)       [new]

argus.capability.builder (CapabilityBuilder)                [new]
    -> argus.capability.capability (Capability)
    -> argus.capability.metadata (CapabilityMetadata)
    -> argus.capability.exceptions (InvalidCapabilityError)
    -> argus.capability.interfaces (ICapabilityBuilder)
    -> argus.intent.intent (IntentType)

argus.capability.interfaces (ICapabilityRegistry, ICapabilityBuilder)
    -> argus.capability.capability (Capability)             [pre-existing]
    -> argus.intent.intent (IntentType)                     [pre-existing]

argus.capability.registry (CapabilityRegistry)
    -> argus.capability.capability (Capability)             [pre-existing]
    -> argus.capability.exceptions                          [pre-existing]
    -> argus.capability.interfaces (ICapabilityRegistry)    [pre-existing]
    -> argus.events (Event, EventType, IEventBus)           [pre-existing]
    -> argus.intent.intent (IntentType)                     [pre-existing]

argus.execution_engine.engine (ExecutionEngine)
    -> argus.capability.interfaces (ICapabilityRegistry)    [new, Package 033,
                                                              stored only]

argus.bootstrap
    -> argus.capability (unchanged import surface)
    -> argus.execution_engine (ExecutionEngine construction changed)
```

`argus.capability.metadata` remains a pure, dependency-free leaf,
matching every other metadata value object in this codebase.
`argus.execution_engine.engine`'s new dependency on
`argus.capability.interfaces` is one-directional and inert - no method
in `argus.capability` imports or calls into `argus.execution_engine`
in either direction.

---

## Registry Behavior

`register(capability)`: validates (non-empty id/name/intent_types/
action_kind, workflow_id required when action_kind is "workflow" -
all pre-existing, 013), then rejects a duplicate id, then (Package
033) rejects a duplicate name across every currently-registered
Capability - raising the same `DuplicateCapabilityError` either way.
`unregister(capability_id)`: removes by id, freeing both that id and
that Capability's own name for reuse. `get(capability_id)` /
`get_by_name(name)`: exact lookups, raising `CapabilityNotFoundError`
if absent, `InvalidCapabilityError` if the argument is the wrong type.
`find_by_intent_type(intent_type)`: unchanged, a pure filter applying
no enabled/disabled policy. `list_capabilities()`: unchanged, returns
every registered Capability in insertion (registration) order.
`contains(capability_id)`: unchanged, never raises.

---

## IService Adoption

None new. `ICapabilityBuilder` does not inherit `IService` - the same
"not an IService" shape every prior builder interface in this
codebase (`ICognitiveContextBuilder`/`IPlanningSessionBuilder`/
`ITraceBuilder`/`ITaskBuilder`/`IRelationshipBuilder`/
`IExecutionResultBuilder`) already established. `ICapabilityRegistry`
remains a plain `ABC`, unchanged since Package 013 - its own
Architectural Note (registry has no genuine multi-phase behavior) is
untouched by this package. `IExecutionEngine` remains an `IService`
adopter, unchanged in adoption status by this package - see
"Integration" above for what *did* change (a stored constructor
dependency, not a gate). No new entry was added to
`design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md` - this package
introduces no new `IService` adopter and changes no adopter's own
gating behavior, only a constructor's dependency list.

---

## Events

None new. `argus/events/event_types.py` was not modified -
`CAPABILITY_REGISTERED`/`CAPABILITY_UNREGISTERED` already existed
(Package 013) and continue to fire from `register()`/`unregister()`
exactly as before, now also covering the new duplicate-name rejection
path (which, like every other `register()` validation failure, does
not publish).

---

## Repository Verification Note

Before writing any code, the uploaded repository ("ArgusOS (32).zip")
was verified fresh against this package's own general pre-flight
instruction. No anomaly was found - the nineteenth consecutive clean
pre-flight (015-033). HEAD (`194c6e4`, "Synchronize repository version
with v0.3.2 release") is a clean, single-commit descendant of tag
`v0.3.2` (which points to `4dbd2bb`, "Implement Package 032 Execution
Engine"), confirmed via `git merge-base --is-ancestor v0.3.2 HEAD`.
`git diff v0.3.2..HEAD --stat` shows exactly the expected one-line
version-sync commit - `CORE_SERVICES_VERSION` moved from `"0.3.1"` to
`"0.3.2"`, a patch increment, the Founder's own release choice
following Package 032's integration. `python -m pytest` passing (2034
passed, 38 subtests); `python -m unittest discover -s tests` passing
(1946); `python -m unittest discover -s argus/tests` passing (64);
`python main.py` starting and shutting down cleanly (exit 0);
`CORE_SERVICES_VERSION == "0.3.2"` matching tag `v0.3.2`. The naming
collision described above was the only anomaly of any kind found
during pre-flight, and was surfaced to the Founder directly rather
than resolved unilaterally.

Per the Founder's explicit release rules, this implementation was
built, tested, and verified entirely within the supplied repository.
No `git commit`, `git tag`, push, or git-history modification of any
kind was performed, `CORE_SERVICES_VERSION` was not changed by this
package, and this package is not being reported as complete - final
validation, integration, release, tagging, and git operations are the
Founder's responsibility, to be performed against the live repository
after independent regression testing.

---

## Files Created

```
argus/
    capability/
        metadata.py                          (new)
        builder.py                           (new)
factory/
    packages/
        033_CAPABILITY_FRAMEWORK.md          (new)
tests/
    test_capability_builder.py               (new)
    test_capability_metadata.py              (new)
```

---

## Files Modified

```
argus/
    capability/
        __init__.py                          (modified)
        capability.py                        (modified)
        interfaces.py                        (modified)
        registry.py                          (modified)
    execution_engine/
        engine.py                            (modified)
        interfaces.py                        (modified)
    bootstrap.py                             (modified)
tests/
    test_capability.py                       (modified)
    test_capability_registry.py              (modified)
    test_execution_engine.py                 (modified)
    test_agent_service.py                    (modified)
    test_bootstrap.py                        (modified)
    test_planner.py                          (modified - two fixtures
                                                 given distinct names)
CHANGELOG.md                                 (modified)
DEVLOG.md                                    (modified)
factory/ROADMAP.md                           (modified)
IMPLEMENTATION_REPORT.md                     (replaced)
```

No file outside these two lists was created, deleted, moved, or
modified. `argus/task/`, `argus/task_relationship/`, `argus/planner/`,
`argus/planning/`, `argus/pipeline/`, `argus/response/`,
`argus/trace/`, `argus/runtime/`, `argus/agent/service.py`,
`argus/dispatcher/`, `argus/plugins/`, `argus/connectors/`,
`argus/knowledge_graph/`, `argus/execution_engine/builder.py`,
`argus/execution_engine/result.py`, `argus/execution_engine/status.py`,
`argus/execution_engine/metadata.py`,
`argus/execution_engine/exceptions.py`,
`argus/execution_engine/__init__.py`, `argus/tests/test_bootstrap.py`,
and `argus/events/event_types.py` were left completely untouched -
confirmed via `git diff --stat` showing zero lines changed in any of
them.

---

## Test Results

New capability builder/metadata suites:
```
python -m pytest tests/test_capability_builder.py tests/test_capability_metadata.py -q
67 passed in 0.05s
```

Modified capability/execution_engine/bootstrap/agent suites:
```
python -m pytest tests/test_capability.py tests/test_capability_registry.py tests/test_execution_engine.py tests/test_agent_service.py tests/test_bootstrap.py argus/tests/test_bootstrap.py tests/test_planner.py -q
```
(all passing as part of the full run below)

Canonical suite (`tests/`):
```
python -m unittest discover -s tests
Ran 2036 tests in 0.123s
OK
```

Per this package's own explicit testing instruction:
```
python -m pytest
2124 passed, 38 subtests passed in 1.49s
```

The duplicate `argus/tests/` also verified passing:
```
python -m unittest discover -s argus/tests
Ran 64 tests in 0.015s
OK
```

`python main.py`:
```
[INFO] argus: ArgusOS application started.
[INFO] argus: ArgusOS application shutting down.
```
Exit code 0.

New/updated test coverage, per this package's own explicit Testing
section - immutable Capability, registry insertion order, duplicate
rejection, lookup by id, lookup by name, bootstrap registration,
ExecutionEngine constructor injection:

- `tests/test_capability_metadata.py` (new): defaults, field-order
  mirroring, `extra` wrapping/defensive-copy/immutability, dataclass
  immutability, equality.
- `tests/test_capability_builder.py` (new): identity/not-an-IService,
  every `with_*()` method's chaining/overwrite/accumulate/validation
  behavior, `with_id()`'s own auto-generation-when-unset behavior,
  `with_metadata()`'s own non-interference with the pre-existing
  `metadata` field, `build()` completeness/independence/full chain.
- `tests/test_capability.py` (+13): `version` field defaults/honored/
  immutability, `capability_metadata` field defaults/honored/
  immutability/distinctness from the pre-existing `metadata` field, a
  dedicated `BackwardCompatibilityTests` class confirming the exact
  field set and pre-existing call shapes still work unchanged.
- `tests/test_capability_registry.py` (+9): duplicate-name rejection
  (raises, does not register, distinct names do not collide,
  unregister frees the name), a full `GetByNameTests` class (returns
  registered, rejects non-string, unknown name raises, raises after
  unregister, publishes no events).
- `tests/test_execution_engine.py` (rewritten throughout): every
  `ExecutionEngine()` construction updated to require
  `capability_registry`, a new `ConstructorInjectionTests` class
  (registry is stored, accepts any `ICapabilityRegistry`
  implementation, `execute()` never calls any registry method - proven
  via an exploding test double), constructor-requires-argument
  negative test.
- `tests/test_agent_service.py` (updated throughout): every
  `ExecutionEngine()` construction updated identically.
- `tests/test_bootstrap.py` (+1): confirms `ExecutionEngine`'s own
  stored `capability_registry` is the exact same singleton the
  container resolves under `"capability_registry"` - genuine
  dependency injection, not a separate instance.
- `tests/test_planner.py` (2 fixtures updated): distinct names given
  to three Capabilities previously sharing a default name within a
  single registry - see "Engineering Decisions" above.

---

## Coverage

Measured with `coverage.py`,
`python -m coverage run --source=argus.capability,argus.execution_engine.engine,argus.execution_engine.interfaces,argus.bootstrap -m pytest`:

| Module | Stmts | Miss | Cover |
|---|---|---|---|
| `argus/bootstrap.py` | 96 | 0 | 100% |
| `argus/capability/__init__.py` | 7 | 0 | 100% |
| `argus/capability/builder.py` | 71 | 0 | 100% |
| `argus/capability/capability.py` | 21 | 0 | 100% |
| `argus/capability/exceptions.py` | 4 | 0 | 100% |
| `argus/capability/interfaces.py` | 44 | 0 | 100% |
| `argus/capability/metadata.py` | 14 | 0 | 100% |
| `argus/capability/registry.py` | 70 | 0 | 100% |
| `argus/execution_engine/engine.py` | 35 | 0 | 100% |
| `argus/execution_engine/interfaces.py` | 31 | 0 | 100% |

100% coverage across the entire `argus/capability/` package (231
statements, both new and modified modules) and across every modified
`argus/execution_engine/` module and `argus/bootstrap.py` (162
statements) - reached on the first measurement, no post-hoc
gap-closing needed.

---

## Known Limitations

- **No dispatch model exists yet** - "The framework simply establishes
  the contracts and registration mechanism." `ExecutionEngine` holds a
  `CapabilityRegistry` reference but never calls any of its methods;
  nothing in this codebase yet resolves a `Task` to a `Capability` or
  invokes one.
- **`Capability` still performs no field validation of its own** -
  unchanged since Package 013; `CapabilityRegistry.register()` and
  (as of this package) `CapabilityBuilder`'s own `with_*()` methods
  remain the only two places validation lives.
- **Two distinct "metadata" concepts now coexist on `Capability`** -
  the pre-existing (013) `metadata: Mapping[str, Any]` (arbitrary
  caller data) and the new (033) `capability_metadata:
  CapabilityMetadata` (creation timestamp/schema version/correlation
  id/extra bookkeeping) are never merged or reconciled into one field
  - a direct, documented consequence of prioritizing backward
  compatibility over a clean single-metadata-field design.
- **`capability_id` is not a real field name anywhere in this
  codebase** - it is a documented alias for the pre-existing `id`
  field; any future work order that says "capability_id" should be
  read as referring to `Capability.id`.
- **No tool invocation, API call, or AI inference of any kind** - "For
  Package 033: No real work is performed."
- **`ExecutionEngine` is no longer a fully-empty-constructor core
  service** - `ResponseEngine` (027) remains the sole surviving
  example of that shape; `IExecutionEngine`'s own zero-gated-adopter
  and divergent-ADR-0002-case counts are unaffected, since no method
  gained a gate.
- No execution, no scheduling, no persistence, no concurrency -
  unchanged from every prior package in this phase.

---

## Future Dispatch Model

This package deliberately stops at "ExecutionEngine receives a
reference to CapabilityRegistry but does not use it yet." A future
package building genuine Task-to-Capability dispatch would need to:
resolve which registered `Capability` (or Capabilities) can perform a
given `Task` - likely via `Task`'s own fields, though `Task` (029) and
`Capability` (013/033) share no field today that could drive that
match; decide what "execute a Capability" even means for a Capability
whose `action_kind` isn't `"workflow"` (Version 1's `IntentDispatcher`
only ever resolves that one kind); and give `ExecutionEngine.execute()`
a genuine second responsibility beyond placing every Task into
`completed_tasks` unconditionally - the first point at which
`ExecutionStatus.FAILED`/`RUNNING` could become reachable states
rather than reserved ones (032). None of that exists yet, and none of
it was introduced here - `self._capability_registry` is inert.
Combined with Package 032's own still-open "Future Execution Model,"
the fuller target shape now reads: `Plan -> Tasks -> Execution Engine
-> Capability Registry -> [future: Task-to-Capability resolution] ->
[future: genuine per-Task outcomes] -> Execution Result`.

---

## Release Rules

Per the Founder's standing release process, this package was
implemented and verified entirely within the supplied repository. No
`git commit`, `git tag`, push, or git-history modification of any
kind was performed. `CORE_SERVICES_VERSION` was not changed and
remains `"0.3.2"`. This package is not being reported as complete -
final validation, integration, version bump, commit, tag, and release
remain the Founder's responsibility, to be performed against the live
repository after independent regression testing.
