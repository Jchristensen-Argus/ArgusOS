# Implementation Package 035 - Capability Context

## Objective

Introduce an immutable `CapabilityContext`. "A CapabilityContext
represents all information available to a capability when it
eventually performs work. For Package 035: No execution behavior. No
AI. No tool invocation. No APIs. The context is simply created and
passed through the execution pipeline."

---

## Architectural Position

Prior architecture:

```
Execution Engine
        |
        v
Capability Executor
```

New architecture:

```
Execution Engine
        |
        v
Capability Context
        |
        v
Capability Executor
```

`ExecutionEngine` now constructs one `CapabilityContext` per Task and
sends that context - not a bare Task - to `CapabilityExecutor.resolve()`.
This is a single, linear insertion into the existing chain, matching
the diagram literally: `CapabilityExecutor.resolve()`'s own Package
034 `task: Task` parameter is *replaced* by `context: CapabilityContext`,
not supplemented by it. See "Engineering Decision" below for the full
reasoning.

---

## New Package

```
argus/capability_context/
    __init__.py     (new)
    context.py       (new)
    metadata.py       (new)
    builder.py         (new)
    interfaces.py       (new)
    exceptions.py         (new)
```

---

## CapabilityContext

Immutable value object. Fields, per the work order's own literal
order: `context_id`, `task`, `plan`, `execution_trace`, `metadata` -
already places `metadata` last, needing no normalization. Every field
defaults - `CapabilityContext()` is always valid, the same "value
object with a dedicated builder" shape `CognitiveContext`/
`PlanningSession`/`ExecutionTrace`/`Task`/`TaskRelationship`/
`ExecutionResult`/`CapabilityExecutionResult` (022, 023, 028, 029,
031, 032, 034) all use. `task`/`plan`/`execution_trace` all hold the
actual object directly, not a reference string, and all default to
`None` - "The context owns references only. No behavior." No field on
`CapabilityContext` is ever validated by the object itself; that is
`CapabilityContextBuilder`'s own job.

`execution_trace` deserves a special note: it is a genuine field on
this object, but it is **never populated by `ExecutionEngine` in
Version 1**. No real `ExecutionTrace` exists at the point
`ExecutionEngine.execute()` runs - the trace is built later, inside
`AgentService.run()`, after every step describing `execute()`'s own
effects has already been recorded onto it. Every `CapabilityContext`
`ExecutionEngine` constructs therefore carries `execution_trace=None`,
which is the only way to satisfy this package's own "every field
defaults" requirement given that construction-time constraint. See
"Known Limitations" below for the fuller statement.

---

## CapabilityContextMetadata

Immutable value object, following the same field-order convention
every metadata module in this codebase already uses: `created_at`,
`version`, `correlation_id`, `extra` - the work order's own explicit
"Follow existing metadata conventions" settles the recurring
field-order tension directly, without interpretive judgment, exactly
as Package 034's identically-worded instruction did. `extra` is
wrapped in `MappingProxyType` with a defensive copy in `__post_init__`,
matching every sibling metadata module.

---

## CapabilityContextBuilder

The only mutable object in this package. Responsibilities, per the
work order's own literal list: assign task, assign plan, assign
execution_trace, assign metadata, build immutable CapabilityContext -
five items, mapping one-to-one onto five implemented methods
(`with_task`, `with_plan`, `with_execution_trace`, `with_metadata`,
`build`), the same shape `CapabilityExecutionResultBuilder` (034)
established as the first builder in this codebase's history not
needing an expanded method surface beyond its own literal
Responsibilities list. No `with_context_id()` - the work order's own
list does not name "assign id," continuing the precedent already set
by `RelationshipBuilder` (031), `ExecutionResultBuilder` (032), and
`CapabilityExecutionResultBuilder` (034). `with_execution_trace()` is
fully implemented and tested even though `ExecutionEngine` (this
builder's only Version 1 caller) never calls it - matching this
interface's own complete Responsibilities list rather than leaving
part of the surface unbuilt. Malformed input to any `with_*()` method
raises `InvalidCapabilityContextError` - a name deliberately distinct
from `argus.capability_executor.exceptions.InvalidCapabilityContextReferenceError`
(see "Engineering Decision" below).

---

## Integration

`ExecutionEngine.execute()` now constructs one `CapabilityContextBuilder`
per Task, inside the same per-Task loop that already existed in
Package 034 - never as an instance attribute, never
constructor-injected, mirroring `AgentService.run()`'s own established
"construct `TraceBuilder` directly inside every call, not injected"
precedent (028). Each context carries `task=task, plan=plan`
(`execution_trace` left at its own `None` default). That context, not
the bare Task, is then sent to `self._capability_executor.resolve(context)`.

`CapabilityExecutor.resolve()`'s own signature changes from
`resolve(self, task: Task)` to `resolve(self, context: CapabilityContext)`.
"Resolution behavior remains unchanged - the executor still resolves
solely by `context.task.name`" - confirmed unchanged: the lookup
itself still calls `CapabilityRegistry.get_by_name(context.task.name)`
exactly as before, still treats `CapabilityNotFoundError` as the
normal `NOT_FOUND` outcome, and still never invokes the found
`Capability`.

---

## Dependency Graph

```
ExecutionEngine
    -> CapabilityContextBuilder (constructed locally, per Task)
        -> CapabilityContext (immutable, built and discarded per Task)
    -> CapabilityExecutor.resolve(context)
        -> CapabilityRegistry.get_by_name(context.task.name)
            -> Capability | CapabilityNotFoundError
```

`CapabilityContextBuilder` is never constructor-injected into
`ExecutionEngine`, and is never registered with the DI container -
confirmed by direct repository inspection (`grep -rn "Builder("
argus/bootstrap.py` and `grep -n "register.*[Bb]uilder"
argus/bootstrap.py` both return zero matches for any builder anywhere
in this codebase's history, as of Package 035). Since builders are
never bootstrap-level services, `ExecutionEngine` could not receive
one via constructor injection even if this package had asked for it -
building it locally is the only available shape.

---

## Context Lifecycle

1. `ExecutionEngine.execute(plan)` begins iterating `plan.tasks`.
2. For each Task, a fresh `CapabilityContextBuilder` is constructed,
   given `task` and `plan`, and `.build()` is called - producing one
   immutable `CapabilityContext` with a fresh `context_id`,
   `execution_trace=None`, and a fresh `CapabilityContextMetadata`.
3. That `CapabilityContext` is passed to
   `self._capability_executor.resolve(context)`.
4. `CapabilityExecutor.resolve()` validates `context` itself (must be
   a `CapabilityContext`), then validates `context.task` (must be a
   `Task`), then performs the exact-name lookup exactly as in Package
   034, reading the name through `context.task.name`.
5. The returned `CapabilityExecutionResult` is discarded immediately -
   "Ignore the returned status for now," unchanged from Package 034.
6. The `CapabilityContext` itself is never retained anywhere - it is
   built, used for exactly one `resolve()` call, and then goes out of
   scope. No `CapabilityContext` outlives the Task iteration that
   created it in Version 1.
7. `AgentService.run()` records one new trace step,
   `("CapabilityContext", "created")`, positioned between
   `("ExecutionEngine", "processed")` and `("CapabilityExecutor",
   "resolved")` - recorded honestly, after the fact, since by the time
   this step is recorded every Task in the Plan has already had its
   own `CapabilityContext` constructed and resolved.

---

## Engineering Decision

**Why `resolve()`'s signature change is a replacement, not an
addition.** This package's own Integration section reads literally:
"CapabilityExecutor now accepts CapabilityContext instead of a bare
Task." The word "instead," combined with the Architectural Position
diagram's own single-chain shape (`Execution Engine -> Capability
Context -> Capability Executor`, no skip-level arrow bypassing
`CapabilityContext` to reach `CapabilityExecutor` with a bare Task),
settles this the same way Package 034's own "ExecutionEngine now
owns: CapabilityExecutor" (not "also owns") settled its own
constructor-parameter replacement. `resolve()`'s old `task: Task`
parameter is fully replaced by `context: CapabilityContext` - there is
no overload, no bare-Task fallback path.

**Two-layer validation design.** Because `resolve()` used to validate
its own parameter directly (`InvalidTaskReferenceError` when `task`
itself wasn't a `Task`), and now receives a `CapabilityContext`
wrapping a `task` field one level down, a single validation layer
would either lose the outer check entirely or conflate two distinct
failure modes under one exception name. This package therefore adds a
new exception, `InvalidCapabilityContextReferenceError` (in
`argus.capability_executor.exceptions`), for validating the outer
`context` argument itself, while keeping `InvalidTaskReferenceError`
genuinely alive and meaningful - now validating the extracted
`context.task` value instead of the (former) outer parameter. Both
exceptions remain actively raised and actively tested; neither goes
dormant after the signature change.

**Why `InvalidCapabilityContextError` (builder) and
`InvalidCapabilityContextReferenceError` (executor) are deliberately
different names.** These validate two different things in two
different packages: `argus.capability_context.exceptions.InvalidCapabilityContextError`
is raised by `CapabilityContextBuilder`'s own `with_*()` methods when
given a malformed field value (a non-Task, a non-Plan, a non-
ExecutionTrace) - the same "builder validates its own inputs" role
`InvalidCapabilityExecutionResultError` (034) and
`InvalidExecutionResultError` (032) already play for their own
sibling builders. `argus.capability_executor.exceptions.InvalidCapabilityContextReferenceError`
is raised by `CapabilityExecutor.resolve()` when the outer `context`
argument it receives is not a `CapabilityContext` instance at all -
an entirely different check, in an entirely different package, at an
entirely different point in the pipeline. Named differently on
purpose, to prevent the two from being mistaken for the same
exception across the package boundary.

**Why `execution_trace` stays `None` in every context `ExecutionEngine`
builds.** `CapabilityContext.execution_trace` is a real field this
package's own work order names, but `ExecutionEngine.execute(plan)`'s
own signature is unchanged by this package - no `ExecutionTrace`
parameter was added - and no genuine `ExecutionTrace` object exists
at the point `execute()` runs in the first place: it is built later,
inside `AgentService.run()`, via `TraceBuilder.build()`, only after
every trace step describing `execute()`'s own effects (including the
new `("CapabilityContext", "created")` step itself) has already been
recorded onto it. Leaving `execution_trace=None` on every
`ExecutionEngine`-constructed context is therefore not an oversight -
it is the only way to satisfy this package's own "every field
defaults" requirement given that construction-time ordering
constraint, and is documented here and in context.py's own module
docstring as a deliberate, forward-looking limitation rather than left
as an unexplained gap. This mirrors the "reserved-but-unproduced enum
member" precedent already established by `ExecutionStatus.FAILED`/
`CapabilityExecutionStatus.RESOLVED`, applied here to a field instead
of an enum member.

**Why `CapabilityContextBuilder` is not registered in `bootstrap.py`.**
This package's own Bootstrap instruction is conditional: "Register:
CapabilityContextBuilder only if the existing architecture registers
builders as services; otherwise, do not register it." Direct
repository inspection (`grep -rn "Builder(" argus/bootstrap.py` and a
search for any `container.register(...)` call naming a builder)
confirms zero builders have ever been registered as bootstrap-level
services anywhere in this codebase's history - `ContextBuilder`
(022), `PlanningSessionBuilder` (023), `TraceBuilder` (028),
`TaskBuilder` (029), `RelationshipBuilder` (031),
`ExecutionResultBuilder` (032), and `CapabilityExecutionResultBuilder`
(034) are all constructed locally by their own callers, never
injected. This directly and unambiguously resolves the conditional in
favor of "otherwise, do not register it" - no judgment call was
required. `bootstrap.py` is therefore **not modified at all** by this
package, confirmed via `git diff --stat -- argus/bootstrap.py`
showing zero lines changed.

---

## Repository Verification Note

Before writing any code, the uploaded repository ("ArgusOS (34).zip")
was verified fresh against this package's own general pre-flight
instruction. No anomaly was found - the twenty-first consecutive clean
pre-flight (015-035). HEAD (`30104ab`, "Synchronize repository version
with v0.3.4 release") is a clean, single-commit descendant of tag
`v0.3.4` (which points to `f0e344f`, "Implement Package 034 Capability
Executor"), confirmed via `git merge-base --is-ancestor v0.3.4 HEAD`.
`git diff v0.3.4..HEAD --stat` shows exactly the expected one-line
version-sync commit - `CORE_SERVICES_VERSION` moved from `"0.3.3"` to
`"0.3.4"`, a patch increment, the Founder's own release choice
following Package 034's own integration. `python -m pytest` passing
(2236 passed, 38 subtests); `python -m unittest discover -s tests`
passing (2148); `python -m unittest discover -s argus/tests` passing
(64); `python main.py` starting and shutting down cleanly (exit 0);
`CORE_SERVICES_VERSION == "0.3.4"` matching tag `v0.3.4`. No anomaly of
any kind was found during pre-flight for this package.

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
    capability_context/
        __init__.py                              (new)
        context.py                               (new)
        metadata.py                               (new)
        builder.py                                (new)
        interfaces.py                             (new)
        exceptions.py                             (new)
factory/
    packages/
        035_CAPABILITY_CONTEXT.md                (new)
tests/
    test_capability_context.py                   (new)
    test_capability_context_builder.py           (new)
    test_capability_context_metadata.py          (new)
```

---

## Files Modified

```
argus/
    agent/
        service.py                               (modified)
    capability_executor/
        __init__.py                              (modified)
        exceptions.py                             (modified)
        executor.py                                (modified)
        interfaces.py                               (modified)
    execution_engine/
        engine.py                                (modified)
        interfaces.py                            (modified)
tests/
    test_agent_service.py                        (modified)
    test_bootstrap.py                             (modified)
    test_capability_executor.py                    (modified)
    test_execution_engine.py                        (modified)
CHANGELOG.md                                     (modified)
DEVLOG.md                                        (modified)
factory/ROADMAP.md                               (modified)
IMPLEMENTATION_REPORT.md                         (replaced)
```

No file outside these two lists was created, deleted, moved, or
modified. `argus/bootstrap.py` is unmodified - see "Engineering
Decision" above. `argus/capability/`, `argus/task/`,
`argus/task_relationship/`, `argus/planner/`, `argus/planning/`,
`argus/pipeline/`, `argus/response/`, `argus/trace/`, `argus/runtime/`,
`argus/dispatcher/`, `argus/plugins/`, `argus/connectors/`,
`argus/knowledge_graph/`, every `argus/capability_executor/` file
other than `__init__.py`/`exceptions.py`/`executor.py`/`interfaces.py`,
every `argus/execution_engine/` file other than `engine.py`/
`interfaces.py`, `argus/events/event_types.py`, and
`argus/tests/test_bootstrap.py` were left completely untouched -
confirmed via `git diff --stat` showing zero lines changed in any of
them.

---

## Test Results

New capability_context suites:
```
python -m pytest tests/test_capability_context.py tests/test_capability_context_builder.py tests/test_capability_context_metadata.py -q
53 passed in 0.05s
```

Modified capability_executor/execution_engine/agent_service/bootstrap
suites:
```
python -m pytest tests/test_capability_executor.py tests/test_execution_engine.py tests/test_agent_service.py tests/test_bootstrap.py -q
189 passed in 0.16s
```

Canonical suite (`tests/`):
```
python -m unittest discover -s tests
Ran 2209 tests in 0.162s
OK
```

Per this package's own explicit testing instruction:
```
python -m pytest
2297 passed, 38 subtests passed in 1.46s
```

The duplicate `argus/tests/` also verified passing (unmodified by this
package):
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
section - immutable context, builder behavior, context creation,
executor accepts context, trace propagation:

- `tests/test_capability_context_metadata.py` (new, 10 tests):
  defaults, field-order mirroring, `extra` wrapping/defensive-copy/
  immutability, dataclass immutability, equality.
- `tests/test_capability_context.py` (new, 16 tests): defaults, field
  set, field-order (`metadata` last), `execution_trace`-always-None
  note, task/plan object-identity, immutability, serialization
  consistency, equality.
- `tests/test_capability_context_builder.py` (new, 27 tests):
  identity/not-an-IService/no `with_context_id()`, every `with_*()`
  method's chaining/overwrite/validation behavior, `build()`
  independence/full chain.
- `tests/test_capability_executor.py` (+4 net, extensively rewritten):
  every existing call site wrapping a bare Task in a
  `CapabilityContext` via a new `_context()` helper; new
  `InvalidCapabilityContextTests` (non-context/None/bare-Task/dict
  rejected at the outer layer) and `InvalidTaskTests` (a
  `CapabilityContext` with no task, or a malformed `task` field,
  rejected at the inner layer); new context-immutability and
  independent-resolution tests.
- `tests/test_execution_engine.py` (+4, test doubles' `resolve()`
  updated to accept `context` and read `context.task`): new tests
  confirming `execute()` sends a `CapabilityContext` (not a bare
  Task), builds one context per Task carrying that Task and the Plan,
  builds a fresh context per Task (not a shared one), and leaves
  `execution_trace=None` on every context.
- `tests/test_agent_service.py` (assertions updated, no new tests):
  trace-sequence assertions updated to the new six-step sequence
  including `("CapabilityContext", "created")`; trace-length
  assertion updated from 5 to 6.
- `tests/test_bootstrap.py` (one test updated, no new tests): the
  end-to-end `capability_executor.resolve()` test now wraps its Task
  in a `CapabilityContextBuilder`-built context; the end-to-end
  trace-sequence assertion updated to include `"CapabilityContext"`.

---

## Coverage

Measured with `coverage.py`,
`python -m coverage run --source=argus.capability_context,argus.capability_executor,argus.execution_engine.engine,argus.execution_engine.interfaces,argus.agent.service,argus.bootstrap -m pytest`:

| Module | Stmts | Miss | Cover |
|---|---|---|---|
| `argus/agent/service.py` | 70 | 0 | 100% |
| `argus/bootstrap.py` | 99 | 0 | 100% |
| `argus/capability_context/__init__.py` | 6 | 0 | 100% |
| `argus/capability_context/builder.py` | 34 | 0 | 100% |
| `argus/capability_context/context.py` | 14 | 0 | 100% |
| `argus/capability_context/exceptions.py` | 2 | 0 | 100% |
| `argus/capability_context/interfaces.py` | 16 | 0 | 100% |
| `argus/capability_context/metadata.py` | 14 | 0 | 100% |
| `argus/capability_executor/__init__.py` | 8 | 0 | 100% |
| `argus/capability_executor/builder.py` | 39 | 0 | 100% |
| `argus/capability_executor/exceptions.py` | 4 | 0 | 100% |
| `argus/capability_executor/executor.py` | 44 | 0 | 100% |
| `argus/capability_executor/interfaces.py` | 22 | 0 | 100% |
| `argus/capability_executor/metadata.py` | 14 | 0 | 100% |
| `argus/capability_executor/result.py` | 14 | 0 | 100% |
| `argus/capability_executor/status.py` | 7 | 0 | 100% |
| `argus/execution_engine/engine.py` | 38 | 0 | 100% |
| `argus/execution_engine/interfaces.py` | 31 | 0 | 100% |

100% coverage across the entire new `argus/capability_context/`
package (86 statements) and across every modified
`argus/capability_executor/`, `argus/execution_engine/`,
`argus/agent/service.py`, and `argus/bootstrap.py` module (560
statements total across both packages) - reached on the first
measurement, no post-hoc gap-closing needed. One interim gap was
caught and fixed before this final measurement: `ICapabilityContextBuilder`'s
abstract methods initially included `raise NotImplementedError` body
statements, which - unlike every sibling builder interface, which use
docstring-only abstract method bodies - registered as uncovered
statements; removed to match the established sibling-interface
convention, restoring 100%.

---

## Known Limitations

- **`execution_trace` is always `None` on every `CapabilityContext`
  `ExecutionEngine` constructs in Version 1** - a deliberate,
  documented consequence of construction-time ordering, not an
  oversight. See "Engineering Decision" above and context.py's own
  module docstring.
- **No execution occurs** - "No execution behavior. No AI. No tool
  invocation. No APIs." `CapabilityContext` is a passive data carrier
  only; nothing in this codebase yet reads any field off it besides
  `CapabilityExecutor.resolve()`'s own `context.task` extraction.
- **`CapabilityContext` never outlives the Task iteration that created
  it** - it is built, used for exactly one `resolve()` call, and
  discarded; no caching, no reuse across Tasks, no persistence.
- **Resolution behavior is unchanged from Package 034** - still exact-
  name-only, still ignored by `ExecutionEngine` once returned; this
  package changes only how the Task reaches `CapabilityExecutor`, not
  what happens once it arrives.
- **No tool invocation, API call, or AI inference of any kind** - "No
  execution behavior. No AI. No tool invocation. No APIs."
- **`CapabilityContextBuilder` is not a bootstrap-level service** - by
  design, per this package's own conditional Bootstrap instruction and
  this codebase's own "no builder has ever been registered as a
  service" precedent; see "Engineering Decision" above.
- No persistence, no concurrency, no scheduling - unchanged from every
  prior package in this phase.

---

## Release Rules

Per the Founder's standing release process, this package was
implemented and verified entirely within the supplied repository. No
`git commit`, `git tag`, push, or git-history modification of any
kind was performed. `CORE_SERVICES_VERSION` was not changed and
remains `"0.3.4"`. This package is not being reported as complete -
final validation, integration, version bump, commit, tag, and release
remain the Founder's responsibility, to be performed against the live
repository after independent regression testing.
