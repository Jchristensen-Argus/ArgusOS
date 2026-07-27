# Implementation Package 029 - Task Model

## Objective

Introduce the immutable Task domain model. "A Task represents a
single unit of work produced by a Plan." This package introduces no
execution - "Only the model." Unlike every runtime-facing package
since 025 (Cognitive Pipeline, Agent Session, Response Engine,
Execution Trace), this package is deliberately, completely isolated -
it modifies no pre-existing file at all, the first purely additive
package since Cognitive Context (022).

---

## Architectural Motivation

Prior to this package, this codebase's only "unit of work" concept was
`PlanStep` - a planning-time description of "one thing that needs to
happen," scoped entirely to the Planner's own domain and constructed
directly by `Planner.add_step()`. `Task` introduces a separate,
independent concept: a unit of work as it will eventually be
understood by execution, once a future package exists to perform it.
Keeping `Task` isolated from `Plan`/`PlanStep` in Version 1 - "Future
packages will integrate Tasks into Plans" - avoids conflating "how the
Planner currently represents work" with "how execution will eventually
consume it," a distinction this package's own Constraints are explicit
about: no execution, no scheduling, no workflows, no tools, and no
redesign of any existing package.

---

## Architectural Position

Current architecture:

```
User
    -> Agent
    -> Pipeline
    -> Planner
    -> Response
```

Future architecture:

```
User
    -> Agent
    -> Pipeline
    -> Planner
    -> Plan
    -> Tasks
    -> Execution
```

This package only creates the Task layer - no arrow in either diagram
above is wired up by this package. `Task` exists as a standalone value
object today; nothing in this codebase yet constructs one automatically
or reads one back out of a `Plan`.

---

## New Package

```
argus/task/
    __init__.py
    task.py
    status.py
    metadata.py
    builder.py
    interfaces.py
    exceptions.py
```

---

## Task

Immutable. Fields: `task_id` (defaulted, uuid4), `name` (defaulted,
`""`), `description` (defaulted, `""`), `status` (defaulted,
`TaskStatus.PENDING`), `metadata` (defaulted, a fresh `TaskMetadata`).
"The task contains no executable logic. It is purely a value object."
Unlike `PlanStep` (constructed directly by `Planner.add_step()`, with
no builder of its own, and therefore required, no-default
`description`/`required_capability` fields), `Task` has its own
dedicated `TaskBuilder` - the same "value object with a dedicated
builder" shape `CognitiveContext` (022), `PlanningSession` (023), and
`ExecutionTrace` (028) all use, each of which lets every field default
and leaves construction-time validation to the builder's own
`with_*()` methods. `Task()` with no arguments is therefore always
valid, representing an empty, unnamed task.

## TaskStatus

Immutable enumeration. A plain `Enum` (not a `str` subclass), mirroring
`argus.planner.plan.PlanStatus`'s own shape exactly. Five members:
`PENDING`, `READY`, `COMPLETED`, `FAILED`, `CANCELLED`, each with a
lowercase string value matching its own name. "Do not implement
transitions" - no method anywhere in `argus.task` moves a `Task` from
one `TaskStatus` to another; the default status a `TaskBuilder`
produces is `PENDING`, and nothing advances it further in Version 1.

## TaskMetadata

Immutable. Fields: `created_at` (defaulted, current UTC time),
`version` (defaulted, `TASK_METADATA_VERSION`), `correlation_id`
(defaulted, uuid4), `extra` (defaulted, wrapped in `MappingProxyType`).
"Mirror existing metadata conventions." This package's own explicit
field list ("created_at, correlation_id, version, extra") lists a
different relative order than `ContextMetadata`/`PlanningMetadata`/
`TraceMetadata` (022/023/028) all use - continuing the exact reasoning
Package 028 already applied to this identical tension with
`TraceMetadata`, this module declares its fields in the same relative
order its three siblings use (`created_at`, `version`,
`correlation_id`, `extra`), since "mirror existing metadata
conventions" is the dominant instruction and every field defaults, so
no declaration-order constraint forces one sequence over the other.

---

## TaskBuilder

The one mutable object in this package - "Builder is the only mutable
object" - mirroring `ContextBuilder`/`PlanningSessionBuilder`/
`TraceBuilder`'s (022/023/028) own shape and validation discipline.

- `with_name(name)` - validates a non-empty string (raising
  `InvalidTaskError` otherwise), overwrites the builder's own `name`,
  and returns `self`. A singular field - the last call before
  `build()` wins, not accumulated.
- `with_description(description)` - validates a string (empty strings
  are accepted - a description is legitimately optional elaboration),
  overwrites, returns `self`.
- `with_status(status)` - validates a `TaskStatus` instance, overwrites,
  returns `self`.
- `with_metadata(key, value)` - accumulates into the eventual
  `TaskMetadata.extra`, last-call-wins on repeated keys, the same rule
  `ContextBuilder`/`PlanningSessionBuilder`/`TraceBuilder`'s own
  `with_metadata()` already use.
- `build()` - returns an independent `Task` snapshot from the
  builder's current state. Callable more than once without mutating an
  earlier snapshot.

### Engineering Decision - with_name()/with_description() Beyond The Work Order's Own Four-Item List

This package's own Responsibilities list for `TaskBuilder` names
exactly four items: "create task, assign metadata, assign status,
build immutable Task" - it does not separately name "assign
name"/"assign description" as their own bullets. Read literally, this
could mean `TaskBuilder` has no supported way to ever set
`Task.name`/`Task.description` away from their own empty-string
defaults, which would leave the builder unable to produce a genuinely
populated `Task` - undermining its own stated purpose and leaving
`Task.name`/`Task.description` effectively dead fields for any caller
using the supported construction path.

Resolved by reading "create task" as the umbrella responsibility
encompassing a `Task`'s basic identity, and adding `with_name()`/
`with_description()` alongside the two explicitly-named `with_status()`/
`with_metadata()` - the same shape every other fluent builder in this
codebase already has: one `with_*()` method per field the built object
holds, not only the fields a work order happened to call out
individually. Flagged explicitly in `builder.py`'s own module docstring
as a documented reading, not a silent addition.

`ITaskBuilder` does not inherit `IService` - "No new services" -
mirroring `ICognitiveContextBuilder`/`IPlanningSessionBuilder`/
`ITraceBuilder`'s own identical choice; a builder has no meaningful
start/stop lifecycle, only a short, per-use existence.

---

## Dependency Graph

```
Task / TaskStatus / TaskMetadata
    depend on: nothing but each other (immutable value objects)

TaskBuilder
    depends on: nothing at construction time
```

Per the explicit Integration section: "Do not modify: Planner, Plan,
Pipeline, Response, Agent, Execution Trace." `argus/task/` imports
nothing from any of those six packages, and nothing outside
`argus/task/` imports from `argus/task/` either - this package has
zero inbound and zero outbound dependencies on the rest of the
codebase, confirmed via `git diff --stat` showing changes confined
entirely to `argus/task/` and four new test files.

---

## Bootstrap Integration

None. "No new services. No bootstrap changes." `argus/bootstrap.py` is
completely untouched by this package - confirmed via `git diff --stat
-- argus/bootstrap.py` showing zero lines changed, the second package
since Planning Session (023) for which that is true (after Execution
Trace, 028). `CORE_SERVICES_VERSION` remains `"0.2.8"`.

---

## IService Adoption

None. `ITaskBuilder` does not inherit `IService` - the same "not an
IService" shape Cognitive Context (022), Planning Session (023), and
Execution Trace (028) already established for infrastructure packages
that expand no service registry. No new entry was added to
`design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`, matching the
precedent already set by those same three packages.

---

## Events

No new `EventType` members. Neither `TaskBuilder` nor any
`argus.task` value object calls `self._publish()` or holds an
`IEventBus` reference - there is nothing in this package with a
collaborator to publish through in the first place.

---

## Repository Verification Note

The uploaded repository ("ArgusOS (28).zip") was verified against
this package's own general "verify repository state, verify version
consistency, verify HEAD/tag ancestry, run smoke validation"
pre-flight instruction. Findings: HEAD (`19c8148`, "Synchronize
repository version with v0.2.8 release") is a clean, single-commit
descendant of tag `v0.2.8` (which points to `783d24e`, "Implement
Package 028 Execution Trace"), confirmed via `git merge-base
--is-ancestor v0.2.8 HEAD`. `git diff v0.2.8..HEAD --stat` shows
exactly the expected one-line version-sync commit (`argus/bootstrap.py`,
1 insertion, 1 deletion) - no anomaly. `python -m pytest` passing
(1692 passed, 38 subtests); `python -m unittest discover -s tests`
passing (1604); `python -m unittest discover -s argus/tests` passing
(64); `python main.py` starting and shutting down cleanly (exit 0);
`CORE_SERVICES_VERSION == "0.2.8"` matching tag `v0.2.8`; `argus/task/`
confirmed absent from the repository prior to this package. All
confirmed before any Package 029 code was written.

---

## Files Created

```
argus/task/__init__.py
argus/task/task.py
argus/task/status.py
argus/task/metadata.py
argus/task/builder.py
argus/task/interfaces.py
argus/task/exceptions.py
factory/packages/029_TASK_MODEL.md
tests/test_task.py
tests/test_task_status.py
tests/test_task_metadata.py
tests/test_task_builder.py
```

## Files Modified

```
CHANGELOG.md, DEVLOG.md, IMPLEMENTATION_REPORT.md, factory/ROADMAP.md
```

No other file was created, deleted, moved, or modified. Per this
package's own explicit Integration section - "Do not modify: Planner,
Plan, Pipeline, Response, Agent, Execution Trace" - `argus/bootstrap.py`,
`argus/planner/`, `argus/planning/`, `argus/context/`,
`argus/conversation/`, `argus/memory/`, `argus/memory_integration/`,
`argus/knowledge/`, `argus/knowledge_graph/`, `argus/decision/`,
`argus/reasoning/`, `argus/pipeline/`, `argus/agent/`,
`argus/response/`, `argus/trace/`, `tests/test_bootstrap.py`,
`argus/tests/test_bootstrap.py`, and `argus/events/event_types.py`
were left completely untouched - confirmed via `git diff --stat`
showing zero lines changed in any of them.

---

## Test Results

New task suites:
```
python -m pytest tests/test_task.py tests/test_task_status.py tests/test_task_metadata.py tests/test_task_builder.py -q
64 passed in 0.06s
```

Canonical suite (`tests/`):
```
python -m unittest discover -s tests
Ran 1668 tests in 0.108s
OK
```

Per this package's explicit testing instruction:
```
python -m pytest
1756 passed, 38 subtests passed in 1.12s
```

The duplicate `argus/tests/` also verified passing standalone
(unaffected - not touched by this package):
```
python -m unittest discover -s argus/tests -p "test_*.py"
Ran 64 tests in 0.014s
OK
```

`python main.py`:
```
[INFO] argus: ArgusOS application started.
[INFO] argus: ArgusOS application shutting down.
```
Exit code 0.

---

## Coverage

Measured with `coverage.py`, `python -m coverage run -m pytest`:

```
--include="argus/task/*"
argus/task/__init__.py       7      0   100%
argus/task/builder.py       35      0   100%
argus/task/exceptions.py     2      0   100%
argus/task/interfaces.py    15      0   100%
argus/task/metadata.py      14      0   100%
argus/task/status.py         7      0   100%
argus/task/task.py          11      0   100%
TOTAL                        91      0   100%
```

100% coverage across the entire `argus/task/` package, reached on the
first measurement - no post-hoc gap-closing needed.

---

## Version 1 Limitations

- **`Task` is never produced by anything** - no `Plan`, `PlanStep`,
  `Planner`, or any other component in this codebase constructs a
  `Task`; it is available only to a caller holding a `TaskBuilder`
  directly. "Future packages will integrate Tasks into Plans."
- **`TaskStatus` values beyond `PENDING`** (`READY`, `COMPLETED`,
  `FAILED`, `CANCELLED`) **are reserved for future packages** - no
  Version 1 code ever produces them automatically, and "Do not
  implement transitions" means no method exists anywhere to move a
  `Task` between them either.
- **`TaskBuilder.build()` performs no "was `with_name()` ever called"
  check** - an unnamed `Task` (`name=""`) is a valid, buildable value,
  not an error.
- **`TaskMetadata.extra`'s `MappingProxyType` wrapping is not
  picklable/deep-copyable** via the standard library - an inherent
  limitation shared by every metadata class in this codebase
  (`ContextMetadata`, `PlanningMetadata`, `ResponseMetadata`,
  `TraceMetadata` all wrap `extra` the same way), newly documented
  here after being exercised for the first time by this package's own
  "serialization consistency" tests.
- **No execution, no scheduling, no workflows, no tools, no
  persistence, no concurrency** - unchanged from every prior package
  in this phase.
- The repository's stray `argus/` duplicate tree and legacy
  pre-Factory files remain unresolved, out of scope per the Founder's
  explicit repository rules.

---

## Future AI Integration

- A future package may extend `Plan`/`PlanStep` to reference `Task`
  objects directly, closing the "Tasks" arrow in this package's own
  Future Architecture diagram - deliberately out of scope here, since
  this package's own explicit Integration section instructs "Do not
  modify: Planner, Plan."
- A future execution/scheduling package should treat `Task` as its own
  stable input contract - `TaskStatus`'s reserved `READY`/`COMPLETED`/
  `FAILED`/`CANCELLED` members already anticipate the shape that
  future transition logic will need to produce, without this package
  itself guessing at what that logic should be.
- Any future persistence layer for Tasks should treat `Task`/
  `TaskStatus`/`TaskMetadata` as the stable schema to serialize - all
  three are already plain, immutable value objects with no behavior to
  strip out, modulo the `MappingProxyType` limitation noted above,
  which a future persistence layer would need to work around (for
  example, by serializing `dict(task.metadata.extra)` rather than the
  `TaskMetadata` object itself).

---

## Release Rules

Per the Founder's explicit instruction: no commit, tag, or push was
performed. `CORE_SERVICES_VERSION` was not changed by this package -
it remains `"0.2.8"`. This package is not reported as complete or
released - implementation ends after successful local verification;
final validation, integration, release, version update, commit, and
tag are the Founder's responsibility against the live repository.
