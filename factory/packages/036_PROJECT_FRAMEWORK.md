# Implementation Package 036 - Project Framework

## Objective

Introduce the Project domain. "A Project is the top-level
organizational unit for long-running work." Examples given: Just
Tallow, Packaging Sales, ArgusOS, Book Publishing, Real Estate,
Marketing, Personal. "Projects own Goals. Goals own Plans. Plans own
Tasks."

---

## Architectural Position

Prior architecture:

```
Goal
    |
    v
Plan
    |
    v
Task
```

New architecture:

```
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

This package introduces `Project` as a standalone value object only -
no `Goal` domain object exists yet anywhere in this codebase (the
closest prior concept, `PlanningGoal` in `argus/planning/`, Package
023, is an unrelated transport field describing a single planning
session's own stated objective, not a standalone owning entity), and
this package does not create one. The diagram above describes the
*eventual* ownership hierarchy this package's own domain is a first
piece of - "This package introduces the Project model only," with no
`goals` field, no relationship to `Goal`, `Plan`, or `Task` of any
kind. See "Future Relationship" below.

---

## New Package

```
argus/project/
    __init__.py     (new)
    project.py       (new)
    metadata.py       (new)
    builder.py          (new)
    status.py             (new)
    interfaces.py          (new)
    exceptions.py            (new)
```

---

## Project

Immutable value object. Fields, per the work order's own literal
order: `project_id`, `name`, `description`, `status`, `metadata` -
already places `metadata` last, needing no normalization. Every field
defaults - `Project()` is always valid, the same "value object with a
dedicated builder" shape `CognitiveContext`/`PlanningSession`/
`ExecutionTrace`/`Task`/`TaskRelationship`/`ExecutionResult`/
`CapabilityExecutionResult`/`CapabilityContext` (022, 023, 028, 029,
031, 032, 034, 035) all use. `project_id` defaults to a fresh uuid4
string; `name`/`description` default to `""`; `status` defaults to
`ProjectStatus.PLANNING`; `metadata` defaults to a fresh
`ProjectMetadata()`. Directly mirrors `Task`'s own shape (029) -
`project_id`/`name`/`description`/`status`/`metadata` is exactly
`Task`'s own `task_id`/`name`/`description`/`status`/`metadata`, minus
the `relationships` field `Task` gained in Package 031, since this
package introduces no ownership relationships yet. "Project is a
passive domain object only" - no behavior, no validation beyond the
standard dataclass field typing.

---

## ProjectStatus

A plain `Enum` (not a `str` subclass), five members: `PLANNING`,
`ACTIVE`, `PAUSED`, `COMPLETED`, `ARCHIVED` - lowercase string values
matching each member's own name, mirroring `TaskStatus`
(029)/`CapabilityExecutionStatus` (034)'s own shape exactly. No
transition logic anywhere - nothing in `argus.project` ever moves a
`Project` from one `ProjectStatus` to another; the default,
`PLANNING`, is simply what every `Project` built without an explicit
`with_status()` call carries. Unlike `TaskStatus`/`CapabilityExecutionStatus`,
no member of `ProjectStatus` is reserved-but-unproduced - every one of
the five is equally reachable via `ProjectBuilder.with_status()`,
since this package defines no distinguished "successful outcome" the
way resolution-producing packages do.

---

## ProjectMetadata

Immutable value object. The work order's own field list for this
module is the first in this codebase's history to be introduced as
"Suggested fields" rather than the imperative "Fields:" every prior
metadata module's work order used - and the list itself, `created_at,
owner, tags, version, extra`, genuinely diverges from every
established metadata module in composition, not merely order: it
omits `correlation_id` (present in every sibling metadata module since
Package 028 without exception) and introduces two fields, `owner` and
`tags`, no metadata module has ever carried. Resolved by treating
"Follow existing metadata conventions" as the dominant instruction (as
in every prior resolution) and "Suggested fields" as genuinely
additive to, not a replacement of, that convention: `correlation_id`
is kept; `owner` and `tags` are added. Final field order:
`created_at`, `version`, `correlation_id` (the established quartet's
own unchanged relative order), then `owner`, `tags` (the new fields,
in the order this package's own suggested list gives them), then
`extra` (last, per every prior convention). `tags` defaults to an
empty tuple and is coerced to a tuple in `__post_init__`, mirroring
`Task.relationships`/`Plan.tasks`'s own "always stored as a tuple"
convention. `owner` defaults to `None`. See "Engineering Decision"
below for why `owner`/`tags` are not settable through
`ProjectBuilder` in Version 1.

---

## ProjectBuilder

The only mutable object in this package. Responsibilities, per the
work order's own literal list: assign name, assign description,
assign status, assign metadata, build immutable Project - four items
plus "assign metadata," mapping onto five implemented methods
(`with_name`, `with_description`, `with_status`, `with_metadata`,
`build`), directly mirroring `TaskBuilder`'s own shape (029) minus the
`relationships` trio. No `with_project_id()` - the work order's own
list does not name "assign id," continuing the precedent already set
by `RelationshipBuilder` (031), `ExecutionResultBuilder` (032),
`CapabilityExecutionResultBuilder` (034), and `CapabilityContextBuilder`
(035). No `with_owner()`/`with_tags()` either - see "Engineering
Decision" below. `with_metadata(key, value)` only ever populates
`ProjectMetadata.extra`, mirroring every prior builder's identical
rule. Malformed input to `with_name()`/`with_description()`/
`with_status()`/`with_metadata()` raises `InvalidProjectError`.

---

## Integration

None. "No runtime behavior yet. No planner changes. No execution
changes. No capability changes. No response changes. No bootstrap
changes. This package introduces the Project model only." Confirmed:
`argus/bootstrap.py` is unmodified, and no file outside
`argus/project/` and its own new test files was touched by this
package - the first package in this codebase's history to modify
*zero* pre-existing files, purely additive.

---

## Dependency Graph

```
Project
    -> ProjectStatus (field type)
    -> ProjectMetadata (field type)

ProjectBuilder
    -> Project (constructs)
    -> ProjectMetadata (constructs)
    -> ProjectStatus (validates against)
    -> InvalidProjectError (raises)

IProjectBuilder
    -> Project (return type)
    -> ProjectStatus (parameter type)
```

No component outside `argus/project/` depends on anything in this
package, and `argus/project/` depends on nothing outside itself and
the standard library - confirmed via `grep -rln "argus.project\|from
argus import project"` across the rest of the repository returning
zero matches. This is a genuinely isolated leaf package.

---

## Ownership Hierarchy

```
Project              (this package - implemented)
    |
    v
Goal                 (does not exist yet - not implemented)
    |
    v
Plan                 (argus.planner.plan - Package 015, pre-existing)
    |
    v
Task                 (argus.task.task - Package 029, pre-existing)
```

`Project` is introduced as a standalone value object with no field
referencing `Goal`, `Plan`, or `Task` - the ownership arrows above
describe the domain's own eventual conceptual shape, not any code
relationship this package creates. `Plan` and `Task` already exist and
are untouched by this package; `Goal` does not exist in any form in
this codebase and this package does not create it.

---

## Future Relationship

Per this package's own explicit "Future Relationship" section:
"Projects will eventually own: Goals, Documents, Knowledge,
Conversations, Assets, Campaigns. Do not implement those relationships
yet. Simply document them." None of these six relationships are
implemented by this package - `Project` holds no `goals` field, no
`documents` field, and so on. A future package would most likely add
each such relationship the same way `Task` gained `relationships` in
Package 031: a new, defaulted, ordered collection field declared
after `status` and before `metadata` (continuing the "insert the new
collection field before metadata, so metadata stays the
last-declared field" precedent established at Package 030 and
repeated at 031), with a corresponding
`with_<relationship>()`/`with_<relationship>s()`/`clear_<relationship>s()`
trio added to `ProjectBuilder`, mirroring `TaskBuilder`'s own
`with_relationship()`/`with_relationships()`/`clear_relationships()`
shape. This is a documented expectation about a future package's own
likely shape, not a commitment this package makes.

---

## Engineering Decision

**Why "Suggested fields" resolves differently than every prior
"follow existing metadata conventions" tension.** Every prior metadata
module's own work order (029 through 035) used the imperative
"Fields:" header and named exactly the established quartet
(`created_at`, `correlation_id`, `version`, `extra`) in some order -
the only tension to resolve was ever about *order*, and "follow
existing conventions" always settled it in favor of the codebase's own
established relative ordering over the work order's own literal
listed order. This package's own work order instead uses "Suggested
fields," a softer, advisory header no prior metadata module's own work
order used, and lists a field *set* that genuinely differs in
composition: `correlation_id` is absent, and `owner`/`tags` are
present. Read "Suggested fields" as inviting judgment about
composition (not merely order) while "Follow existing metadata
conventions" remains the dominant instruction, as in every prior
resolution: `correlation_id` is kept, since dropping it would be a
genuine, unrequested convention break; `owner` and `tags` are added,
since they are explicitly and specifically suggested for this
particular domain object - the first metadata module ever suggested
with its own domain-specific fields at all.

**Why `owner`/`tags` are not settable through `ProjectBuilder` in
Version 1.** `ProjectBuilder`'s own Responsibilities list names
exactly "assign name, assign description, assign status, assign
metadata" - one bullet for "assign metadata," the same shape every
prior builder's `with_metadata()` already resolves as "populate
`extra` only," never as license to expose a setter for every field the
metadata object happens to hold. Extending that established
"`created_at`/`version`/`correlation_id` are system-managed, not
builder-overridable" rule to also cover `owner`/`tags` keeps this
package consistent with `TaskBuilder`'s own precedent rather than
introducing a new, unprecedented builder shape (two additional
dedicated setters neither named in this package's own Responsibilities
list) to accommodate two fields that happen to be new. A caller
wanting a specific `owner`/`tags` value in Version 1 can populate it
through `with_metadata()`'s own `extra` mapping, or construct
`ProjectMetadata` directly, bypassing the builder - both already-legal
paths, requiring no new method.

**Why no `Goal` object is introduced, even minimally.** The work
order's own Constraints section is explicit: "Do NOT... redesign Goal"
- read together with "Introduce the Project domain" (not "the Project
and Goal domains") and "This package introduces the Project model
only," creating even a placeholder `Goal` would exceed this package's
own stated scope. `Project` is therefore genuinely standalone in
Version 1, with its eventual relationship to `Goal` documented, not
built.

---

## Repository Verification Note

Before writing any code, the uploaded repository ("ArgusOS (35).zip")
was verified fresh against this package's own general pre-flight
instruction. No anomaly was found - the twenty-second consecutive
clean pre-flight (015-036). HEAD (`71f227b`, "Synchronize repository
version with v0.3.5 release") is a clean, single-commit descendant of
tag `v0.3.5` (which points to `4b99564`, "Implement Package 035
Capability Context"), confirmed via `git merge-base --is-ancestor
v0.3.5 HEAD`. `git diff v0.3.5..HEAD --stat` shows exactly the
expected one-line version-sync commit - `CORE_SERVICES_VERSION` moved
from `"0.3.4"` to `"0.3.5"`, a patch increment, the Founder's own
release choice following Package 035's own integration. `python -m
pytest` passing (2297 passed, 38 subtests); `python -m unittest
discover -s tests` passing (2209); `python -m unittest discover -s
argus/tests` passing (64); `python main.py` starting and shutting down
cleanly (exit 0); `CORE_SERVICES_VERSION == "0.3.5"` matching tag
`v0.3.5`. `argus/project/` confirmed absent from the repository prior
to this package. No anomaly of any kind was found during pre-flight
for this package.

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
    project/
        __init__.py                              (new)
        project.py                               (new)
        metadata.py                               (new)
        builder.py                                (new)
        status.py                                 (new)
        interfaces.py                             (new)
        exceptions.py                             (new)
factory/
    packages/
        036_PROJECT_FRAMEWORK.md                 (new)
tests/
    test_project.py                              (new)
    test_project_builder.py                      (new)
    test_project_metadata.py                     (new)
    test_project_status.py                       (new)
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
modified - `argus/bootstrap.py` is unmodified, and no pre-existing
source file anywhere in the repository was touched. This is the first
package in this codebase's history whose own "Files Modified" list
contains no source or test file at all - purely additive to
`argus/project/` and this package's own documentation.

---

## Test Results

New project suites:
```
python -m pytest tests/test_project.py tests/test_project_builder.py tests/test_project_metadata.py tests/test_project_status.py -q
72 passed in 0.06s
```

Canonical suite (`tests/`):
```
python -m unittest discover -s tests
Ran 2281 tests in 0.171s
OK
```

Per this package's own explicit testing instruction:
```
python -m pytest
2369 passed, 38 subtests passed in 1.54s
```

The duplicate `argus/tests/` also verified passing (unmodified by
this package):
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

New test coverage, per this package's own explicit Testing section -
immutability, builder behavior, enum behavior, metadata defaults,
equality, serialization consistency:

- `tests/test_project_status.py` (new, 8 tests): members, values,
  plain-Enum shape, no-extra-methods, round trips, equality/identity.
- `tests/test_project_metadata.py` (new, 21 tests): defaults, field
  set/order (the new `owner`/`tags` composition), `owner` acceptance,
  `tags` tuple-wrapping/defensive-copy, `extra` wrapping/defensive-copy/
  immutability, dataclass immutability, equality.
- `tests/test_project.py` (new, 18 tests): defaults, field set/order
  (`metadata` last), every example name from the work order, object
  immutability, deepcopy/pickle/JSON-suitability, equality.
- `tests/test_project_builder.py` (new, 25 tests): identity/not-an-
  IService/no `with_project_id()`/no `with_owner()`/no `with_tags()`,
  every `with_*()` method's chaining/overwrite/validation behavior,
  confirmation that `with_metadata("owner", ...)` populates `extra`
  only (never the dedicated `owner` field), `build()`
  independence/full chain.

---

## Coverage

Measured with `coverage.py`,
`python -m coverage run --source=argus.project -m pytest`:

| Module | Stmts | Miss | Cover |
|---|---|---|---|
| `argus/project/__init__.py` | 7 | 0 | 100% |
| `argus/project/builder.py` | 35 | 0 | 100% |
| `argus/project/exceptions.py` | 2 | 0 | 100% |
| `argus/project/interfaces.py` | 15 | 0 | 100% |
| `argus/project/metadata.py` | 17 | 0 | 100% |
| `argus/project/project.py` | 11 | 0 | 100% |
| `argus/project/status.py` | 7 | 0 | 100% |

100% coverage across the entire new `argus/project/` package (94
statements) - reached on the first measurement, no post-hoc
gap-closing needed. No other module was modified by this package, so
no other module's coverage is reported here.

---

## Known Limitations

- **No ownership relationships exist yet** - `Project` holds no
  reference to `Goal`, `Document`, `Knowledge`, `Conversation`,
  `Asset`, or `Campaign`. "Do not implement those relationships yet.
  Simply document them."
- **`Goal` does not exist as a domain object anywhere in this
  codebase** - the ownership chain `Project -> Goal -> Plan -> Task`
  is one implemented link (`Project`) followed by one missing link
  (`Goal`) followed by two pre-existing, already-implemented links
  (`Plan`, `Task`).
- **`owner`/`tags` are not settable through `ProjectBuilder`** - a
  deliberate consequence of this codebase's own "system-managed
  metadata fields are not builder-overridable" convention, extended
  here to two genuinely new fields; see "Engineering Decision" above.
- **No transition logic on `ProjectStatus`** - nothing advances a
  `Project` from `PLANNING` to `ACTIVE`, or between any other pair of
  states; every state is reachable only via an explicit
  `ProjectBuilder.with_status()` call.
- **No persistence, no concurrency, no scheduling, no runtime
  behavior of any kind** - "Project is a passive domain object only."
- **No integration with any existing package** - `Planner`, `Response`,
  `Runtime`, `ExecutionEngine`, `CapabilityExecutor`,
  `CapabilityContext`, and `bootstrap.py` are all completely untouched.

---

## Release Rules

Per the Founder's standing release process, this package was
implemented and verified entirely within the supplied repository. No
`git commit`, `git tag`, push, or git-history modification of any
kind was performed. `CORE_SERVICES_VERSION` was not changed and
remains `"0.3.5"`. This package is not being reported as complete -
final validation, integration, version bump, commit, tag, and release
remain the Founder's responsibility, to be performed against the live
repository after independent regression testing.
