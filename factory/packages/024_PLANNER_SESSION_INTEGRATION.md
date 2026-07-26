# Implementation Package 024 - Planner Session Integration

## Objective

Introduce `PlanningSession` awareness into the Planner while
maintaining complete backward compatibility. "This package is an
integration package. No planning behavior shall change. No plan
generation shall change. No execution behavior shall change." Unlike
Packages 022-023, which each introduced a new, standalone,
zero-dependency-on-existing-code package, Package 024 modifies an
existing package (`argus/planner/`) - the first time since Package
018 (Knowledge Graph's own arrival alongside the pre-existing Planner)
that a later package's own Constraints section explicitly requires
touching a package this codebase has shipped and tested since Package
015.

```
Conversation -> Memory -> Knowledge -> Reasoning -> Context -> Planning Session -> Planner -> Validated Plan -> Runtime
```

"The Planner shall now recognize `PlanningSession` as a first-class
input." Concretely, this means one new public method -
`Planner.plan_session()` - added alongside every pre-existing
`IPlanner` method, none of which changed.

---

## Specification Note

No `design/specifications/PLANNER_SESSION_INTEGRATION.md` exists in
the repository - the same situation as Packages 002, 009-023. This
package is built directly from the Founder's explicit work order,
which itself amends `factory/packages/015_PLANNER.md`'s own scope
rather than introducing an unrelated new package.

---

## Delegation Architecture

`plan_session(planning_session)` does exactly three things, in order,
and nothing else:

```
1. Synthesize an Intent from the session
   (PlanningSession carries no Intent of its own - see
   "Why A Synthetic Intent" below)
2. self.create_plan(intent, metadata=<session metadata>)
3. self.add_step(plan.id, ...) once per planning_session.goal, in order
```

Every event this produces - `PLAN_CREATED` once, `PLAN_UPDATED` once
per goal - is published by `create_plan()`/`add_step()` themselves,
exactly as it would be for any other caller of those two methods.
`plan_session()` itself publishes nothing directly and contains no
independent planning algorithm of any kind - "No duplicate planning
logic" is satisfied by construction: there is no second, parallel
implementation of "how a Plan gets built," only a second, higher-level
way to invoke the one that already existed.

```
        caller calls plan_session(planning_session)
                    |
                    v
        isinstance(planning_session, PlanningSession)?
           |                              |
          no                             yes
           |                              |
           v                              v
    InvalidPlanError            synthesize Intent
    (raised immediately,        (IntentType.UNKNOWN,
     nothing created)            confidence=0.0)
                                          |
                                          v
                              self.create_plan(intent, metadata=...)
                              -> publishes PLAN_CREATED
                                          |
                                          v
                          for each goal in planning_session.goals:
                              self.add_step(plan.id, ...)
                              -> publishes PLAN_UPDATED
                                          |
                                          v
                                   return final Plan
```

---

## Why A Synthetic Intent

`create_plan()` requires a real `Intent` instance - `Plan
.originating_intent: Intent` has no default, matching every
pre-existing `create_plan()` caller's own requirement. `PlanningSession`
carries no `Intent` anywhere in its own structure (nor does the
`CognitiveContext` it holds - see `factory/packages/022_COGNITIVE_CONTEXT.md`'s
own field list), so `plan_session()` must synthesize one. This
deliberately uses `IntentType.UNKNOWN` with `confidence=0.0` rather
than fabricate a classification the session never actually contained,
directly matching `Intent`'s own "Unrecognized input always classifies
as UNKNOWN - parsing a valid string never fails" precedent
(`argus/intent/intent.py`). The session's own `session_id` (and, when
present, its `cognitive_context`'s `context_id`) are carried through
in the synthetic `Intent`'s `parameters` mapping for traceability - the
same "pass real identifying data through an existing field" approach
Package 016's own synthetic-Intent-per-step solution used for a
related problem (see `DEVLOG.md`'s Package 016 entry).

---

## Goal-to-Step and Constraint-to-Metadata Mapping

Each `PlanningGoal` becomes exactly one `PlanStep`:

| PlanningGoal field | PlanStep field | Rule |
|---|---|---|
| `description` (may be `""`) | `description` | goal's `description` if non-empty, else goal's `name` (`PlanStep.description` must be non-empty per `add_step()`'s own validation) |
| `name` | `required_capability` | direct - see rationale below |
| (none) | `order` | assigned by `add_step()` itself, exactly as always |
| (none) | `optional` | defaults to `False`, matching `add_step()`'s own default |
| `goal_id`, `priority` | `metadata` | both carried through so neither is silently dropped |

`PlanningGoal.name` becomes `required_capability` because
`PlanningGoal` has no field more specifically analogous to "which
Capability satisfies this goal" - its one other identifying string
field is the most direct, deterministic choice available, the same
category of "derive an id from an existing field rather than inventing
new state" resolution Package 019's `MemoryMapper`
(`f"memory:{key}"`) and this same package's own synthetic-Intent
choice above both use for a related problem.

`PlanningConstraint`s are never turned into `PlanStep`s - a constraint
describes a limit, not an action to take, which is not what a
`PlanStep` represents. Instead, every constraint's `constraint_id`/
`name`/`description` is recorded as a plain, descriptive list under
the created Plan's own `metadata["constraints"]`, alongside
`metadata["planning_session_id"]` (always present) and
`metadata["cognitive_context_id"]` (present only when
`planning_session.cognitive_context` is not `None`). A session with no
goals and no constraints produces a Plan with zero steps and an empty
`constraints` tuple in its metadata - the same "vacuously fine,
nothing to check" treatment `validate_plan()` already gives an empty
Plan.

---

## Backward Compatibility

Every pre-existing `IPlanner` method - `create_plan()`, `add_step()`,
`remove_step()`, `reorder_steps()`, `validate_plan()`, `get_plan()`,
`list_plans()` - is completely unchanged: same signature, same
behavior, same events, same exceptions. `plan_session()` is purely
additive; nothing about the pre-existing API had to change to
accommodate it, and nothing in this package's own diff touches any of
those seven methods' bodies. Verification: all 52 pre-existing tests
in `tests/test_planner.py` pass unchanged, with zero modifications to
that file. See "Backward Compatibility Verification" below for the
exact commands run.

---

## Migration Strategy

There is no migration required - existing callers of `create_plan()`/
`add_step()`/etc. continue exactly as before, with zero code changes
needed on their part. A caller that wants to adopt `PlanningSession`
as an input simply switches from manually calling `create_plan()` +
one or more `add_step()` calls to a single `plan_session()` call once
it has a `PlanningSession` available (once a future package wires the
Reasoning Engine/Cognitive Context/Planning Session pipeline together
end-to-end - "Planner shall not consume Planning Session yet" only
describes automatic pipeline wiring, which this package does not add;
`plan_session()` itself is available to any caller starting now).
Both entry points remain permanently available side by side - "This
package introduces an additional interface - not a replacement."

---

## Dependency Graph

```
Planner
    depends on -> IEventBus              (Package 003; unchanged)
    depends on -> ICapabilityRegistry    (Package 013; unchanged)
    depends on -> Intent                 (Package 009; unchanged)
    depends on -> PlanningSession        (Package 023; NEW - the
                                           immutable contract only)

Planner shall NOT depend on:
    argus.planning.builder      (PlanningSessionBuilder)
    argus.planning.metadata     (PlanningMetadata)
    argus.planning.exceptions   (PlanningError, InvalidPlanningSessionError)
```

`plan_session()` raises this package's own pre-existing
`InvalidPlanError` for malformed input - exactly the same exception
`create_plan()` already raises for a non-`Intent` argument. No new
exception type was introduced, and none of `argus.planning`'s own
exception types are ever caught, raised, or referenced anywhere in
`argus/planner/`. "Use only the immutable contract."

`PlanningGoal`/`PlanningConstraint` are accessed only via attribute
access on items already inside `planning_session.goals`/`.constraints`
(never imported, never `isinstance`-checked individually) - the
Dependency Rules name `PlanningSession` as the one thing Planner may
depend on, and `PlanningSession`'s own `__post_init__` already
guarantees `goals`/`constraints` are tuples of whatever the caller
supplied, so no further per-item type-checking was added inside
`plan_session()` itself.

---

## Architectural Decisions

### 1. `plan_session()` synthesizes an `Intent` rather than requiring one

Since neither `PlanningSession` nor `CognitiveContext` carries an
`Intent`, and `create_plan()`'s own contract requires one, a synthetic
`Intent(name=IntentType.UNKNOWN, confidence=0.0, parameters={...})` is
constructed internally - never exposed as a separate step a caller
must perform themselves. See "Why A Synthetic Intent" above.

### 2. Goals become steps; constraints become metadata, never steps

A `PlanningGoal` describes something to do (mapping naturally onto
`PlanStep`, which represents one unit of work); a `PlanningConstraint`
describes a limit (which `PlanStep` has no field to represent at all).
Rather than force constraints into a step-shaped hole they do not fit,
they are recorded descriptively in the Plan's own `metadata` instead -
information is preserved, never silently dropped, without distorting
`PlanStep`'s own meaning. See "Goal-to-Step and Constraint-to-Metadata
Mapping" above.

### 3. `PlanningGoal.name` becomes `PlanStep.required_capability`

The only other candidate was leaving `required_capability` unset,
which is not possible - `add_step()`'s own validation requires a
non-empty string. `name` is chosen deterministically, not because it
is semantically identical to "a Capability id," but because it is the
one PlanningGoal field capable of playing that role without inventing
new state. Documented explicitly as a Known Limitation, not quietly
assumed to be correct in every case.

### 4. `InvalidPlanError` is reused; no new exception type

`plan_session()` raising the Planner's own pre-existing
`InvalidPlanError` for a non-`PlanningSession` argument mirrors
`create_plan()`'s own identical treatment of a non-`Intent` argument -
consistent, minimal, and satisfies "Planner shall NOT depend directly
on: ... Exceptions" (meaning `argus.planning.exceptions`, never
raised, caught, or imported here) without needing any new vocabulary.

### 5. `IPlanner` gains `plan_session()` as a new abstract method

Every prior package in this codebase has kept its interface's
abstract method list exactly matching its implementation's public
surface - `plan_session()` is declared on `IPlanner` for the same
reason, rather than being added to `Planner` alone without an
interface declaration.

---

## Events

No new `EventType` members - "No EventBus changes." `plan_session()`
publishes nothing directly; every event it causes to fire
(`PLAN_CREATED` once, `PLAN_UPDATED` once per goal) is published by
the pre-existing `create_plan()`/`add_step()` calls it delegates to,
using the exact same `EventType.PLAN_CREATED`/`EventType.PLAN_UPDATED`
members those methods have published since Package 015.

---

## IService Adoption

Not applicable - `IPlanner` did not inherit `IService` before this
package and still does not; Planner's own lack of any genuine
multi-phase behavior (see `argus/planner/interfaces.py`'s
pre-existing Architectural Note) is entirely unaffected by adding one
more ungated, synchronous, in-memory method.
`design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md` was not
modified by this package.

---

## Repository Verification Note

The uploaded repository ("ArgusOS (23).zip") was verified against
this package's own general "verify repository state, verify version
consistency, verify HEAD/tag ancestry, run smoke validation"
pre-flight instruction. Findings: HEAD (`5e39630`, "Synchronize
repository version with v0.2.3 release") is a clean, single-commit
descendant of tag `v0.2.3` (which points to `ef67b8e`, "Implement
Package 023 Planning Session"); `v0.2.2` also confirmed an ancestor of
HEAD via `git merge-base --is-ancestor`. `git diff v0.2.3..HEAD --stat`
shows exactly the expected one-line version-sync commit
(`argus/bootstrap.py`, 1 insertion, 1 deletion) - no anomaly.
`git status --short` showed a completely clean working tree.
`argus/planning/` (Package 023) present with all expected files;
`python -m pytest` passing (1397 passed, 38 subtests); `python -m
unittest discover -s tests` passing (1309); `python -m unittest
discover -s argus/tests` passing (64); `python main.py` starting and
shutting down cleanly (exit 0); `CORE_SERVICES_VERSION == "0.2.3"`
matching tag `v0.2.3`. All confirmed before any Package 024 code was
written.

---

## Files Created

```
factory/packages/024_PLANNER_SESSION_INTEGRATION.md
tests/test_planner_session_integration.py
```

## Files Modified

```
argus/planner/interfaces.py    (added plan_session() to IPlanner,
                                 plus two new Architectural Notes;
                                 every pre-existing abstract method
                                 unchanged)
argus/planner/planner.py       (added Planner.plan_session() and two
                                 private helpers
                                 (_synthesize_intent_for_session(),
                                 _session_plan_metadata()); every
                                 pre-existing method's body unchanged)
CHANGELOG.md, DEVLOG.md, IMPLEMENTATION_REPORT.md, factory/ROADMAP.md
```

No other file was modified. Per this package's own explicit
Constraints, `argus/bootstrap.py`, `argus/events/event_types.py`,
`tests/test_bootstrap.py`, `argus/tests/test_bootstrap.py`,
`argus/runtime/`, `argus/decision/`, `argus/context/`,
`argus/planning/`, `argus/planner/plan.py`, `argus/planner/step.py`,
`argus/planner/exceptions.py`, `argus/planner/__init__.py`, and
`tests/test_planner.py` were left completely untouched - confirmed via
`git diff --stat` showing zero lines changed in any of them.

---

## Backward Compatibility Verification

```
python -m pytest tests/test_planner.py -q
52 passed in 0.05s
```

All 52 pre-existing Planner tests pass with zero modification to
`tests/test_planner.py` itself - direct evidence that every
pre-existing `IPlanner` method's behavior, signature, and event
publication are unchanged. The full regression suite
(`python -m pytest`) also passes in full afterward - see Test Results
below.

---

## Test Results

New integration suite:
```
python -m pytest tests/test_planner_session_integration.py -q
31 passed in 0.04s
```

Canonical suite (`tests/`):
```
python -m unittest discover -s tests
Ran 1340 tests in 0.110s
OK
```

Per this package's explicit testing instruction:
```
python -m pytest
1428 passed, 38 subtests passed in 0.91s
```

The duplicate `argus/tests/` also verified passing standalone
(unaffected - not touched by this package):
```
python -m unittest discover -s argus/tests -p "test_*.py"
Ran 64 tests in 0.015s
OK
```

`pyflakes` on every new/modified module: clean, no warnings.

`python main.py`:
```
[INFO] argus: ArgusOS application started.
[INFO] argus: ArgusOS application shutting down.
```
Exit code 0.

---

## Coverage

Measured with `coverage.py`, `python -m coverage run --source=argus/planner -m pytest tests/test_planner.py tests/test_planner_session_integration.py`:

```
argus/planner/__init__.py         6      0   100%
argus/planner/exceptions.py       5      0   100%
argus/planner/interfaces.py      22      0   100%
argus/planner/plan.py            25      0   100%
argus/planner/planner.py        102      0   100%
argus/planner/step.py            14      0   100%
TOTAL                            174      0   100%
```

100% coverage across the entire `argus/planner/` package - including
every newly added line - reached on the first measurement, no
post-hoc gap-closing needed. Overall repository coverage: 99%
(unchanged from Package 023; remaining gaps are pre-existing and out
of scope).

---

## Known Limitations

- **`PlanningGoal.name` doubles as `required_capability`** - a
  deterministic, documented choice, not a semantic guarantee that
  every goal's name will actually correspond to a registered
  Capability. `validate_plan()`, called separately, is what surfaces
  whether that's actually true for any given Plan - `plan_session()`
  itself never calls it.
- **`plan_session()` never calls `validate_plan()`** - it produces a
  `PlanStatus.CREATED` Plan, exactly like `create_plan()` alone would;
  validation remains an explicit, separate step for any caller who
  wants it, unchanged from every other Plan in this codebase.
- **Goal `priority` still has no behavior beyond being copied into
  step metadata** - `add_step()` does not reorder based on it, and
  `plan_session()` does not either; steps always appear in the
  session's own `goals` call order, per Package 023's own "descriptive
  only" design for `PlanningGoal.priority`.
- **`PlanningSession.cognitive_context`'s own contents (beyond
  `context_id`) are not otherwise consulted** - `memory_references`/
  `knowledge_references`/`reasoning_results`/`decision_references` are
  not read or reflected anywhere in the resulting Plan; only
  `context_id` is carried through for traceability.
- **The Planner is still not automatically wired into the pipeline** -
  a future package deciding to have the Reasoning Engine/Cognitive
  Context/Planning Session chain call `plan_session()` automatically
  would be a separate, later integration; this package only makes that
  call possible for a caller that already has a `PlanningSession` in
  hand.
- No AI, no optimization, no persistence - unchanged from Package 015.
- No concurrency.
- The repository's stray `argus/` duplicate tree and legacy
  pre-Factory files remain unresolved, out of scope per the Founder's
  explicit repository rules.

---

## Future Planner Evolution

- Wire an automatic pipeline stage (Reasoning Engine -> Cognitive
  Context -> Planning Session -> `Planner.plan_session()`) once a
  future package's work order explicitly asks for that integration -
  "Planner shall not consume Planning Session yet" describes only the
  absence of that automatic wiring, not any limitation of
  `plan_session()` itself.
- Consider whether a future package should let `PlanningGoal` carry an
  explicit, separate capability-id field distinct from `name`, once a
  concrete need to decouple "what the goal is called" from "what
  Capability satisfies it" arises - Version 1 deliberately reuses
  `name` rather than extending `PlanningGoal` (out of this package's
  own Constraints: "modify Planning Session" is explicitly forbidden).
- Consider whether `PlanningConstraint`s should eventually influence
  plan generation itself (for example, filtering which Capabilities
  `validate_plan()` will accept) once `PlanningConstraint` gains
  evaluable logic (see `factory/packages/023_PLANNING_SESSION.md`'s
  own Future Expansion) - Version 1 records constraints purely
  descriptively, with zero effect on validation or step generation.

---

## Release Rules

Per the Founder's explicit instruction: no commit, tag, or push was
performed. `CORE_SERVICES_VERSION` was not changed by this package -
it remains `"0.2.3"`. Bootstrap was not modified in any way. This
package is not reported as complete or released - implementation ends
after successful local verification; final validation, integration,
release, version update, commit, and tag are the Founder's
responsibility against the live repository.
