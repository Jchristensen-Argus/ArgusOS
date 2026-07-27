# Implementation Package 034 - Capability Executor

## Objective

Introduce the Capability Executor. "The Capability Executor resolves
a Capability for a Task and produces an immutable
CapabilityExecutionResult. For Package 034: No AI. No plugins. No
external tools. No API calls. No business logic. It establishes the
execution contract only."

---

## Architectural Position

Prior architecture:

```
Execution Engine
        |
        v
Capability Registry
```

New architecture:

```
Execution Engine
        |
        v
Capability Executor
        |
        v
Capability Registry
        |
        v
Capability
```

`ExecutionEngine` no longer holds any direct reference to
`ICapabilityRegistry` - only `CapabilityExecutor` does. This is a
single, linear dependency chain with no skip-level arrow, matching
the diagram literally: `ExecutionEngine.__init__()`'s own Package 033
`capability_registry` parameter is *replaced* by `capability_executor:
ICapabilityExecutor`, not supplemented by it. See "Engineering
Decision" below for the full reasoning.

---

## New Package

```
argus/capability_executor/
    __init__.py     (new)
    executor.py      (new)
    result.py         (new)
    status.py          (new)
    metadata.py         (new)
    builder.py            (new)
    interfaces.py          (new)
    exceptions.py            (new)
```

---

## CapabilityExecutionResult

Immutable value object. Fields, per the work order's own literal
order: `execution_id`, `task`, `capability`, `status`, `metadata` -
already places `metadata` last, needing no normalization (unlike the
metadata-field-order tension every prior metadata-bearing package
since 028 had to resolve). Every field defaults -
`CapabilityExecutionResult()` is always valid, the same "value object
with a dedicated builder" shape `CognitiveContext`/`PlanningSession`/
`ExecutionTrace`/`Task`/`TaskRelationship`/`ExecutionResult` (022,
023, 028, 029, 031, 032) all use. `task`/`capability` both hold the
actual object directly, not a reference string, and both default to
`None` - `capability` stays `None` whenever no matching Capability was
found; the NOT_FOUND case never fabricates a placeholder.

---

## CapabilityExecutionStatus

New. Immutable `Enum` (not a `str` subclass), five members: `PENDING`,
`RESOLVED`, `COMPLETED`, `FAILED`, `NOT_FOUND`. "No transition logic."
Only `COMPLETED` and `NOT_FOUND` are ever produced by Version 1's
`resolve()` - see "Engineering Decision" below for why a successful
match produces `COMPLETED` rather than the seemingly more intuitive
`RESOLVED`. `PENDING` serves only as the pre-resolve() default,
mirroring `ExecutionResult.status`'s identical role. `RESOLVED` and
`FAILED` are reserved for a future package.

---

## CapabilityExecutionMetadata

New. Immutable. Fields: `created_at`, `version`, `correlation_id`,
`extra` - mirrors `ContextMetadata`/`PlanningMetadata`/`TraceMetadata`/
`TaskMetadata`/`RelationshipMetadata`/`ExecutionMetadata`/
`CapabilityMetadata`'s shape and field names exactly. This package's
own work order explicitly instructs "Follow established metadata
conventions" - settling directly, without any interpretive judgment
call, the same field-order tension every metadata-bearing package
since 028 has had to reason its own way through.

---

## CapabilityExecutionResultBuilder

New. Mutable, fluent builder - "Builder is the only mutable object."
Method surface matches the work order's own five-item Responsibilities
list exactly, unlike every builder since Package 029: `with_task()`,
`with_capability()`, `with_status()`, `with_metadata(key, value)`,
`build()`. No `with_execution_id()` - unlike `CapabilityBuilder`
(033), whose own Responsibilities list explicitly names "assign id,"
this package's own list does not name "assign execution_id," matching
`RelationshipBuilder`'s (031) and `ExecutionResultBuilder`'s (032) own
shape - identity is always system-assigned.
`with_task()`/`with_capability()`/`with_status()` are singular fields,
overwritten not accumulated, mirroring `ExecutionResultBuilder.
with_plan()`/`with_status()`'s own rule. `with_capability()` requires
an actual `Capability` instance - no `None` shortcut, mirroring
`with_plan()`'s own identical rule; a result with `capability=None` is
produced by never calling `with_capability()` at all.

---

## CapabilityExecutor

New core service. Responsibilities: accept a `Task` (per-call, via
`resolve()`), accept a `CapabilityRegistry` (constructor-injected),
resolve a `Capability`. `resolve(task)` does exactly two things:
validate `task` is a `Task` instance (raising
`InvalidTaskReferenceError` otherwise), then call
`capability_registry.get_by_name(task.name)` - if found, return a
`CapabilityExecutionResult` carrying that `Capability` with
`status=COMPLETED`; if `CapabilityNotFoundError` is raised, treat that
as a normal resolution outcome (not an error to propagate) and return
one with `capability=None` and `status=NOT_FOUND` instead. "Only
deterministic resolution" - no other `CapabilityRegistry` method is
ever called, and the found `Capability` is never invoked.

---

## Dispatch Model

`ExecutionEngine.execute()` sends every `Task` in `plan.tasks`, in
order, to `capability_executor.resolve(task)` before placing it into
`completed_tasks` - "Send Task to CapabilityExecutor. Receive
CapabilityExecutionResult. Ignore the returned status for now.
Continue placing every Task into completed_tasks (unchanged behavior
from Package 032)." The returned `CapabilityExecutionResult` is
discarded immediately - not stored, not inspected, not passed to
anything else. An empty `Plan` never calls `resolve()` at all. "This
package introduces dispatch only - not execution policy": whether a
`Task` resolves to `COMPLETED` or `NOT_FOUND` changes nothing about
`ExecutionEngine`'s own outcome for that `Task` in Version 1 - every
`Task` still lands in `completed_tasks`, and `ExecutionResult.status`
is still always `ExecutionStatus.COMPLETED`.

---

## Deterministic Lookup

`CapabilityExecutor.resolve()` performs exactly one lookup per call -
`CapabilityRegistry.get_by_name(task.name)` (Package 033) - an
O(n) linear scan over every registered `Capability`, returning the
first (and, since `CapabilityRegistry.register()` has rejected
duplicate names since Package 033, only) `Capability` whose `name`
exactly matches. The match is case-sensitive and requires exact
equality - no partial matching, no fuzzy matching, no intent-based
routing (that remains `IntentDispatcher`'s own, entirely separate,
unmodified responsibility). The same `Task` resolved twice against an
unchanged registry always produces the same `capability`/`status`
pair - only `execution_id` and `metadata.correlation_id`/`created_at`
differ between calls, matching every other builder-produced value
object's own "independent snapshots" precedent.

---

## Integration

`ExecutionEngine.__init__()` (`argus/execution_engine/engine.py`)
parameter changed from `capability_registry: ICapabilityRegistry`
(033) to `capability_executor: ICapabilityExecutor` (034) - a
replacement, not an addition. `execute()`'s own body changed too,
unlike Package 033's inert constructor change: for each `Task` in
`plan.tasks`, `self._capability_executor.resolve(task)` is called and
its result discarded, then `with_completed_task(task)` proceeds
exactly as before.

`argus/agent/service.py` (`AgentService.run()`) gains one new trace
step - `("CapabilityExecutor", "resolved")` - positioned between
`("ExecutionEngine", "processed")` and `("ResponseEngine", "invoked")`
- recorded honestly, after the fact: by the time `("ExecutionEngine",
"processed")` is recorded, every `Task` in the `Plan` has already been
sent through `CapabilityExecutor.resolve()`, since that happens
*inside* `execution_engine.execute()`, before that call returns.
`AgentService` gains no new constructor dependency and `run()` gains
no new interaction step - `CapabilityExecutor` is owned by
`ExecutionEngine`, not by `AgentService`.

`argus/bootstrap.py` constructs `capability_executor =
CapabilityExecutor(capability_registry=capability_registry)`
immediately after the Cognitive Pipeline and immediately before the
Execution Engine, registers it as `"capability_executor"`, then
constructs `execution_engine = ExecutionEngine(capability_executor=
capability_executor)`. `_register_core_services()` gains a matching
`capability_executor: ICapabilityExecutor` parameter and
`core_services` tuple entry - twenty-six core services now registered
(up from twenty-five). `CORE_SERVICES_VERSION` remains `"0.3.3"`, not
advanced by this package.

No changes to `Response`, `Planner`, `Runtime`, or `Events` - confirmed
via `git diff --stat` showing zero lines changed in `argus/response/`,
`argus/planner/`, `argus/planning/`, `argus/runtime/`, and
`argus/events/event_types.py`. No redesign of `CapabilityRegistry` -
`argus/capability/` is completely untouched by this package.

---

## Dependency Graph

```
argus.capability_executor.metadata (CapabilityExecutionMetadata)
    [pure, dependency-free leaf - new]

argus.capability_executor.status (CapabilityExecutionStatus)
    [pure, dependency-free leaf - new]

argus.capability_executor.result (CapabilityExecutionResult)
    -> argus.task.task (Task)
    -> argus.capability.capability (Capability)
    -> argus.capability_executor.status (CapabilityExecutionStatus)
    -> argus.capability_executor.metadata (CapabilityExecutionMetadata)

argus.capability_executor.interfaces
    (ICapabilityExecutionResultBuilder, ICapabilityExecutor)
    -> argus.task.task (Task)
    -> argus.capability.capability (Capability)
    -> argus.capability_executor.result (CapabilityExecutionResult)
    -> argus.capability_executor.status (CapabilityExecutionStatus)
    -> argus.lifecycle.interfaces (IService)

argus.capability_executor.builder (CapabilityExecutionResultBuilder)
    -> argus.task.task (Task)
    -> argus.capability.capability (Capability)
    -> argus.capability_executor.result (CapabilityExecutionResult)
    -> argus.capability_executor.status (CapabilityExecutionStatus)
    -> argus.capability_executor.metadata (CapabilityExecutionMetadata)
    -> argus.capability_executor.exceptions
    -> argus.capability_executor.interfaces

argus.capability_executor.executor (CapabilityExecutor)
    -> argus.task.task (Task)
    -> argus.capability.interfaces (ICapabilityRegistry) - genuinely
       called, once per resolve()
    -> argus.capability.exceptions (CapabilityNotFoundError)
    -> argus.capability_executor.builder
    -> argus.capability_executor.interfaces
    -> argus.capability_executor.result
    -> argus.capability_executor.status
    -> argus.lifecycle.lifecycle (LifecycleState)

argus.execution_engine.engine (ExecutionEngine)
    -> argus.capability_executor.interfaces (ICapabilityExecutor) -
       new, Package 034, genuinely called once per Task, replacing
       argus.capability.interfaces (ICapabilityRegistry) - Package
       033, stored only

argus.agent.service (AgentService)
    -> unchanged constructor dependencies (ICognitivePipeline,
       IExecutionEngine, IResponseEngine) - no new dependency; the new
       trace step describes work ExecutionEngine already performed
       internally

argus.bootstrap
    -> argus.capability_executor (CapabilityExecutor construction,
       registration)
    -> argus.execution_engine (ExecutionEngine construction changed)
```

`argus.capability_executor.metadata` and `.status` remain pure,
dependency-free leaves, matching every sibling metadata/status module
in this codebase. `argus.execution_engine.engine`'s dependency on
`argus.capability_executor.interfaces` is one-directional; no method
in `argus.capability_executor` imports or calls into
`argus.execution_engine`.

---

## Execution Lifecycle

`CapabilityExecutor` implements `IService`
(`initialize`/`start`/`stop`/`status`), per "Register: CapabilityExecutor
as a core service" - read the same "core service" == "adopts IService"
shorthand already established for `ResponseEngine` (027) and
`ExecutionEngine` (032). Applying ADR-0002's own criterion to
`resolve()` independently would not have suggested adoption on its
own: `resolve()` is a synchronous, read-only, in-memory lookup against
an already-injected `ICapabilityRegistry` - no external call, no
write, no phase distinction it could plausibly be gated on. This makes
`ICapabilityExecutor` the **seventh** zero-gated `IService` adopter in
this codebase (after `IntentRouter`, `KnowledgeGraph`, `ReasoningEngine`,
`DecisionEngine`, `ResponseEngine`, and `ExecutionEngine`) and the
**sixth** case where an explicit instruction to adopt `IService`
diverges from what ADR-0002's own criterion would independently
conclude (after Packages 018, 020, 021, 027, and 032) - architecturally
closer to `ReasoningEngine`/`DecisionEngine`/`KnowledgeGraph` (each
zero-gated despite holding a genuine constructor dependency) than to
`ResponseEngine`/`ExecutionEngine` (each zero-gated specifically
because they hold *no* constructor dependency at all). `resolve()`
remains callable in `CREATED`, `RUNNING`, or `STOPPED` alike -
confirmed via `UngatedBehaviorTests` in
`tests/test_capability_executor.py`. `ExecutionEngine.execute()`
itself also remains ungated, unaffected in its own gating status by
this package - calling a zero-gated method introduces no new phase
distinction for the caller to gate on either. Appended a new Empirical
Finding to `design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`
recording this - the sixteenth adopter overall, and this ADR's own
first run of three consecutive divergent findings (027, 032, 034).

---

## Engineering Decision

**Why does `ExecutionEngine.__init__()` replace `capability_registry`
with `capability_executor`, rather than accept both?** The work
order's own Architectural Position diagram gives a single, linear
chain - `Execution Engine -> Capability Executor -> Capability
Registry -> Capability` - with no skip-level arrow from `Execution
Engine` directly to `Capability Registry`. The Bootstrap section's own
phrasing reinforces this: "ExecutionEngine now owns:
CapabilityExecutor" (not "ExecutionEngine also owns"). Since
`ExecutionEngine` never called `capability_registry` directly even in
Package 033 (it was stored but genuinely unused, "to establish future
wiring"), and that future wiring is now `CapabilityExecutor` itself,
retaining a direct `ICapabilityRegistry` reference on `ExecutionEngine`
would be dead weight - the same object reachable one hop further via
`CapabilityExecutor` if it were ever needed, with no call site in this
package that needs it directly. This is a breaking constructor change
from Package 033's own shape, and it is not inert the way Package
033's own change was - `execute()`'s body changed too.

**Why does a successful match produce `CapabilityExecutionStatus.
COMPLETED` rather than `RESOLVED`?** The work order's own Resolution
behavior section is unambiguous, literal instruction, not prose open
to interpretation: "If a Capability exists whose name exactly matches
the Task name, return: status = COMPLETED." `RESOLVED` might read as
the more intuitive member name for "a Capability was found," but it is
implemented literally as instructed rather than substituted for a
seemingly-more-apt alternative - `RESOLVED` remains a reserved,
unused member, available for a future package that distinguishes "a
Capability was found" from "resolution is fully done."

**Why does `CapabilityExecutor.resolve()` treat `CapabilityNotFoundError`
as a normal outcome rather than propagating it?** `CapabilityRegistry.
get_by_name()` (033) raises `CapabilityNotFoundError` whenever no
Capability matches - that is its own documented, expected behavior for
"no match," not a genuine failure. Since this package's own explicit
Resolution behavior names `NOT_FOUND` as one of exactly two possible
outcomes (the other being `COMPLETED`), catching this specific,
well-defined exception and converting it into that documented outcome
is the correct mapping - a `resolve()` that let this exception
propagate would leave `NOT_FOUND` unreachable through its own
documented entry point.

**Why does `CapabilityExecutionResultBuilder` expose no
`with_execution_id()`?** Unlike Package 033's `CapabilityBuilder`,
whose own Responsibilities list explicitly names "assign id" (a
documented divergence from every other builder in this codebase),
this package's own five-item Responsibilities list does not name
"assign execution_id" - matching `RelationshipBuilder`'s (031) and
`ExecutionResultBuilder`'s (032) own shape instead. Identity remains
always system-assigned via `CapabilityExecutionResult`'s own
`default_factory`.

---

## Repository Verification Note

Before writing any code, the uploaded repository ("ArgusOS (33).zip")
was verified fresh against this package's own general pre-flight
instruction. No anomaly was found - the twentieth consecutive clean
pre-flight (015-034). HEAD (`ab2ac70`, "Synchronize repository version
with v0.3.3 release") is a clean, single-commit descendant of tag
`v0.3.3` (which points to `9952afd`, "Implement Package 033 Capability
Framework"), confirmed via `git merge-base --is-ancestor v0.3.3 HEAD`.
`git diff v0.3.3..HEAD --stat` shows exactly the expected one-line
version-sync commit - `CORE_SERVICES_VERSION` moved from `"0.3.2"` to
`"0.3.3"`, a patch increment, the Founder's own release choice
following Package 033's own integration. `python -m pytest` passing
(2124 passed, 38 subtests); `python -m unittest discover -s tests`
passing (2036); `python -m unittest discover -s argus/tests` passing
(64); `python main.py` starting and shutting down cleanly (exit 0);
`CORE_SERVICES_VERSION == "0.3.3"` matching tag `v0.3.3`. No anomaly of
any kind was found during pre-flight for this package - unlike Package
033, no naming collision or other architectural surprise arose.

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
    capability_executor/
        __init__.py                              (new)
        executor.py                              (new)
        result.py                                (new)
        status.py                                (new)
        metadata.py                              (new)
        builder.py                               (new)
        interfaces.py                            (new)
        exceptions.py                            (new)
factory/
    packages/
        034_CAPABILITY_EXECUTOR.md               (new)
tests/
    test_capability_execution_result.py          (new)
    test_capability_execution_status.py          (new)
    test_capability_execution_metadata.py        (new)
    test_capability_execution_builder.py         (new)
    test_capability_executor.py                  (new)
```

---

## Files Modified

```
argus/
    agent/
        service.py                               (modified)
    execution_engine/
        engine.py                                (modified)
        interfaces.py                            (modified)
    bootstrap.py                                 (modified)
    tests/
        test_bootstrap.py                        (modified)
design/
    decisions/
        0002_ISERVICE_ADOPTION_CRITERION.md      (modified)
tests/
    test_agent_service.py                        (modified)
    test_bootstrap.py                            (modified)
    test_execution_engine.py                     (modified)
CHANGELOG.md                                     (modified)
DEVLOG.md                                        (modified)
factory/ROADMAP.md                               (modified)
IMPLEMENTATION_REPORT.md                         (replaced)
```

No file outside these two lists was created, deleted, moved, or
modified. `argus/capability/`, `argus/task/`, `argus/task_relationship/`,
`argus/planner/`, `argus/planning/`, `argus/pipeline/`, `argus/response/`,
`argus/trace/`, `argus/runtime/`, `argus/dispatcher/`, `argus/plugins/`,
`argus/connectors/`, `argus/knowledge_graph/`, every
`argus/execution_engine/` file other than `engine.py`/`interfaces.py`,
and `argus/events/event_types.py` were left completely untouched -
confirmed via `git diff --stat` showing zero lines changed in any of
them.

---

## Test Results

New capability_executor suites:
```
python -m pytest tests/test_capability_execution_result.py tests/test_capability_execution_status.py tests/test_capability_execution_metadata.py tests/test_capability_execution_builder.py tests/test_capability_executor.py -q
104 passed in 0.09s
```

Modified execution_engine/agent_service/bootstrap suites:
```
python -m pytest tests/test_execution_engine.py tests/test_agent_service.py tests/test_bootstrap.py argus/tests/test_bootstrap.py -q
156 passed in 0.20s
```

Canonical suite (`tests/`):
```
python -m unittest discover -s tests
Ran 2148 tests in 0.158s
OK
```

Per this package's own explicit testing instruction:
```
python -m pytest
2236 passed, 38 subtests passed in 1.46s
```

The duplicate `argus/tests/` also verified passing:
```
python -m unittest discover -s argus/tests
Ran 64 tests in 0.016s
OK
```

`python main.py`:
```
[INFO] argus: ArgusOS application started.
[INFO] argus: ArgusOS application shutting down.
```
Exit code 0.

New/updated test coverage, per this package's own explicit Testing
section - exact-name resolution, not-found behavior, immutable
execution result, builder, registry lookup, constructor injection,
trace propagation:

- `tests/test_capability_execution_status.py` (new, 8 tests):
  members, values, no-transition-logic, round trips, equality.
- `tests/test_capability_execution_metadata.py` (new, 10 tests):
  defaults, field-order mirroring, `extra` wrapping/defensive-copy/
  immutability, dataclass immutability, equality.
- `tests/test_capability_execution_result.py` (new, 23 tests):
  defaults, field set, task/capability object-identity, immutability,
  invalid construction, serialization consistency, equality.
- `tests/test_capability_execution_builder.py` (new, 29 tests):
  identity/not-an-IService/no `with_execution_id()`, every `with_*()`
  method's chaining/overwrite/validation behavior, `with_capability()`'s
  own None-rejection, `build()` independence/full chain.
- `tests/test_capability_executor.py` (new, 34 tests): identity/
  IService, constructor injection, lifecycle, ungated behavior, exact-
  name resolution (including case-sensitivity and partial-match
  rejection), not-found behavior, registry-lookup confirmation (a spy
  registry confirms `get_by_name()` is the only method ever called),
  invalid Task rejection, immutable result / no Task mutation / no
  Capability invocation.
- `tests/test_execution_engine.py` (rewritten throughout): every
  `ExecutionEngine()` construction updated to require
  `capability_executor`; new tests confirming `resolve()` is called
  once per Task in order, the returned `CapabilityExecutionResult` is
  ignored, an empty Plan never calls `resolve()`, and every Task still
  completes regardless of resolution outcome; constructor negative
  tests for both the new required parameter and the removed
  `capability_registry` one.
- `tests/test_agent_service.py` (updated throughout): every
  `ExecutionEngine()` construction updated to supply
  `capability_executor`; trace-sequence assertions updated to the new
  five-step sequence including `("CapabilityExecutor", "resolved")`.
- `tests/test_bootstrap.py` (+5): `capability_executor` registration,
  not-started status, receives-the-container's-own-registry,
  end-to-end resolution against a real bootstrap-registered
  Capability; `execution_engine` test renamed and updated to assert
  identity against `capability_executor` instead of
  `capability_registry`; end-to-end trace-sequence assertion updated.
- `argus/tests/test_bootstrap.py` (+1 entry): `CORE_SERVICE_NAMES`
  gained `"capability_executor"`.

---

## Coverage

Measured with `coverage.py`,
`python -m coverage run --source=argus.capability_executor,argus.execution_engine.engine,argus.execution_engine.interfaces,argus.agent.service,argus.bootstrap -m pytest`:

| Module | Stmts | Miss | Cover |
|---|---|---|---|
| `argus/agent/service.py` | 69 | 0 | 100% |
| `argus/bootstrap.py` | 99 | 0 | 100% |
| `argus/capability_executor/__init__.py` | 8 | 0 | 100% |
| `argus/capability_executor/builder.py` | 39 | 0 | 100% |
| `argus/capability_executor/exceptions.py` | 3 | 0 | 100% |
| `argus/capability_executor/executor.py` | 40 | 0 | 100% |
| `argus/capability_executor/interfaces.py` | 21 | 0 | 100% |
| `argus/capability_executor/metadata.py` | 14 | 0 | 100% |
| `argus/capability_executor/result.py` | 14 | 0 | 100% |
| `argus/capability_executor/status.py` | 7 | 0 | 100% |
| `argus/execution_engine/engine.py` | 36 | 0 | 100% |
| `argus/execution_engine/interfaces.py` | 31 | 0 | 100% |

100% coverage across the entire new `argus/capability_executor/`
package (146 statements) and across every modified
`argus/execution_engine/`, `argus/agent/service.py`, and
`argus/bootstrap.py` module (235 statements) - reached on the first
measurement, no post-hoc gap-closing needed.

---

## Known Limitations

- **No execution occurs** - "Only deterministic resolution." A found
  `Capability` is never invoked; nothing in this codebase yet performs
  the work a `Capability` actually describes.
- **`ExecutionEngine` still ignores every `CapabilityExecutionResult`
  it receives** - "Ignore the returned status for now." A `Task` that
  resolves to `NOT_FOUND` is placed into `completed_tasks` exactly the
  same as one that resolves to `COMPLETED`; `ExecutionStatus.FAILED`
  remains unreachable in Version 1.
- **Resolution is name-based only** - no intent-type matching, no
  fuzzy matching, no ranking among multiple candidates (moot in
  Version 1 since `CapabilityRegistry.register()` has rejected
  duplicate names since Package 033).
- **`CapabilityExecutionStatus.RESOLVED` and `FAILED` are never
  produced by any Version 1 code path** - reserved for a future
  package; see status.py's own module docstring.
- **No tool invocation, API call, or AI inference of any kind** - "No
  AI. No plugins. No external tools. No API calls. No business
  logic."
- **`ExecutionEngine` no longer holds any direct `ICapabilityRegistry`
  reference** - a deliberate, documented consequence of the diagram's
  own single-chain shape; if `ExecutionEngine` ever needs registry
  access directly again, a future package would need to re-add it.
- No persistence, no concurrency, no scheduling - unchanged from every
  prior package in this phase.

---

## Release Rules

Per the Founder's standing release process, this package was
implemented and verified entirely within the supplied repository. No
`git commit`, `git tag`, push, or git-history modification of any
kind was performed. `CORE_SERVICES_VERSION` was not changed and
remains `"0.3.3"`. This package is not being reported as complete -
final validation, integration, version bump, commit, tag, and release
remain the Founder's responsibility, to be performed against the live
repository after independent regression testing.
