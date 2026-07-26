# Implementation Package 023 - Planning Session

## Objective

Give ArgusOS a first-generation Planning Session: an immutable
transport object that represents a single planning cycle -
encapsulating the CognitiveContext it operates over, this cycle's
planning goals and constraints, and descriptive metadata. "It
performs no planning. It executes no workflows. It is a transport
object only." Per the Founder's Package 023 work order, the Planner
does not consume it yet - "Package 023 introduces the abstraction
only" - and, like Package 022 immediately before it, this package
registers no new core service, publishes no new events, and leaves
`argus/bootstrap.py` completely untouched.

```
Conversation -> Memory Service -> Memory Integration -> Knowledge Graph -> Reasoning Engine -> Cognitive Context -> Planning Session -> Planner -> Validated Plan -> Agent Runtime
```

The Planning Session is the only component responsible for carrying
one planning cycle's CognitiveContext, goals, and constraints forward
as a single, immutable unit. It stores nothing beyond the fields it
is given; it never mutates a contained object, never invokes the
Planner, validates no goal, optimizes nothing, executes no workflow,
and owns no persistence of its own.

---

## Specification Note

No `design/specifications/PLANNING_SESSION.md` exists in the
repository - the same situation as Packages 002, 009-022. This
package is built directly from the Founder's explicit work order.

---

## Goal Model

`PlanningGoal` (`argus/planning/goal.py`) is an immutable value
object:

```
name: str                     (required)
goal_id: str = <uuid4>
description: str = ""
priority: int = 0
```

"Priority is descriptive only. No scheduling logic." Unlike
`DecisionRule.priority` (Package 021), which `DecisionEngine` actively
sorts by, `PlanningGoal.priority` is never read, compared, or sorted
by anything in this package - `PlanningSession.goals` always preserves
exactly the order `PlanningSessionBuilder.with_goal()` was called in
(see Architectural Decision 1).

---

## Constraint Model

`PlanningConstraint` (`argus/planning/constraint.py`) is an immutable
value object:

```
name: str                          (required)
constraint_id: str = <uuid4>
description: str = ""
metadata: Mapping[str, Any] = {}
```

"No validation logic." `PlanningConstraint` carries no callable,
expression, or any other mechanism capable of being evaluated against
anything - purely descriptive data a future package may choose to
interpret, once the Planner is instructed to consume PlanningSession.

---

## Metadata Model

`PlanningMetadata` (`argus/planning/metadata.py`) is an immutable
value object:

```
created_at: datetime = <now, UTC>
version: str = "1.0"
correlation_id: str = <uuid4>
extra: Mapping[str, Any] = {}
```

Directly reuses `argus.context.metadata.ContextMetadata`'s (Package
022) own reconciliation of the work order's two descriptions of
"metadata" - the Responsibilities section's generic "metadata" and
the dedicated Planning Metadata section's named fields ("creation
timestamp, version, correlation identifier") - into a single field:
the three named fields are system-assigned, `extra` is the open-ended
mapping a caller populates via
`PlanningSessionBuilder.with_metadata()`. This is the second
consecutive package to use this exact shape (see Architectural
Decision 2). `version` here is the Planning Session schema version,
unrelated to `CORE_SERVICES_VERSION` (`argus/bootstrap.py`).

---

## Session Model

`PlanningSession` (`argus/planning/session.py`) is an immutable value
object:

```
session_id: str = <uuid4>
cognitive_context: Optional[CognitiveContext] = None
goals: Sequence[PlanningGoal] = ()
constraints: Sequence[PlanningConstraint] = ()
metadata: PlanningMetadata = <fresh PlanningMetadata>
```

`cognitive_context` holds the actual, already-immutable
`CognitiveContext` (Package 022) itself; `goals`/`constraints` hold
the actual `PlanningGoal`/`PlanningConstraint` objects, not reference
strings pointing at them elsewhere - a deliberate contrast with
`CognitiveContext`'s own three "..._references" fields (see
Architectural Decision 3). Every field is immutable; sequences are
wrapped in `tuple`, matching every other value object in this
codebase. Like every other value object in this codebase,
`PlanningSession` performs no validation of its own - see
Architectural Decision 4.

---

## Builder Architecture

`PlanningSessionBuilder` (`argus/planning/builder.py`) implements
`IPlanningSessionBuilder`:

```
with_context(cognitive_context)     -> PlanningSessionBuilder
with_goal(goal)                     -> PlanningSessionBuilder
with_constraint(constraint)         -> PlanningSessionBuilder
with_metadata(key, value)           -> PlanningSessionBuilder
build()                             -> PlanningSession
```

- "Builder is mutable. PlanningSession is immutable. Each call to
  build() returns an independent immutable snapshot." Every `with_*`
  method validates its own argument, mutates this builder's private
  accumulator state, and returns `self`, so calls chain fluently.
- `with_goal()` and `with_constraint()` each accumulate across
  multiple calls (list fields); `with_context()` overwrites on each
  call (a single scalar field) - last call before `build()` wins.
  `with_metadata()` accumulates distinct keys and overwrites on a
  repeated key, the same last-call-wins rule (see Architectural
  Decision 5).
- `build()` performs no additional validation and constructs a fresh,
  independent `PlanningSession` (with a fresh `PlanningMetadata`) from
  the builder's current state every time it is called.

Directly mirrors `argus.context.builder.ContextBuilder`'s (Package
022) own shape, accumulation rules, and validation discipline - the
same builder pattern applied one layer further into the cognitive
pipeline.

---

## Session Lifecycle

```
        caller constructs PlanningSessionBuilder()
                    |
                    v
    zero or more with_*(...) calls, each:
           |                        |
      invalid input              valid input
           |                        |
           v                        v
  InvalidPlanningSessionError   accumulate into
    (raised immediately,          builder's private
     builder state                 state; return self
     unchanged)                    for chaining
                                     |
                                     v
                                caller calls build()
                                     |
                                     v
                     construct + return a fresh,
                     independent PlanningSession
                     (fresh PlanningMetadata) from
                     the builder's current state
```

`build()` may be called any number of times on the same builder,
including after further `with_*()` calls - each call returns its own
independent `PlanningSession` snapshot; earlier snapshots are never
retroactively affected. No event is published at any point in this
lifecycle - "No EventTypes."

---

## Dependency Graph

```
PlanningSession
    depends on -> CognitiveContext   (Package 022; typing only, for
                                       the cognitive_context field)
    depends on -> PlanningGoal        (this package)
    depends on -> PlanningConstraint  (this package)
    depends on -> PlanningMetadata    (this package)

PlanningSessionBuilder
    depends on -> PlanningSession     (this package)
    depends on -> CognitiveContext   (Package 022; with_context()'s
                                       own type check)

Planner, Decision Engine, Reasoning Engine, Agent Runtime
    do NOT depend on PlanningSession or PlanningSessionBuilder in
    Version 1 - "Planner shall not consume Planning Session yet."
```

No construction order entry exists in `bootstrap.py` for this
package - `PlanningSession`/`PlanningSessionBuilder` are plain value
objects any caller constructs directly, exactly like `CognitiveContext`
or `ReasoningQuery`, not a registered core service (see Architectural
Decision 6).

---

## Architectural Decisions

### 1. `PlanningGoal.priority` is descriptive only - never read by this package

"Priority is descriptive only. No scheduling logic." `PlanningSession.goals`
always preserves the exact order `with_goal()` was called in, regardless
of each goal's own `priority` value - unlike `DecisionRule.priority`
(Package 021), which `DecisionEngine.list_rules()` actively sorts by.
A future Planner integration may choose to interpret `priority` once
instructed to consume `PlanningSession`; this package assigns it no
behavior at all.

### 2. `PlanningMetadata` reuses `ContextMetadata`'s two-kinds-of-metadata reconciliation

The work order describes "metadata" two different ways - the
Responsibilities section's generic "metadata" and the dedicated
Planning Metadata section's specific named fields. Rather than adding
two separate metadata-shaped fields to `PlanningSession`,
`PlanningMetadata` holds both, directly reusing the shape
`argus.context.metadata.ContextMetadata` (Package 022) established for
the identical tension - the second consecutive package to use this
reconciliation, suggesting it is becoming a genuine codebase
convention rather than a one-off resolution.

### 3. `PlanningSession` holds live objects, not reference strings - a deliberate contrast with Package 022

`cognitive_context`, `goals`, and `constraints` each hold actual
objects (`CognitiveContext`, `PlanningGoal`, `PlanningConstraint`),
never bare identifier strings - unlike `CognitiveContext`'s own three
"..._references" fields (Package 022), which deliberately hold bare
identifier strings instead of live objects. The distinction is
resolved the same way it was there: by the work order's own field
naming. Package 022's work order named three fields "...references"
and one "...results"; this package's work order names no field
"...references" at all - "goals" and "constraints" read the same way
"reasoning_results" and "matched_rules" (Packages 020/021) already do
in this codebase: the actual objects, held directly. Holding the live
`CognitiveContext` costs nothing extra here, since `CognitiveContext`
is already fully immutable - "shall NOT mutate contained objects" is
true by construction, just by a different route than Package 022's
(an unmutatable object rather than a bare string with nothing to
mutate).

### 4. `PlanningSession`, `PlanningGoal`, and `PlanningConstraint` perform no validation of their own

Matches the "pure leaf" precedent set by every other value object in
this codebase; all validation lives in `PlanningSessionBuilder`
instead - the same division of responsibility
`argus.context.builder.ContextBuilder` (Package 022) established for
`CognitiveContext`.

### 5. `with_context()`/`with_metadata()` overwrite; `with_goal()`/`with_constraint()` accumulate

`cognitive_context` is a single scalar field, so calling
`with_context()` more than once simply replaces the previous value -
the same "last call wins" rule applied to repeated `with_metadata()`
calls using the same key. `with_goal()` and `with_constraint()` each
append to a `Sequence`-typed field, so repeated calls accumulate -
directly mirroring `ContextBuilder.with_conversation()`'s (022)
identical distinction.

### 6. No new core service, no bootstrap changes, no `IService`

Per this package's own explicit instruction: "This is not an
IService... No service registration. No lifecycle integration. No
EventBus changes." Directly reuses
`argus.context.interfaces.ICognitiveContextBuilder`'s (Package 022)
own resolution for the identical question - `IPlanningSessionBuilder`
extends plain `ABC`, matching both `ICognitiveContextBuilder` (022)
and `IConnector`'s (017) original precedent. `argus/bootstrap.py` was
not modified in any way by this package.

---

## Events

None. "No EventTypes. No lifecycle." No `with_*` method or `build()`
publishes anything - every operation either mutates this builder's
own private, in-process accumulator state or constructs a plain value
object, neither of which is the kind of externally-visible occurrence
this codebase's `EventType` convention exists to announce.

---

## IService Adoption

Not applicable. `IPlanningSessionBuilder` does not inherit `IService`
- the second consecutive package (after 022) not to register a new
core service, per explicit instruction.
`design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md` was not
modified by this package - it records only `IService` adopters, and
this package introduces none.

---

## Repository Verification Note

The uploaded repository ("ArgusOS (22).zip") was verified against
this package's own general "verify repository state, verify version
consistency, verify HEAD/tag ancestry, run smoke validation"
pre-flight instruction. Findings: HEAD (`990370e`, "Synchronize
repository version with v0.2.2 release") is a clean, single-commit
descendant of tag `v0.2.2` (which points to `642e1b2`, "Implement
Package 022 Cognitive Context"); `v0.2.1` also confirmed an ancestor
of HEAD via `git merge-base --is-ancestor`. `git diff v0.2.2..HEAD --stat`
shows exactly the expected one-line version-sync commit
(`argus/bootstrap.py`, 1 insertion, 1 deletion) - no anomaly.
`git status --short` showed a completely clean working tree.
`argus/context/` (Package 022) present with all expected files;
`python -m pytest` passing (1325 passed, 38 subtests); `python -m
unittest discover -s tests` passing (1237); `python -m unittest
discover -s argus/tests` passing (64); `python main.py` starting and
shutting down cleanly (exit 0); `CORE_SERVICES_VERSION == "0.2.2"`
matching tag `v0.2.2`. All confirmed before any Package 023 code was
written.

---

## Files Created

```
argus/
    planning/
        __init__.py
        session.py
        goal.py
        constraint.py
        metadata.py
        builder.py
        interfaces.py
        exceptions.py
tests/
    test_planning_session.py
    test_planning_builder.py
    test_planning_goal.py
    test_planning_constraint.py
    test_planning_metadata.py
```

## Files Modified

```
CHANGELOG.md, DEVLOG.md, IMPLEMENTATION_REPORT.md, factory/ROADMAP.md
```

No other file was modified. Per this package's own explicit
Constraints, `argus/bootstrap.py`, `argus/events/event_types.py`,
`tests/test_bootstrap.py`, `argus/tests/test_bootstrap.py`,
`argus/planner/`, `argus/decision/`, `argus/reasoning/`, and
`argus/context/` were left completely untouched - confirmed via `git
diff --stat` showing zero lines changed in any of them.

---

## Test Totals

1,309 tests passing via `python -m unittest discover -s tests` (1,237
from Packages 002-022, plus 15 new in `test_planning_session.py`, 20
new in `test_planning_builder.py`, 9 new in `test_planning_goal.py`, 11
new in `test_planning_constraint.py`, and 10 new in
`test_planning_metadata.py`). `python -m unittest discover -s
argus/tests` remains unchanged at 64 - this package touches no file
inside the duplicate `argus/tests/` tree, so no `CORE_SERVICE_NAMES`
sync was needed or performed. `python -m pytest` also passes: 1,397
passed, 38 subtests passed.

---

## Coverage

100% line coverage on every new module measured for this package:
`argus/planning/__init__.py`, `argus/planning/session.py`,
`argus/planning/goal.py`, `argus/planning/constraint.py`,
`argus/planning/metadata.py`, `argus/planning/builder.py`,
`argus/planning/interfaces.py`, and `argus/planning/exceptions.py` -
all 100%, no accepted gaps, reached on the first measurement.
`argus/bootstrap.py` and `argus/events/event_types.py` are not part
of this package's coverage scope, since neither was modified. Overall
repository coverage: 99% (unchanged from Package 022; remaining gaps
are pre-existing and out of scope).

---

## Known Limitations

- **No lifecycle, no service registration** - `PlanningSession`/
  `PlanningSessionBuilder` are plain value objects with no `IService`
  contract; nothing here is started, stopped, or has a status. See
  Architectural Decision 6.
- **No events** - this package publishes nothing; see the Events
  section above.
- **No persistence, no serialization** - a `PlanningSession` exists
  only in memory for as long as a caller holds a reference to it.
- **No goal validation, no plan optimization, no workflow execution** -
  "It performs no planning. It executes no workflows."
- **`PlanningGoal.priority` has no behavior** - descriptive only, never
  read or acted on anywhere in this package. See Architectural
  Decision 1.
- **`PlanningConstraint` carries no evaluable logic** - "No validation
  logic"; purely descriptive data.
- **The Planner does not yet consume the Planning Session** - per this
  package's own explicit "Planner shall not consume Planning Session
  yet" Constraint.
- No concurrency.
- The repository's stray `argus/` duplicate tree and legacy
  pre-Factory files remain unresolved, out of scope per the Founder's
  explicit repository rules.

---

## Future Expansion

- Wire the Planner (or a future orchestrating component) to accept and
  consume a `PlanningSession`, once a concrete requirement to do so
  exists - the diagram already places `PlanningSession` directly
  upstream of the Planner.
- Consider whether a future package should give `PlanningGoal.priority`
  actual behavior (for example, ordering goals for a Planner to
  consider) once a concrete consumer needs it - Version 1 deliberately
  keeps it purely descriptive.
- Consider whether `PlanningConstraint` should eventually carry
  evaluable logic (mirroring `DecisionRule.predicate`'s shape), once a
  future package's work order explicitly asks for constraint
  evaluation - Version 1 deliberately implements none.

---

## Release Rules

Per the Founder's explicit instruction: no commit, tag, or push was
performed. `CORE_SERVICES_VERSION` was not changed by this package -
it remains `"0.2.2"`. This package is not reported as complete or
released - implementation ends after successful local verification;
final validation, integration, release, version update, commit, and
tag are the Founder's responsibility against the live repository.
