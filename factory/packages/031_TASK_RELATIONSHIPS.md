# Implementation Package 031 - Task Relationships

## Objective

Extend the Task domain so that Tasks can describe immutable
relationships with other Tasks. "This package does not implement
scheduling, execution, or dependency resolution. It only introduces
the relationship model." Continuing directly from Package 030 (Plan
Task Integration), which connected `Task` to `Plan`/`PlanningSession`
without letting Tasks reference each other, this package introduces
the first Task-to-Task relationship - still purely descriptive,
still with no execution consequence of any kind.

---

## Architectural Motivation

Prior to this package, a `Task` (Package 029) was a fully isolated
value object - it could be held by a `Plan`/`PlanningSession` (Package
030), but had no way to describe how it related to any other `Task`.
Real work rarely consists of independent, unconnected units - one
Task commonly precedes another, follows another, blocks another, or
is simply related to another in some way worth recording. This
package introduces `TaskRelationship`, a new, standalone value object
that describes exactly one such connection between two Tasks, and
extends `Task` itself to hold an ordered collection of them. As with
every package in this phase, the relationship is data only - "The
relationship contains no logic. It is purely descriptive" - no
scheduling, ordering, or dependency-resolution consequence is
introduced anywhere in this package.

---

## Architectural Position

Current architecture:

```
Plan
 └── Tasks
```

New architecture:

```
Plan
 └── Tasks
      └── Relationships
```

A Task owns zero or more relationships to other Tasks. No arrow
changes anywhere above `Tasks` - `Planner`, `Plan` itself, and every
package this package's own Constraints name are untouched; this
package only adds one more layer beneath `Tasks`.

---

## New Package

```
argus/task_relationship/
    __init__.py
    relationship.py
    relationship_type.py
    metadata.py
    builder.py
    interfaces.py
    exceptions.py
```

---

## TaskRelationship

Immutable. Fields, in the work order's own listed order:
`relationship_id` (defaulted, uuid4), `source_task` (defaulted,
`None`), `target_task` (defaulted, `None`), `relationship_type`
(defaulted, `RelationshipType.RELATED`), `metadata` (defaulted, a
fresh `RelationshipMetadata`). "The relationship contains no logic.
It is purely descriptive." Every field defaults -
`TaskRelationship()` with no arguments is always valid, representing
an empty, unlinked relationship - see the Engineering Decision
section below for why every field defaults, including
`source_task`/`target_task`, rather than making them required.
`source_task`/`target_task` hold the actual `Task` objects directly,
not reference strings, mirroring `Plan.tasks`/`PlanningSession.tasks`
(030) and `PlanningSession.cognitive_context` (022/023)'s own
"objects, not references" precedent - a choice the work order's own
field names (`source_task`/`target_task`, not
`source_task_id`/`target_task_reference`) already settle. `Task`
itself performs no validation of the `TaskRelationship`s it is given
- see `TaskBuilder`'s own module docstring for where
duplicate-`relationship_id` rejection actually lives.

---

## RelationshipType

Immutable enumeration. A plain `Enum` (not a `str` subclass), four
members: `PRECEDES`, `FOLLOWS`, `RELATED`, `BLOCKS`, lowercase string
values matching each member's own name, mirroring
`TaskStatus`(029)/`PlanStatus`'s own shape. "Do not interpret them.
Do not infer behavior." - no code anywhere in this package or
`argus.task` branches on which member a given `TaskRelationship`
carries; ordering, dependency resolution, and any actual
"precedes implies scheduled first" consequence are explicitly out of
scope. `RelationshipType.RELATED` is `TaskRelationship`'s own default
- the most generic, non-directional member of the four, mirroring how
`TaskStatus.PENDING` serves as that enumeration's own neutral default.

---

## RelationshipMetadata

Immutable. Fields: `created_at`, `version`, `correlation_id`, `extra`
- mirrors `ContextMetadata`/`PlanningMetadata`/`TraceMetadata`/
`TaskMetadata`'s shape and field names exactly. The work order's own
field list ("created_at, correlation_id, version, extra") uses a
different relative order than these four siblings all share;
continuing the identical resolution Packages 028 and 029 already
applied to this same recurring tension, this module declares fields
in the siblings' own shared order, not the order listed here - "mirror
existing metadata conventions" is the dominant instruction, and since
every field defaults, no ordering constraint forces one sequence over
the other.

---

## RelationshipBuilder

Mutable, fluent builder - the only mutable object in this package.
`with_source_task(task)`/`with_target_task(task)` validate a `Task`
instance and overwrite (last call wins); `with_type(relationship_type)`
validates a `RelationshipType` instance and overwrites;
`with_metadata(key, value)` accumulates into the eventual
`RelationshipMetadata.extra`, last-call-wins on repeated keys;
`build()` returns an independent `TaskRelationship` snapshot.
`with_source_task()`/`with_target_task()` are included beyond this
package's own four-item Responsibilities list ("create relationship,
assign metadata, assign type, build immutable TaskRelationship") - see
the Engineering Decision section below. Neither `with_source_task()`
nor `with_target_task()` validates the given `Task` against whatever
the other one already holds - a `TaskRelationship` whose `source_task`
and `target_task` are the same `Task` is not rejected. `build()`
performs no completeness check - a `TaskRelationship` built without
ever calling `with_source_task()`/`with_target_task()` still has
`source_task=None`/`target_task=None`, the empty default, not an
error.

---

## Engineering Decision

Two design questions in this package had no single, unambiguous
answer directly stated by the work order, and both were resolved by
reasoning from this codebase's own established precedent rather than
guessing.

**Should `source_task`/`target_task` default to `None`, or be
required fields with no default?** `TraceStep` (028) - this
codebase's closest surface-level analogue, a leaf item describing one
occurrence - makes its own `component`/`action` fields required, with
no builder of its own, reasoning explicitly that "an empty placeholder
string would misrepresent which stage occurred." The identical
argument applies to `TaskRelationship`: a relationship with no source
or target is not a meaningful relationship. But `TraceStep` and
`TaskRelationship` belong to different architectural families.
`TraceStep` is constructed directly by `TraceBuilder.with_step()`,
with no dedicated builder of its own; this package's own work order
explicitly creates a standalone `RelationshipBuilder`, placing
`TaskRelationship` in the same family as `Task`(029)/
`PlanningSession`(023)/`CognitiveContext`(022)/`ExecutionTrace`(028) -
every one of which lets every field default and relies entirely on
its own dedicated builder for validation, never on required
dataclass fields. Consistency with that family's own established
convention, not `TraceStep`'s, governs here:
`source_task`/`target_task` both default to `None`, following
exactly the same pattern `PlanningSession.cognitive_context` already
uses for a single optional object reference.

**Should `RelationshipBuilder` gain `with_source_task()`/
`with_target_task()`, given they are not individually named in the
work order's own four-item Responsibilities list?** This is the
identical shape of gap Package 029 already faced with `TaskBuilder`'s
own "create task" bullet silently omitting "assign name"/"assign
description." Resolved the same way a second time: "create
relationship" is read as the umbrella responsibility encompassing a
`TaskRelationship`'s own two Task references, since a builder unable
to ever set `source_task`/`target_task` away from their own `None`
defaults could not actually build a meaningful relationship at all -
the entire reason `RelationshipBuilder` exists.

---

## Integration

`Task` (`argus/task/task.py`) extended with a new field:
`relationships: Sequence[TaskRelationship]`, declared after `status`
and before `metadata` - continuing Package 030's own "insert the new
collection field before metadata, so metadata stays the last-declared
field" precedent (`Plan.tasks`/`PlanningSession.tasks`) exactly.
Ordered, immutable (wrapped in `tuple()` in a newly-added
`__post_init__` - `Task` had none before this package), defaults to
an empty tuple, preserves insertion order. Duplicate rejection is
enforced in `TaskBuilder`, never in `Task` itself - consistent with
this codebase's established "validation lives in the builder/service,
not the value object" division of responsibility, and with `Plan`'s
own pre-existing, identical non-rejection of duplicate `steps`/`tasks`
at the dataclass level.

`TaskBuilder` (`argus/task/builder.py`) extended with three new
methods, mirroring `PlanningSessionBuilder`'s own identically-shaped
`with_task()`/`with_tasks()`/`clear_tasks()` (Package 030) one layer
down: `with_relationship(relationship)` validates and appends,
rejecting a duplicate `relationship_id` against every
`TaskRelationship` already accumulated (identity-based duplicate
detection, the same policy Package 030 applied to
`Plan.tasks`/`PlanningSession.tasks`); `with_relationships(relationships)`
delegates to `with_relationship()` once per item, in order - not a
parallel validation path; `clear_relationships()` resets the
accumulated relationship list to empty. `build()` now passes
`relationships=tuple(self._relationships)` to the `Task` constructor.

`ITaskBuilder` (`argus/task/interfaces.py`) gained the matching three
abstract methods, keeping interface and implementation in sync per
this codebase's established convention.

No Planner changes. No Plan changes. No Execution changes - "Do not
modify: Agent, Pipeline, Response, Execution Trace, Runtime, Scheduler"
(the same six packages Package 030 was told to leave untouched) plus
`Planner`/`Plan` themselves, all confirmed untouched via `git diff
--stat` showing zero lines changed in any of them.

---

## Avoiding A Circular Import

`TaskRelationship` depends on `Task` (for its own
`source_task`/`target_task` fields) - a real, unavoidable dependency,
since a relationship is meaningless without the Tasks it connects.
`Task` now depends on `TaskRelationship` too (for its own
`relationships` field) - a genuine two-way dependency at the package
level. Resolved without restructuring either package: `argus/task/task.py`
imports `TaskRelationship` only under `typing.TYPE_CHECKING` (never
evaluated at runtime) and spells the field's own annotation as a
forward-reference string, `Sequence["TaskRelationship"]`. Only
`argus/task/builder.py` (which needs `TaskRelationship` for real,
runtime `isinstance()` validation inside `with_relationship()`)
imports it directly at runtime - not circular, since
`argus.task.task` never imports `argus.task.builder`, and
`argus.task_relationship.relationship` never imports
`argus.task.builder` either. The "cycle" exists only in the type-
annotation graph, never in the actual runtime import graph.

---

## Dependency Graph

```
argus.task_relationship.relationship (TaskRelationship)
    -> argus.task.task (Task)                              [real, runtime]
    -> argus.task_relationship.relationship_type (RelationshipType)
    -> argus.task_relationship.metadata (RelationshipMetadata)

argus.task_relationship.builder (RelationshipBuilder)
    -> argus.task.task (Task)                              [real, runtime]
    -> argus.task_relationship.relationship (TaskRelationship)
    -> argus.task_relationship.relationship_type (RelationshipType)
    -> argus.task_relationship.metadata (RelationshipMetadata)
    -> argus.task_relationship.exceptions (InvalidTaskRelationshipError)
    -> argus.task_relationship.interfaces (IRelationshipBuilder)

argus.task_relationship.interfaces (IRelationshipBuilder)
    -> argus.task.task (Task)                              [real, runtime]
    -> argus.task_relationship.relationship (TaskRelationship)
    -> argus.task_relationship.relationship_type (RelationshipType)

argus.task.task (Task)
    -> argus.task_relationship.relationship (TaskRelationship)  [TYPE_CHECKING only]

argus.task.builder (TaskBuilder)
    -> argus.task_relationship.relationship (TaskRelationship)  [real, runtime]

argus.task.interfaces (ITaskBuilder)
    -> argus.task_relationship.relationship (TaskRelationship)  [real, runtime]
```

`argus.task_relationship.metadata` and
`argus.task_relationship.relationship_type` remain pure,
dependency-free leaves, matching every other metadata/enum module in
this codebase.

---

## Bootstrap Integration

None. `TaskRelationship`, `RelationshipType`, `RelationshipMetadata`,
and `RelationshipBuilder` are not `IService` implementations.
`argus/bootstrap.py` was not touched - confirmed via `git diff --stat
-- argus/bootstrap.py` showing zero lines changed. `CORE_SERVICES_VERSION`
remains `"0.3.0"`.

---

## IService Adoption

None. `IRelationshipBuilder` does not inherit `IService` - the same
"not an IService" shape `ICognitiveContextBuilder`(022)/
`IPlanningSessionBuilder`(023)/`ITraceBuilder`(028)/`ITaskBuilder`(029)
already established for infrastructure packages that expand no
service registry. No new entry was added to
`design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`.

---

## Events

None. `argus/events/event_types.py` was not modified - "No new
EventTypes." Nothing in this package publishes any event; `Task`,
`TaskRelationship`, and their respective builders have no `IEventBus`
dependency of any kind.

---

## Repository Verification Note

Before writing any code, the uploaded repository ("ArgusOS (30).zip")
was verified fresh against this package's own general pre-flight
instruction. No anomaly was found - the seventeenth consecutive clean
pre-flight (015-031). HEAD (`5190056`, "Synchronize repository version
with v0.3.0 release") is a clean, single-commit descendant of tag
`v0.3.0` (which points to `2b64606`, "Implement Package 030 Plan Task
Integration"), confirmed via `git merge-base --is-ancestor v0.3.0
HEAD`. `git diff v0.3.0..HEAD --stat` shows exactly the expected
one-line version-sync commit (`argus/bootstrap.py`, 1 insertion, 1
deletion) - `CORE_SERVICES_VERSION` moved from `"0.2.9"` to `"0.3.0"`,
a minor version bump rather than a patch increment, the Founder's own
release choice following Package 030's integration.
`python -m pytest` passing (1797 passed, 38 subtests);
`python -m unittest discover -s tests` passing (1709);
`python -m unittest discover -s argus/tests` passing (64);
`python main.py` starting and shutting down cleanly (exit 0);
`CORE_SERVICES_VERSION == "0.3.0"` matching tag `v0.3.0`.

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
    task_relationship/
        __init__.py                          (new)
        relationship.py                      (new)
        relationship_type.py                 (new)
        metadata.py                          (new)
        builder.py                           (new)
        interfaces.py                        (new)
        exceptions.py                        (new)
factory/
    packages/
        031_TASK_RELATIONSHIPS.md            (new)
tests/
    test_task_relationship.py                (new)
    test_relationship_builder.py             (new)
    test_relationship_metadata.py            (new)
    test_relationship_type.py                (new)
```

---

## Files Modified

```
argus/
    task/
        task.py                              (modified)
        builder.py                           (modified)
        interfaces.py                        (modified)
tests/
    test_task.py                             (modified)
    test_task_builder.py                     (modified)
CHANGELOG.md                                 (modified)
DEVLOG.md                                    (modified)
factory/ROADMAP.md                           (modified)
IMPLEMENTATION_REPORT.md                     (replaced)
```

No file outside these two lists was created, deleted, moved, or
modified. `argus/bootstrap.py`, `argus/planner/`, `argus/planning/`,
`argus/agent/`, `argus/pipeline/`, `argus/response/`, `argus/trace/`,
`argus/runtime/`, `argus/reasoning/`, `argus/decision/`,
`argus/memory/`, `argus/memory_integration/`, `argus/knowledge/`,
`argus/knowledge_graph/`, `argus/context/`, `argus/conversation/`,
`tests/test_bootstrap.py`, `argus/tests/test_bootstrap.py`, and
`argus/events/event_types.py` were left completely untouched -
confirmed via `git diff --stat` showing zero lines changed in any of
them.

---

## Test Results

New task_relationship suites:
```
python -m pytest tests/test_task_relationship.py tests/test_relationship_builder.py tests/test_relationship_metadata.py tests/test_relationship_type.py -q
67 passed in 0.06s
```

Modified Task suites:
```
python -m pytest tests/test_task.py tests/test_task_builder.py -q
72 passed in 0.05s
```

Canonical suite (`tests/`):
```
python -m unittest discover -s tests
Ran 1802 tests in 0.140s
OK
```

Per this package's own explicit testing instruction:
```
python -m pytest
1890 passed, 38 subtests passed in 1.21s
```

The duplicate `argus/tests/` also verified passing standalone
(unaffected - not touched by this package):
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

New test coverage, per this package's own explicit Testing section -
empty relationships, one relationship, many relationships, insertion
order, immutability, duplicate rejection, builder behavior - added
across both new and modified test files:

- `tests/test_task_relationship.py` (21 tests, new): defaults, all
  fields set, no-logic field-set/method-surface checks, immutability
  of every field, "do not interpret" (every RelationshipType member
  accepted identically, same Task as source and target not rejected),
  invalid construction, serialization consistency (scalar fields and
  RelationshipType/RelationshipMetadata.extra independently, per the
  same MappingProxyType limitation documented since Package 029),
  equality.
- `tests/test_relationship_builder.py` (28 tests, new): identity/not-
  an-IService, `with_source_task()`/`with_target_task()`/`with_type()`/
  `with_metadata()` chaining/overwrite/validation, same-task-as-source-
  and-target not rejected, `build()` completeness/independence/full
  chain.
- `tests/test_relationship_metadata.py` (10 tests, new): defaults,
  field-order mirroring, `extra` wrapping/defensive-copy/immutability,
  dataclass immutability, equality.
- `tests/test_relationship_type.py` (8 tests, new): plain-Enum shape,
  four members, values, no-interpretation (no methods beyond Enum
  machinery), singleton/equality.
- `tests/test_task.py` (+9): empty/one/many relationships preserving
  insertion order, tuple-wrapping, immutability from source list and
  in place, field cannot be reassigned, a relationship may reference
  the owning Task itself (not rejected).
- `tests/test_task_builder.py` (+17): `with_relationship()`/
  `with_relationships()`/`clear_relationships()` across empty/single/
  multiple/duplicate/non-TaskRelationship/non-list cases, full chain
  now includes a relationship.

---

## Coverage

Measured with `coverage.py`,
`python -m coverage run -m pytest`:

| Module | Stmts | Miss | Cover |
|---|---|---|---|
| `argus/task/__init__.py` | 7 | 0 | 100% |
| `argus/task/builder.py` | 53 | 0 | 100% |
| `argus/task/exceptions.py` | 2 | 0 | 100% |
| `argus/task/interfaces.py` | 22 | 0 | 100% |
| `argus/task/metadata.py` | 14 | 0 | 100% |
| `argus/task/status.py` | 7 | 0 | 100% |
| `argus/task/task.py` | 15 | 0 | 100% |
| `argus/task_relationship/__init__.py` | 7 | 0 | 100% |
| `argus/task_relationship/builder.py` | 38 | 0 | 100% |
| `argus/task_relationship/exceptions.py` | 2 | 0 | 100% |
| `argus/task_relationship/interfaces.py` | 16 | 0 | 100% |
| `argus/task_relationship/metadata.py` | 14 | 0 | 100% |
| `argus/task_relationship/relationship.py` | 13 | 0 | 100% |
| `argus/task_relationship/relationship_type.py` | 6 | 0 | 100% |

100% coverage across the entire new `argus/task_relationship/`
package (96 statements) and across every modified `argus/task/`
module (120 statements) - reached on the first measurement, no
post-hoc gap-closing needed.

---

## Version 1 Limitations

- **`Task` performs no duplicate-`relationship_id` rejection of its
  own** - `Task(relationships=[r1, r1_duplicate])` succeeds silently
  at the dataclass level, exactly like `Plan`'s own pre-existing,
  identical behavior toward duplicate `steps`/`tasks`. Duplicate
  rejection is enforced only by `TaskBuilder.with_relationship()`.
- **A `TaskRelationship` may reference the same `Task` as both its
  `source_task` and `target_task`** - not rejected, per "Do not
  interpret them. Do not infer behavior."
- **No dependency graph, cycle detection, or ordering semantics exist
  anywhere** - `Task.relationships` is a flat, ordered sequence; a
  `PRECEDES` relationship carries no more actual consequence than a
  `RELATED` one. "This package does not implement scheduling,
  execution, or dependency resolution."
- **`RelationshipType.RELATED` being the default is itself a
  judgment call, not a work-order-stated default** - the work order
  lists the four members but never states which (if any) should be
  the default; `RELATED` was chosen as the most generic, non-
  directional member, mirroring `TaskStatus.PENDING`'s own role as a
  neutral default.
- **Nothing yet reads `Task.relationships` back out for any
  purpose** - no `Planner`, `Plan`, `AgentService`, `ResponseEngine`,
  or `ExecutionTrace` step references `TaskRelationship` in any way.
- No execution, no scheduling, no persistence, no concurrency -
  unchanged from every prior package in this phase.

---

## Future Graph Evolution

`Task.relationships` today is a flat, per-Task list with no shared
identity across Tasks - if Task A holds a `PRECEDES` relationship
pointing at Task B, Task B does not automatically hold any
corresponding `FOLLOWS` relationship pointing back at A; nothing in
this package inserts, infers, or maintains a reciprocal edge. A future
package building an actual dependency graph over these relationships
would need to introduce: a graph-construction step that walks every
Task's own `relationships` and assembles a genuine directed graph
(likely reusing `argus.knowledge_graph`'s own existing
`Entity`/`Relationship` machinery, or a purpose-built equivalent),
cycle detection (nothing here prevents A `PRECEDES` B `PRECEDES` A),
and - only once a graph exists - the first genuine scheduling
consequence any `RelationshipType` member has ever had. None of that
exists yet, and none of it was introduced here. Combined with Package
030's own still-open "Future Execution Model" (`Plan -> Tasks ->
Execution`), the fuller target shape now reads: `Plan -> Tasks ->
Relationships -> [future: Task Graph] -> Execution` - one more named,
unbuilt segment for a future package to target.

---

## Release Rules

Per the Founder's standing release process, this package was
implemented and verified entirely within the supplied repository. No
`git commit`, `git tag`, push, or git-history modification of any
kind was performed. `CORE_SERVICES_VERSION` was not changed and
remains `"0.3.0"`. This package is not being reported as complete -
final validation, integration, version bump, commit, tag, and release
remain the Founder's responsibility, to be performed against the live
repository after independent regression testing.
