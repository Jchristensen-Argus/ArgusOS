# Implementation Package 038 - Goal Framework

## Objective

Introduce the Goal domain. "A Goal represents a desired outcome
within a Project. Projects own Goals. Goals own Plans. Plans own
Tasks. Goals are passive domain objects only."

---

## Architectural Position

Prior architecture:

```
Workspace
    |
    v
Project
    |
    v
Plan
    |
    v
Task
```

New architecture:

```
Workspace
    |
    v
Project
    |
    v
Goal
    |
    v
Plan
    |
    v
Task
```

This package fills the one gap Packages 036 and 037 each left open:
where those two packages extended the organizational hierarchy from
its own topmost end (`Project` above `Plan`/`Task`, then `Workspace`
above `Project`), this package completes the hierarchy from the
middle - `Goal` now sits between the already-implemented `Project`
(036) and the already-implemented `Plan`/`Task` (015/029), closing the
`Workspace -> Project -> Goal -> Plan -> Task` chain end to end for
the first time. `Goal` is introduced as a standalone value object
only - no field on `Goal` references `Project`, `Plan`, or `Task` in
any way; no field on `Project` references `Goal` either. See "Future
Relationship" below.

---

## New Package

```
argus/goal/
    __init__.py     (new)
    goal.py           (new)
    metadata.py         (new)
    builder.py            (new)
    status.py               (new)
    priority.py                (new)
    interfaces.py                 (new)
    exceptions.py                    (new)
```

Eight files, one more than `argus/project/` (036) or `argus/workspace/`
(037) - `priority.py` is a genuine addition, not present on either
sibling package, since neither `Project` nor `Workspace` has a
priority field.

---

## Goal

Immutable value object. Fields, per the work order's own literal
order: `goal_id`, `name`, `description`, `status`, `priority`,
`metadata` - already places `metadata` last, needing no
normalization. Every field defaults - `Goal()` is always valid, the
same "value object with a dedicated builder" shape
`CognitiveContext`/`PlanningSession`/`ExecutionTrace`/`Task`/
`TaskRelationship`/`ExecutionResult`/`CapabilityExecutionResult`/
`CapabilityContext`/`Project`/`Workspace` (022, 023, 028, 029, 031,
032, 034, 035, 036, 037) all use. `goal_id` defaults to a fresh uuid4
string; `name`/`description` default to `""`; `status` defaults to
`GoalStatus.PLANNING`; `priority` defaults to `GoalPriority.NORMAL`;
`metadata` defaults to a fresh `GoalMetadata()`. Unlike `Project`/
`Workspace` (five fields each), `Goal` holds a sixth field, `priority`,
declared between `status` and `metadata`. "Goals are passive domain
objects only" - no behavior, no validation beyond the standard
dataclass field typing.

---

## GoalStatus

A plain `Enum` (not a `str` subclass), five members: `PLANNING`,
`ACTIVE`, `PAUSED`, `COMPLETED`, `ABANDONED` - lowercase string values
matching each member's own name, mirroring `ProjectStatus`
(036)/`WorkspaceStatus` (037)'s own shape exactly. "No transition
logic" - nothing in `argus.goal` ever moves a `Goal` from one
`GoalStatus` to another. The default is `GoalStatus.PLANNING` -
matching `ProjectStatus.PLANNING`'s own "not yet begun" meaning, not
`WorkspaceStatus.ACTIVE`'s own default, since `GoalStatus`'s own
member list is shaped like `ProjectStatus`'s (both open with
`PLANNING`), not `WorkspaceStatus`'s. The final member, `ABANDONED`,
is a deliberate departure from `ProjectStatus.ARCHIVED` - a Goal given
up on carries a different connotation than a Project retained for
historical reference, and this module preserves that distinction
literally rather than reusing `ARCHIVED` for cross-package
consistency's own sake.

---

## GoalPriority

A plain `Enum` (not a `str` subclass, and critically not an `IntEnum`
or any other ordered variant), four members: `LOW`, `NORMAL`, `HIGH`,
`CRITICAL`. "No ordering behavior" - members support no `<`/`>`
comparison and no numeric weighting, despite the member names'
own intuitively ordered reading. The default is `GoalPriority.NORMAL`,
not `LOW` - the first genuine exception in this codebase's history to
the "first-listed member is the default" convention, since defaulting
an unprioritized Goal's own priority to `LOW` would misrepresent the
absence of an explicit priority as evidence of low importance. See
"Engineering Decision" below.

---

## GoalMetadata

Immutable value object. The work order's own field list for this
module reads, literally, `created_at, owner, correlation_id, version,
tags, extra` - the identical literal order Package 037's own work
order used, resolved there in favor of `ProjectMetadata`'s own
established order instead. This package's own explicit governing
instruction, "Follow the existing metadata conventions established by
Project and Workspace," names that precedent directly, by name, for
the first time in this codebase's history. `GoalMetadata` follows
`ProjectMetadata`'s (036) and `WorkspaceMetadata`'s (037) own
identical order exactly: `created_at`, `version`, `correlation_id`,
`owner`, `tags`, `extra`. `tags` defaults to an empty tuple and is
coerced to a tuple in `__post_init__`, mirroring the two sibling
metadata modules' own identical convention. `owner` defaults to
`None`. See "Engineering Decision" below for why `owner`/`tags` are
not settable through `GoalBuilder` in Version 1 - the identical
reasoning already applied to `ProjectMetadata` and `WorkspaceMetadata`.

---

## GoalBuilder

The only mutable object in this package. Responsibilities, per the
work order's own literal list: assign name, assign description,
assign status, assign priority, assign metadata, build immutable Goal
- five items plus build, mapping onto six implemented methods
(`with_name`, `with_description`, `with_status`, `with_priority`,
`with_metadata`, `build`). Unlike `owner`/`tags`, `priority` **is**
explicitly named in this package's own Responsibilities list - "assign
priority" is its own bullet, the same way "assign status" is its own
bullet - so `with_priority()` is implemented as a full, validated,
singular-field setter, not folded into `with_metadata()`'s own
extra-only behavior. No `with_goal_id()` - the work order's own list
does not name "assign id," continuing the precedent already set by
`RelationshipBuilder` (031), `ExecutionResultBuilder` (032),
`CapabilityExecutionResultBuilder` (034), `CapabilityContextBuilder`
(035), `ProjectBuilder` (036), and `WorkspaceBuilder` (037). No
`with_owner()`/`with_tags()` either - see "Engineering Decision"
below. Malformed input to any `with_*()` method raises
`InvalidGoalError`.

---

## Integration

None. "No runtime behavior. No Planner changes. No Execution changes.
No Capability changes. No Bootstrap changes. No Project changes. No
Workspace changes. No Response changes. Introduce the Goal model
only." Confirmed: `argus/bootstrap.py` is unmodified, `argus/project/`
and `argus/workspace/` are both unmodified, and no file outside
`argus/goal/` and its own new test files was touched by this package -
the third consecutive package (after 036, 037) to modify zero
pre-existing files, purely additive.

---

## Dependency Graph

```
Goal
    -> GoalStatus (field type)
    -> GoalPriority (field type)
    -> GoalMetadata (field type)

GoalBuilder
    -> Goal (constructs)
    -> GoalMetadata (constructs)
    -> GoalStatus (validates against)
    -> GoalPriority (validates against)
    -> InvalidGoalError (raises)

IGoalBuilder
    -> Goal (return type)
    -> GoalStatus (parameter type)
    -> GoalPriority (parameter type)
```

No component outside `argus/goal/` depends on anything in this
package, and `argus/goal/` depends on nothing outside itself and the
standard library - confirmed via `grep -rln "argus.goal\|from argus
import goal"` across the rest of the repository returning zero
matches. This is a genuinely isolated leaf package, structurally
close to `argus/project/` (036) and `argus/workspace/` (037), with one
additional field/module (`priority`/`priority.py`) neither sibling
package has.

---

## Ownership Hierarchy

```
Workspace             (argus.workspace.workspace - Package 037, pre-existing)
    |
    v
Project                (argus.project.project - Package 036, pre-existing)
    |
    v
Goal                     (this package - implemented)
    |
    v
Plan                       (argus.planner.plan - Package 015, pre-existing)
    |
    v
Task                          (argus.task.task - Package 029, pre-existing)
```

For the first time, every link in this five-level chain now
corresponds to an implemented, standalone domain object - `Workspace`,
`Project`, `Goal`, `Plan`, and `Task` all exist as code, even though
none of the ownership *relationships* between them (the arrows above)
are implemented anywhere. `Project`, `Plan`, and `Task` are all
completely untouched by this package.

---

## Future Relationship

Per this package's own explicit "Future Relationship" section: "A
Goal will eventually own: Plans, Success metrics, Milestones,
Decisions, Deadlines, Risks, Dependencies. Do NOT implement these
relationships. Document them only." None of these seven relationships
are implemented by this package - `Goal` holds no `plans` field, no
`milestones` field, and so on. A future package would most likely add
each such relationship the same way `Task` gained `relationships` in
Package 031: a new, defaulted, ordered collection field declared
after `priority` and before `metadata`, with a corresponding
`with_<relationship>()`/`with_<relationship>s()`/`clear_<relationship>s()`
trio added to `GoalBuilder`, mirroring `TaskBuilder`'s own shape. This
is a documented expectation about a future package's own likely
shape, not a commitment this package makes.

Notably, "Plans" appears in this list - meaning a future package
connecting `Goal` to the already-implemented `Plan` (015) would follow
this exact same pattern, finally wiring the one link in the
`Workspace -> Project -> Goal -> Plan -> Task` chain this package's
own Architectural Position diagram draws but does not build.

---

## Real-World Examples

Illustrative only - no code in this package constructs any of these;
they exist to show how a Goal's own "desired outcome within a
Project" role might look concretely, continuing the example format
Packages 036/037 established for `Project`/`Workspace`:

- Within a **"Just Tallow"** (036) Project: a Goal named "Launch the
  winter scent line by Q4," `priority=HIGH`, `status=ACTIVE`.
- Within a **"Deline Box & Display"** (037) Workspace's own sales
  Project: a Goal named "Close 20 new wholesale accounts this
  quarter," `priority=CRITICAL`.
- Within an **"ArgusOS"** Project: a Goal named "Complete the
  organizational hierarchy through Package 040," `priority=NORMAL`,
  `status=PLANNING` - the kind of Goal this very package's own
  existence might eventually be tracked under, once `Project`/`Goal`
  ownership is implemented.
- A **"Sandbox"** (037) Workspace's own experimental Project might
  hold a Goal with `priority=LOW`, `status=PAUSED` - deliberately
  low-stakes, easily set aside.

---

## Engineering Decision

**Why `GoalMetadata`'s own field order follows `ProjectMetadata`'s/
`WorkspaceMetadata`'s precedent, with no genuine tension to resolve
this time.** This package's own governing instruction - "Follow the
existing metadata conventions established by Project and Workspace" -
names the precedent to follow by name, for the first time in this
codebase's history (every prior "follow existing conventions"
instruction referred to the convention only in the abstract). There is
therefore no interpretive judgment required here at all, unlike
Packages 036's and 037's own resolutions: `GoalMetadata` simply
follows `ProjectMetadata`'s/`WorkspaceMetadata`'s own identical order
- `created_at`, `version`, `correlation_id`, `owner`, `tags`, `extra`
- as directly instructed.

**Why `owner`/`tags` are not settable through `GoalBuilder`.**
Identical reasoning to `ProjectMetadata`'s (036) and `WorkspaceMetadata`'s
(037) own precedent: `GoalBuilder`'s own Responsibilities list names
exactly "assign name, assign description, assign status, assign
priority, assign metadata" - one bullet for metadata, not separate
bullets for `owner`/`tags`. Keeping all three sibling builders
(`ProjectBuilder`, `WorkspaceBuilder`, `GoalBuilder`) symmetric on this
point avoids introducing an unprincipled inconsistency between three
otherwise near-identical packages.

**Why `with_priority()` *is* implemented, unlike `with_owner()`/
`with_tags()`.** The distinguishing factor is not "is this field new"
- `priority`, like `owner`/`tags`, is a field no prior organizational-
tier package had - but *where* the field lives. `owner`/`tags` are
sub-fields of `GoalMetadata`, governed by the single "assign metadata"
bullet every sibling builder already reads as "populate `extra`
only." `priority` is a top-level field on `Goal` itself, and this
package's own Responsibilities list names "assign priority" as its
own explicit bullet, structurally identical to "assign status." The
same literal-listing discipline that keeps `owner`/`tags` out of the
builder's method surface is what puts `with_priority()` into it.

**Why `GoalPriority.NORMAL`, not `GoalPriority.LOW`, is the default.**
Every enum-typed field in this codebase so far has defaulted to its
own first-listed member (`TaskStatus.PENDING`, `PlanStatus.CREATED`,
`ProjectStatus.PLANNING`, `WorkspaceStatus.ACTIVE`, `GoalStatus.PLANNING`)
- but that pattern is a consequence of what each work order's own
member list happened to name first, not a rule imposed independent of
member meaning. Defaulting `Goal.priority` to `LOW` would carry a
false signal - "this Goal is known to be low-priority" - when the
truth is simply "no priority was ever specified." `NORMAL`, the
second-listed member, is the honest default for that case, and is
implemented as such even though it breaks from the "first-listed
member" pattern observed everywhere else in this codebase. This is a
deliberate exception, not an oversight - documented explicitly in
priority.py's own module docstring.

**Why `GoalStatus`'s own final member is `ABANDONED`, not
`ARCHIVED`.** The work order's own literal member list names
`ABANDONED`, not `ARCHIVED` - implemented literally, since the two
words carry genuinely different connotations for a Goal (given up on)
versus a Project (formally closed out, its work presumably finished).

**Why no relationship to `Project` (or `Plan`) is implemented, even
minimally.** The work order's own Constraints are explicit: "Do
NOT... redesign Project... redesign Plan." `Goal` ships standalone,
with its relationships to both documented in prose only.

---

## Repository Verification Note

Before writing any code, the uploaded repository ("ArgusOS (37).zip")
was verified fresh against this package's own general pre-flight
instruction. No anomaly was found - the twenty-fourth consecutive
clean pre-flight (015-038). HEAD (`7666b8d`, "Synchronize repository
version with v0.3.7 release") is a clean, single-commit descendant of
tag `v0.3.7` (which points to `c44f3ef`, "Implement Package 037
Workspace Framework"), confirmed via `git merge-base --is-ancestor
v0.3.7 HEAD`. `git diff v0.3.7..HEAD --stat` shows exactly the
expected one-line version-sync commit - `CORE_SERVICES_VERSION` moved
from `"0.3.6"` to `"0.3.7"`, a patch increment, the Founder's own
release choice following Package 037's own integration. `python -m
pytest` passing (2442 passed, 38 subtests); `python -m unittest
discover -s tests` passing (2354); `python -m unittest discover -s
argus/tests` passing (64); `python main.py` starting and shutting down
cleanly (exit 0); `CORE_SERVICES_VERSION == "0.3.7"` matching tag
`v0.3.7`. `argus/goal/` confirmed absent from the repository prior to
this package, and no `Goal` naming collision anywhere. No anomaly of
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
    goal/
        __init__.py                              (new)
        goal.py                                  (new)
        metadata.py                               (new)
        builder.py                                (new)
        status.py                                 (new)
        priority.py                               (new)
        interfaces.py                             (new)
        exceptions.py                             (new)
factory/
    packages/
        038_GOAL_FRAMEWORK.md                    (new)
tests/
    test_goal.py                                 (new)
    test_goal_builder.py                         (new)
    test_goal_metadata.py                        (new)
    test_goal_status.py                          (new)
    test_goal_priority.py                        (new)
```

---

## Files Modified

```
CHANGELOG.md                                     (modified)
DEVLOG.md                                        (modified)
factory/ROADMAP.md                               (modified)
IMPLEMENTATION_REPORT.md                         (replaced)
```

No file outside these two lists was created, deleted, moved, or
modified - `argus/bootstrap.py`, `argus/project/`, and
`argus/workspace/` are all unmodified, and no pre-existing source
file anywhere in the repository was touched. This is the third
consecutive package (after 036, 037) whose own "Files Modified" list
contains no source or test file at all - purely additive to
`argus/goal/` and this package's own documentation.

---

## Test Results

New goal suites:
```
python -m pytest tests/test_goal.py tests/test_goal_builder.py tests/test_goal_metadata.py tests/test_goal_status.py tests/test_goal_priority.py -q
92 passed in 0.08s
```

Canonical suite (`tests/`):
```
python -m unittest discover -s tests
Ran 2446 tests in 0.170s
OK
```

Per this package's own explicit testing instruction:
```
python -m pytest
2534 passed, 38 subtests passed in 1.68s
```

The duplicate `argus/tests/` also verified passing (unmodified by
this package):
```
python -m unittest discover -s argus/tests
Ran 64 tests in 0.014s
OK
```

`python main.py`:
```
[INFO] argus: ArgusOS application started.
[INFO] argus: ArgusOS application shutting down.
```
Exit code 0.

New test coverage, per this package's own explicit Testing section -
immutability, builder behavior, enum behavior, metadata defaults,
equality, serialization consistency:

- `tests/test_goal_status.py` (new, 8 tests): members, values,
  plain-Enum shape, no-extra-methods, round trips, equality/identity.
- `tests/test_goal_priority.py` (new, 11 tests): members, values,
  plain-Enum shape, explicit non-`IntEnum` confirmation, `<`/`>`
  comparison rejection, no-extra-methods, round trips,
  equality/identity.
- `tests/test_goal_metadata.py` (new, 22 tests): defaults, field
  set/order (matching `ProjectMetadata`'s/`WorkspaceMetadata`'s own
  precedent), `owner` acceptance, `tags` tuple-wrapping/defensive-copy,
  `extra` wrapping/defensive-copy/immutability, dataclass immutability,
  equality.
- `tests/test_goal.py` (new, 20 tests): defaults, field set/order
  (`metadata` last), default status/priority confirmation, object
  immutability (including the new `priority` field), deepcopy/pickle/
  JSON-suitability, equality.
- `tests/test_goal_builder.py` (new, 31 tests): identity/not-an-
  IService/no `with_goal_id()`/no `with_owner()`/no `with_tags()`/has
  `with_priority()`, every `with_*()` method's chaining/overwrite/
  validation behavior, confirmation that `with_metadata("owner", ...)`
  populates `extra` only, `build()` independence/full chain.

---

## Coverage

Measured with `coverage.py`,
`python -m coverage run --source=argus.goal -m pytest`:

| Module | Stmts | Miss | Cover |
|---|---|---|---|
| `argus/goal/__init__.py` | 8 | 0 | 100% |
| `argus/goal/builder.py` | 42 | 0 | 100% |
| `argus/goal/exceptions.py` | 2 | 0 | 100% |
| `argus/goal/goal.py` | 13 | 0 | 100% |
| `argus/goal/interfaces.py` | 18 | 0 | 100% |
| `argus/goal/metadata.py` | 17 | 0 | 100% |
| `argus/goal/priority.py` | 6 | 0 | 100% |
| `argus/goal/status.py` | 7 | 0 | 100% |

100% coverage across the entire new `argus/goal/` package (113
statements) - reached on the first measurement, no post-hoc
gap-closing needed. No other module was modified by this package.

---

## Known Limitations

- **No ownership relationships exist yet** - `Goal` holds no
  reference to `Plan`, `Success metric`, `Milestone`, `Decision`,
  `Deadline`, `Risk`, or `Dependency`. "Do NOT implement these
  relationships. Document them only."
- **`Goal` is not referenced by `Project`** - `Project.metadata`
  (036) holds no `goals` field of its own; the ownership arrow from
  `Project` to `Goal` in the Architectural Position diagram is not
  implemented in either direction.
- **`owner`/`tags` are not settable through `GoalBuilder`** - a
  deliberate consequence of this codebase's own "system-managed
  metadata fields are not builder-overridable" convention, matching
  `ProjectMetadata`'s/`WorkspaceMetadata`'s own identical treatment.
- **No transition logic on `GoalStatus`, no ordering behavior on
  `GoalPriority`** - nothing advances a Goal's status automatically,
  and no priority level can be compared against another.
- **No persistence, no concurrency, no scheduling, no runtime
  behavior of any kind** - "Goals are passive domain objects only."
- **No integration with any existing package** - `Project`,
  `Workspace`, `Planner`, `Response`, `Runtime`, `ExecutionEngine`,
  `CapabilityExecutor`, `CapabilityContext`, and `bootstrap.py` are
  all completely untouched.

---

## Release Rules

Per the Founder's standing release process, this package was
implemented and verified entirely within the supplied repository. No
`git commit`, `git tag`, push, or git-history modification of any
kind was performed. `CORE_SERVICES_VERSION` was not changed and
remains `"0.3.7"`. This package is not being reported as complete -
final validation, integration, version bump, commit, tag, and release
remain the Founder's responsibility, to be performed against the live
repository after independent regression testing.
