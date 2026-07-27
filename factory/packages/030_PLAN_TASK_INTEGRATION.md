# Implementation Package 030 - Plan Task Integration

## Objective

Extend the Planning domain so that a Plan owns an ordered collection
of immutable Task objects. "This package does not execute tasks. It
only allows the Planner to describe work at a finer level of detail."
Unlike Package 029 (Task Model), which was deliberately, completely
isolated and modified no pre-existing file, this package is the first
to connect `Task` to anything else in this codebase - "The Planner
owns Tasks, but does not perform them."

---

## Architectural Motivation

Package 029 introduced `Task` as a standalone value object with no
producer and no consumer anywhere in this codebase - "`Task` is never
produced by anything... Integrating Tasks into Plans is explicitly
deferred to a future package," per that package's own Known
Limitations. This package is that future package, for exactly one
integration: a Plan (and, as this document's own Engineering Decision
section explains, a PlanningSession) can now hold an ordered sequence
of Tasks alongside whatever it already held. No new capability is
introduced beyond storage and pass-through - "No planning logic
changes. No AI. No decomposition." - the Planner continues to build
Plans exactly as it always has; the only difference is that a caller
may now also hand it a list of Tasks to carry along for the ride.

---

## Architectural Position

Current architecture (per this package's own work order):

```
Planner -> Plan
```

New architecture (per this package's own work order):

```
Planner -> Plan -> Goals / Constraints / Metadata / Tasks
```

Tasks become part of the Plan.

This diagram's own field list - Goals, Constraints, Metadata, Tasks -
is the central interpretive problem this package had to resolve; see
Engineering Decision below.

---

## Engineering Decision: Plan vs. PlanningSession

The work order contains two sections that, read together, do not
describe the same object.

The section titled "Plan" says, literally: "Extend the existing
immutable: Plan. Add: tasks." Read as a bare class-name reference,
this points at `argus.planner.plan.Plan` - the object `Planner`
actually produces, stores, and returns from `create_plan()`,
`add_step()`, `get_plan()`, and every other pre-existing Planner
method.

But the Architectural Position diagram's own field list - "Goals /
Constraints / Metadata / Tasks" - does not match `Plan`'s actual
fields at all. `Plan` has never had `goals` or `constraints`; it has
`originating_intent`, `id`, `status`, `created_at`, `steps`, and
`metadata`. The diagram's field list matches `PlanningSession`
(Package 023) instead, field for field: `PlanningSession` already
holds `cognitive_context`, `goals`, `constraints`, and `metadata` -
exactly the diagram's own four nouns, once "cognitive_context" is set
aside as the one field the diagram's own arrow already accounts for
separately via "Planner ->".

The "Planning Builder" section deepens the same ambiguity rather than
resolving it: "Extend the existing PlanningBuilder. Add fluent
methods: with_task(task), with_tasks(tasks), clear_tasks()." No class
in this codebase is literally named `PlanningBuilder` - the actual
class is `PlanningSessionBuilder` (`argus/planning/builder.py`), the
one and only builder with "Builder" in its own name anywhere in the
Planning or Planner packages. `Plan` itself has no dedicated builder
at all; it is constructed directly by `Planner.create_plan()`. Read
literally, "the existing PlanningBuilder" can only be
`PlanningSessionBuilder` - which argues for the diagram's own
PlanningSession-shaped reading, in direct tension with the Plan
section's own literal class-name reading immediately above it.

**Resolution: implement `tasks` on both objects**, rather than picking
one interpretation and leaving the other's own literal instruction
unaddressed:

- `Plan` (`argus/planner/plan.py`) gains a `tasks` field, satisfying
  the Plan section's own literal "Extend the existing immutable:
  Plan. Add: tasks" instruction.
- `PlanningSession` (`argus/planning/session.py`) gains a `tasks`
  field, satisfying the Architectural Position diagram's own field
  list, and `PlanningSessionBuilder`
  (`argus/planning/builder.py`) gains `with_task()`/`with_tasks()`/
  `clear_tasks()`, satisfying the Planning Builder section's own
  literal "the existing PlanningBuilder" reading.
- `Planner.plan_session()` (`argus/planner/planner.py`) then carries
  `PlanningSession.tasks` through to the returned `Plan.tasks`
  unchanged - exactly mirroring the precedent Package 024 already
  established for `PlanningSession.constraints`, which
  `plan_session()` already records descriptively in the returned
  `Plan`'s own `metadata`, without `Plan` itself gaining a
  `constraints` field of its own. This single bridging step is what
  makes the "Planner" section's own instruction literally true no
  matter which object a reader assumes it is describing: "Update
  Planner so that Plans can contain Tasks... The Planner simply
  preserves whatever Tasks are supplied during construction."

This resolution was chosen over two rejected alternatives. Picking
only the Plan section's literal reading and ignoring the diagram would
mean `PlanningSessionBuilder` - the work order's own named builder -
never gains `with_task()`/`with_tasks()`/`clear_tasks()` at all, a
direct contradiction of an explicit method list. Picking only the
diagram's reading and ignoring the Plan section's literal class name
would mean the class named "Plan" in the work order's own vocabulary
never actually changes, a direct contradiction of "Extend the
existing immutable: Plan. Add: tasks." Implementing both, bridged by
the one carry-through method the Planner section explicitly describes,
is the only reading under which every sentence in the work order is
literally true simultaneously.

"Only the Planning package changes" is read broadly, as "the planning
domain" - both `argus/planning/` and `argus/planner/` - rather than
narrowly as the single directory literally named `planning`, since the
Planner section explicitly names "Planner" (a class that lives in
`argus/planner/`, not `argus/planning/`) as needing an update. This
broader reading is distinguished from, not a loosening of, the
explicitly-excluded packages: Agent, Pipeline, Response, Execution
Trace, Runtime, and Scheduler remain completely untouched, confirmed
via `git diff --stat` showing zero lines changed in any of them.

---

## Plan

Extended. New field: `tasks: Sequence[Task]`, declared after `steps`
and before `metadata`, defaulting to an empty tuple and wrapped in
`tuple()` in `__post_init__` - the identical immutability pattern
`steps` itself already uses. `Plan(originating_intent=...)` with no
`tasks` argument continues to produce a Plan with an empty `tasks`
tuple, exactly as before this package. Ordered, preserves insertion
order, immutable (frozen dataclass, tuple-wrapped sequence field).
`Plan` itself performs no duplicate-`task_id` rejection - consistent
with `Plan`'s own pre-existing behavior toward `steps` (which is
likewise never checked for duplicates at the dataclass level) and with
this codebase's established "validation lives in the builder/service,
not the value object" division of responsibility. Duplicate rejection
for `tasks` is enforced by `Planner._validate_tasks()` for any Plan
constructed via `Planner.create_plan()`/`plan_session()` - the only
supported way to construct a `Plan` with `tasks` populated outside of
direct, unvalidated dataclass construction.

---

## PlanningSession

Extended. New field: `tasks: Sequence[Task]`, declared after
`constraints` and before `metadata`, defaulting to an empty tuple and
wrapped in `tuple()` in `__post_init__` - the identical pattern
`goals`/`constraints` already use. `PlanningSession()` with no `tasks`
argument continues to produce a session with an empty `tasks` tuple.
Ordered, preserves insertion order, immutable.

---

## PlanningSessionBuilder

Extended with three new fluent methods, all returning `self`:

- `with_task(task)` - validates `task` is a `Task` instance, rejects a
  duplicate `task_id` against every `Task` already accumulated
  (identity-based duplicate detection, per this codebase's established
  id-based duplicate-prevention pattern already used by
  `CapabilityRegistry`/`PluginManager`), then appends. Accumulates
  across calls, exactly like `with_goal()`/`with_constraint()`.
- `with_tasks(tasks)` - validates `tasks` is a list or tuple, then
  delegates to `with_task()` once per item, in order - not a parallel
  validation path, so duplicate rejection (both within the batch and
  against anything already accumulated) is inherited automatically
  rather than reimplemented.
- `clear_tasks()` - resets the accumulated task list to empty. The
  first "reset a collection" method any builder in this codebase has
  ever exposed; `with_goal()`/`with_constraint()` have no equivalent
  `clear_goals()`/`clear_constraints()`, since the work order names
  `clear_tasks()` explicitly and no prior package has asked for the
  equivalent on any other collection field.

`build()` passes `tasks=tuple(self._tasks)` to the `PlanningSession`
constructor, alongside its own pre-existing `goals`/`constraints`/
`context`/`metadata` construction. The builder remains the only
mutable object in the Planning package - `Task` itself stays frozen;
only the builder's own internal accumulator list is mutated between
`with_task()` calls.

---

## Planner

`create_plan()` gained one new optional keyword parameter,
`tasks: Optional[Sequence[Task]] = None`, validated by a new private
helper, `_validate_tasks()`, and stored on the constructed `Plan`
unchanged. `_validate_tasks()` performs three checks: `tasks` must be
`None`, a list, or a tuple (anything else raises `InvalidPlanError`);
every item must be a `Task` instance (anything else raises
`InvalidPlanError`); no two items may share a `task_id` (a duplicate
raises `InvalidPlanError`, naming the offending id). `tasks=None`
(the default, matching every pre-030 call site unchanged) produces an
empty `tasks` tuple on the resulting `Plan`, identical to its pre-030
behavior.

`plan_session()` was updated to pass
`tasks=planning_session.tasks` through to its own internal
`create_plan()` call - the single line that fulfills "The Planner
simply preserves whatever Tasks are supplied during construction. No
planning logic changes. No AI. No decomposition." `plan_session()`
does not generate, decompose, or derive any `Task` from
`planning_session.goals`/`.constraints` - it carries forward exactly
whatever `Task` objects the caller already placed into the
`PlanningSession`, nothing more and nothing less.

`IPlanner.create_plan()`'s abstract method signature and docstring
were updated in lockstep with the concrete implementation, keeping
interface and implementation in sync per this codebase's established
convention (e.g. `IResponseEngine.build_response()` was updated
alongside `ResponseEngine.build_response()` in Package 028).

---

## Dependency Graph

```
argus.planner.plan (Plan)
    -> argus.task.task (Task)                [Package 030, typing only]
    -> argus.planner.step (PlanStep)          [pre-existing]
    -> argus.intent.intent (Intent)           [pre-existing]

argus.planning.session (PlanningSession)
    -> argus.task.task (Task)                [Package 030, typing only]
    -> argus.context.context (CognitiveContext) [pre-existing]
    -> argus.planning.goal (PlanningGoal)     [pre-existing]
    -> argus.planning.constraint (PlanningConstraint) [pre-existing]
    -> argus.planning.metadata (PlanningMetadata) [pre-existing]

argus.planning.builder (PlanningSessionBuilder)
    -> argus.task.task (Task)                [Package 030]
    -> argus.planning.session (PlanningSession) [pre-existing]
    -> argus.planning.exceptions (InvalidPlanningSessionError) [pre-existing]

argus.planner.planner (Planner)
    -> argus.task.task (Task)                [Package 030, typing only]
    -> argus.planner.plan (Plan)              [pre-existing]
    -> argus.planning.session (PlanningSession) [pre-existing, Package 024]
```

`argus.task` gains no new outbound dependency of its own - it remains,
as Package 029 left it, dependent on nothing but the Python standard
library and its own sibling modules. This package only adds inbound
dependencies *onto* `argus.task.task.Task` from four Planning/Planner
modules; nothing in `argus.task` was modified.

---

## Bootstrap Integration

None. `Plan`, `PlanningSession`, and `PlanningSessionBuilder` are not
`IService` implementations, and `Planner` is not gated by
`IService` either (an unchanged, pre-existing fact, not a decision
made by this package). `argus/bootstrap.py` was not touched -
confirmed via `git diff --stat -- argus/bootstrap.py` showing zero
lines changed. `CORE_SERVICES_VERSION` remains `"0.2.9"`.

---

## IService Adoption

None. This package introduces no new class of any kind - it extends
four existing, already-shipped classes, none of which is or has ever
been an `IService` implementation. No new entry was added to
`design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`.

---

## Events

None. `argus/events/event_types.py` was not modified - "No new
EventTypes." `Planner.create_plan()`/`plan_session()` continue to
publish exactly the same `PLAN_CREATED`/`PLAN_UPDATED` events they
always have; the payload each publishes is unchanged, since neither
event's payload has ever included `steps` or (now) `tasks` - only
`plan_id` and, for `PLAN_UPDATED`, a `change` descriptor.

---

## Repository Verification Note

Before writing any code, the uploaded repository ("ArgusOS (29).zip")
was verified fresh against this package's own general pre-flight
instruction. No anomaly was found - the sixteenth consecutive clean
pre-flight (015-030). HEAD (`14bb4fc`, "Synchronize repository version
with v0.2.9 release") is a clean, single-commit descendant of tag
`v0.2.9` (which points to `88f3e41`, "Implement Package 029 Task
Model"), confirmed via `git merge-base --is-ancestor v0.2.9 HEAD`.
`git diff v0.2.9..HEAD --stat` shows exactly the expected one-line
version-sync commit (`argus/bootstrap.py`, 1 insertion, 1 deletion).
`python -m pytest` passing (1756 passed, 38 subtests);
`python -m unittest discover -s tests` passing (1668);
`python -m unittest discover -s argus/tests` passing (64);
`python main.py` starting and shutting down cleanly (exit 0);
`CORE_SERVICES_VERSION == "0.2.9"` matching tag `v0.2.9`.

Per the Founder's explicit release rules, this implementation was
built, tested, and verified entirely within the supplied repository.
No `git commit`, `git tag`, push, or git-history modification of any
kind was performed, `CORE_SERVICES_VERSION` was not changed by this
package, and this package is not being reported as complete - final
validation, integration, release, tagging, and git operations are the
Founder's responsibility, to be performed against the live repository
after independent regression testing.

---

## Files Modified

```
argus/
    planner/
        plan.py                              (modified)
        planner.py                           (modified)
        interfaces.py                        (modified)
    planning/
        session.py                           (modified)
        builder.py                           (modified)
        interfaces.py                        (modified)
tests/
    test_plan.py                             (modified)
    test_planner.py                          (modified)
    test_planner_session_integration.py      (modified)
    test_planning_session.py                 (modified)
    test_planning_builder.py                 (modified)
CHANGELOG.md                                 (modified)
DEVLOG.md                                    (modified)
factory/ROADMAP.md                           (modified)
IMPLEMENTATION_REPORT.md                     (replaced)
```

No file outside this list was created, deleted, moved, or modified.
`argus/bootstrap.py`, `argus/task/`, `argus/agent/`, `argus/pipeline/`,
`argus/response/`, `argus/trace/`, `argus/runtime/`,
`argus/reasoning/`, `argus/decision/`, `argus/memory/`,
`argus/memory_integration/`, `argus/knowledge/`,
`argus/knowledge_graph/`, `argus/context/`, `argus/conversation/`,
`tests/test_bootstrap.py`, `argus/tests/test_bootstrap.py`, and
`argus/events/event_types.py` were left completely untouched -
confirmed via `git diff --stat` showing zero lines changed in any of
them.

---

## Files Created

```
factory/
    packages/
        030_PLAN_TASK_INTEGRATION.md          (new)
```

No new source module was created by this package - "Only the Planning
package changes," and every change to that domain took the form of
extending an already-shipped file, not adding a new one.

---

## Test Results

Modified Planning/Planner suites, standalone:
```
python -m pytest tests/test_plan.py tests/test_planner.py tests/test_planner_session_integration.py tests/test_planning_session.py tests/test_planning_builder.py -q
183 passed in 0.09s
```

Canonical suite (`tests/`):
```
python -m unittest discover -s tests
Ran 1709 tests in 0.137s
OK
```

Full suite, per this package's own explicit testing instruction:
```
python -m pytest
1797 passed, 38 subtests passed in 1.15s
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

New test coverage added, per this package's own explicit Testing
section - empty task list, single task, multiple tasks, duplicate
rejection, insertion order, immutability, builder methods, and planner
propagation - each exercised independently across all five modified
test files:

- `tests/test_plan.py` (+5): `tasks` defaults to empty, honors a
  single task, honors multiple tasks preserving insertion order,
  `tasks` is a tuple, `tasks` is immutable from its source list.
- `tests/test_planning_session.py` (+4): multiple tasks preserve
  insertion order, `tasks` defensive-copies its source list, `tasks`
  tuple cannot be mutated in place, `tasks` cannot be reassigned
  (frozen).
- `tests/test_planning_builder.py` (+14): `with_task()` on an empty
  builder, accumulation across calls preserving order, `with_tasks()`
  adding multiple in order, `with_tasks()` combining with prior
  `with_task()` calls, `clear_tasks()` emptying accumulated tasks,
  `clear_tasks()` then re-add, duplicate `task_id` rejection (same
  object, different object, within a `with_tasks()` batch, against a
  prior `with_task()` call), non-`Task`/`None`/non-list rejections,
  tuple acceptance.
- `tests/test_planner.py` (+11): `tasks` default to empty tuple on
  `create_plan()`, honors single/multiple tasks preserving order,
  `tasks` wrapped in a tuple, duplicate `task_id` rejection, non-`Task`
  item rejection, non-list/tuple rejection, tuple acceptance, "no
  tasks generated automatically," failed validation does not store or
  publish.
- `tests/test_planner_session_integration.py` (+9): empty session
  produces no tasks, single/multiple tasks carried through preserving
  order, tasks carried through alongside goals/constraints, Planner
  never generates its own tasks, Task remains frozen after
  `plan_session()`, session's own `tasks` tuple unaffected by
  `plan_session()`.

---

## Coverage

Measured with `coverage.py`,
`python -m coverage run -m pytest`:

| Module | Stmts | Miss | Cover |
|---|---|---|---|
| `argus/planner/__init__.py` | 6 | 0 | 100% |
| `argus/planner/exceptions.py` | 5 | 0 | 100% |
| `argus/planner/interfaces.py` | 23 | 0 | 100% |
| `argus/planner/plan.py` | 28 | 0 | 100% |
| `argus/planner/planner.py` | 118 | 0 | 100% |
| `argus/planner/step.py` | 14 | 0 | 100% |
| `argus/planning/__init__.py` | 8 | 0 | 100% |
| `argus/planning/builder.py` | 57 | 0 | 100% |
| `argus/planning/constraint.py` | 12 | 0 | 100% |
| `argus/planning/exceptions.py` | 2 | 0 | 100% |
| `argus/planning/goal.py` | 8 | 0 | 100% |
| `argus/planning/interfaces.py` | 24 | 0 | 100% |
| `argus/planning/metadata.py` | 14 | 0 | 100% |
| `argus/planning/session.py` | 20 | 0 | 100% |

100% coverage across every modified Planning/Planner file (339
statements total) - reached on the first measurement, no post-hoc
gap-closing needed.

---

## Version 1 Limitations

- **A `Plan`/`PlanningSession` constructed directly (not via
  `Planner`/`PlanningSessionBuilder`) performs no duplicate-`task_id`
  rejection of its own** - `Plan(originating_intent=..., tasks=[t1,
  t1_duplicate])` succeeds silently at the dataclass level, exactly
  like `Plan`'s own pre-existing, identical behavior toward duplicate
  `steps`. Duplicate rejection is enforced only by
  `Planner._validate_tasks()` and `PlanningSessionBuilder.with_task()`
  - the two supported construction paths.
- **Tasks are never generated, decomposed, or scheduled by anything
  in this package** - by design. "This package does not execute
  tasks." A `Plan`'s `tasks` collection is populated exclusively by
  whatever the caller explicitly supplies; no goal, constraint, or
  intent is ever translated into a `Task` automatically.
- **No task graph, dependency ordering, or workflow relationship
  between Tasks exists** - `Plan.tasks`/`PlanningSession.tasks` are
  flat, ordered sequences with no notion of one Task depending on
  another.
- **`clear_tasks()` has no counterpart on `goals`/`constraints`** -
  an intentional asymmetry, since this package's own work order names
  `clear_tasks()` explicitly and neither prior package's own work
  order asked for the equivalent on any other collection field.
- No execution, no scheduling, no workflows, no tools, no persistence,
  no concurrency - unchanged from every prior package in this phase.

---

## Future Execution Model

This package deliberately stops at storage and pass-through. The
future architecture diagram this package's own work order names -
"Planner -> Plan -> Goals / Constraints / Metadata / Tasks" - still
has no arrow leading out of "Tasks" toward anything that would
actually perform one. Package 029's own "Future architecture" diagram
(`User -> Agent -> Pipeline -> Planner -> Plan -> Tasks -> Execution`)
remains the more complete picture of where this is heading: a Plan now
genuinely owns its own Tasks (this package), but nothing yet reads
`Plan.tasks` back out for any purpose - no `AgentService`, no
`ResponseEngine`, no `ExecutionTrace` step references `Task` in any
way, confirmed via `git diff --stat` showing zero lines changed in any
of those packages. A future package integrating Tasks with execution
would need to introduce: a component that reads `Plan.tasks` and
dispatches each one to some execution mechanism, a status-transition
model for `TaskStatus` (currently a static enum with "no transitions"
per Package 029's own explicit constraint), and a way for execution
results to flow back into either the owning `Plan` or a future
`ExecutionTrace` step. None of that exists yet, and none of it was
introduced here - "The Planner owns Tasks, but does not perform
them."

---

## Release Rules

Per the Founder's standing release process, this package was
implemented and verified entirely within the supplied repository. No
`git commit`, `git tag`, push, or git-history modification of any
kind was performed. `CORE_SERVICES_VERSION` was not changed and
remains `"0.2.9"`. This package is not being reported as complete -
final validation, integration, version bump, commit, tag, and release
remain the Founder's responsibility, to be performed against the live
repository after independent regression testing.
