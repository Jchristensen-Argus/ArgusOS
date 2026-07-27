# Implementation Package 037 - Workspace Framework

## Objective

Introduce the Workspace domain. "A Workspace represents the
highest-level organizational boundary within Argus." Examples given:
Joel Christensen, Deline Box & Display, Just Tallow, Family, Sandbox.
"A Workspace owns Projects. Projects own Goals. Goals own Plans. Plans
own Tasks."

---

## Architectural Position

Prior architecture:

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

This package introduces `Workspace` as a standalone value object only
- no field on `Workspace` references `Project`, `Goal`, `Plan`, or
`Task` in any way. The diagram above describes the *eventual*
ownership hierarchy this package's own domain is the newest, topmost
piece of - "This package introduces the Workspace model only," with
no `projects` field or relationship of any kind. See "Future
Relationship" below. Taken together with Package 036's own
`Project -> Goal -> Plan -> Task` chain, the organizational hierarchy
above the execution pipeline now reads
`Workspace -> Project -> Goal -> Plan -> Task`, with `Goal` remaining
the one link in that chain not yet implemented as a standalone domain
object.

---

## New Package

```
argus/workspace/
    __init__.py     (new)
    workspace.py     (new)
    metadata.py       (new)
    builder.py          (new)
    status.py             (new)
    interfaces.py          (new)
    exceptions.py            (new)
```

---

## Workspace

Immutable value object. Fields, per the work order's own literal
order: `workspace_id`, `name`, `description`, `status`, `metadata` -
already places `metadata` last, needing no normalization. Every field
defaults - `Workspace()` is always valid, the same "value object with
a dedicated builder" shape `CognitiveContext`/`PlanningSession`/
`ExecutionTrace`/`Task`/`TaskRelationship`/`ExecutionResult`/
`CapabilityExecutionResult`/`CapabilityContext`/`Project` (022, 023,
028, 029, 031, 032, 034, 035, 036) all use. `workspace_id` defaults to
a fresh uuid4 string; `name`/`description` default to `""`; `status`
defaults to `WorkspaceStatus.ACTIVE`; `metadata` defaults to a fresh
`WorkspaceMetadata()`. Directly mirrors `Project`'s own shape (036) -
`workspace_id`/`name`/`description`/`status`/`metadata` is exactly
`Project`'s own `project_id`/`name`/`description`/`status`/`metadata`,
one level up the ownership hierarchy. "Workspace is a passive domain
object only" - no behavior, no validation beyond the standard
dataclass field typing.

---

## WorkspaceStatus

A plain `Enum` (not a `str` subclass), three members: `ACTIVE`,
`INACTIVE`, `ARCHIVED` - lowercase string values matching each
member's own name, mirroring `ProjectStatus` (036)/`TaskStatus`
(029)'s own shape exactly. "No transition logic" - nothing in
`argus.workspace` ever moves a `Workspace` from one `WorkspaceStatus`
to another. The default is `WorkspaceStatus.ACTIVE` - the first-listed
member, continuing this codebase's own "the first-listed member is
the default" convention (`TaskStatus.PENDING`, `PlanStatus.CREATED`,
`ProjectStatus.PLANNING`), but notably *not* the same relative
"not-yet-begun" meaning `ProjectStatus.PLANNING` carries: a Workspace,
once it exists at all, is presumed active by default, unlike a
Project, which is presumed still in planning. See status.py's own
module docstring for the fuller reasoning.

---

## WorkspaceMetadata

Immutable value object. The work order's own field list for this
module reads, literally, `created_at, owner, correlation_id, version,
tags, extra` - and is the first metadata module work order since
Package 036 to include `owner`/`tags` alongside the established
quartet, this time under the ordinary imperative "Fields:" header (not
Package 036's own "Suggested fields"). Its own explicit governing
instruction, "Follow the metadata conventions established throughout
ArgusOS," is read the same way every prior "follow existing metadata
conventions" instruction has been read since Package 028 - as
dominant over the work order's own literal listed order - but this
time with a direct, exact precedent to follow rather than merely the
older four-field quartet: `ProjectMetadata` (036) already resolved
this identical six-field composition (`created_at`, `version`,
`correlation_id`, `owner`, `tags`, `extra`), in that exact order.
`WorkspaceMetadata` follows `ProjectMetadata`'s own order precisely -
`created_at`, `version`, `correlation_id`, `owner`, `tags`, `extra` -
not this package's own literal listed order. `tags` defaults to an
empty tuple and is coerced to a tuple in `__post_init__`, mirroring
`ProjectMetadata.tags` (036)'s own identical convention. `owner`
defaults to `None`. See "Engineering Decision" below for why
`owner`/`tags` are not settable through `WorkspaceBuilder` in Version
1 - the identical reasoning already applied to `ProjectMetadata`.

---

## WorkspaceBuilder

The only mutable object in this package. Responsibilities, per the
work order's own literal list: assign name, assign description,
assign status, assign metadata, build immutable Workspace - four items
plus "assign metadata," mapping onto five implemented methods
(`with_name`, `with_description`, `with_status`, `with_metadata`,
`build`), directly mirroring `ProjectBuilder`'s own shape (036) one
level up the ownership hierarchy. No `with_workspace_id()` - the work
order's own list does not name "assign id," continuing the precedent
already set by `RelationshipBuilder` (031), `ExecutionResultBuilder`
(032), `CapabilityExecutionResultBuilder` (034),
`CapabilityContextBuilder` (035), and `ProjectBuilder` (036). No
`with_owner()`/`with_tags()` either - see "Engineering Decision"
below. `with_metadata(key, value)` only ever populates
`WorkspaceMetadata.extra`, mirroring every prior builder's identical
rule. Malformed input to `with_name()`/`with_description()`/
`with_status()`/`with_metadata()` raises `InvalidWorkspaceError`.

---

## Integration

None. "No runtime behavior. No Planner changes. No Execution changes.
No Capability changes. No Bootstrap changes. No Response changes. This
package introduces the Workspace model only." Confirmed:
`argus/bootstrap.py` is unmodified, and no file outside
`argus/workspace/` and its own new test files was touched by this
package - the second consecutive package (after 036) to modify zero
pre-existing files, purely additive.

---

## Dependency Graph

```
Workspace
    -> WorkspaceStatus (field type)
    -> WorkspaceMetadata (field type)

WorkspaceBuilder
    -> Workspace (constructs)
    -> WorkspaceMetadata (constructs)
    -> WorkspaceStatus (validates against)
    -> InvalidWorkspaceError (raises)

IWorkspaceBuilder
    -> Workspace (return type)
    -> WorkspaceStatus (parameter type)
```

No component outside `argus/workspace/` depends on anything in this
package, and `argus/workspace/` depends on nothing outside itself and
the standard library - confirmed via `grep -rln "argus.workspace\|from
argus import workspace"` across the rest of the repository returning
zero matches. This is a genuinely isolated leaf package, structurally
identical in shape to `argus/project/` (036) one level down.

---

## Ownership Hierarchy

```
Workspace             (this package - implemented)
    |
    v
Project               (argus.project.project - Package 036, pre-existing)
    |
    v
Goal                  (does not exist yet - not implemented)
    |
    v
Plan                  (argus.planner.plan - Package 015, pre-existing)
    |
    v
Task                  (argus.task.task - Package 029, pre-existing)
```

`Workspace` is introduced as a standalone value object with no field
referencing `Project`, `Goal`, `Plan`, or `Task` - the ownership
arrows above describe the domain's own eventual conceptual shape, not
any code relationship this package creates. `Project`, `Plan`, and
`Task` already exist and are untouched by this package; `Goal` still
does not exist in any form in this codebase, and this package does
not create it.

The broader, still-conceptual hierarchy this package's own domain sits
within extends both above and below this five-level chain: above,
toward a still-undefined "Life" concept encompassing every Workspace a
person or organization might have; below, through the already-built
execution pipeline (`Capability Context -> Capability Executor ->
Capability`, Packages 033-035). None of that broader hierarchy is
implemented, referenced, or committed to by this package - it is
mentioned here only to situate `Workspace`'s own role as the
organizational apex of everything this codebase has built so far,
not the absolute top of every conceivable future concept.

---

## Future Relationship

Per this package's own explicit "Future Relationship" section: "A
Workspace will eventually own: Projects, Users, Shared Knowledge,
Shared Assets, Automations, Credentials, Configuration, Policies,
Models, Memory. Do NOT implement these relationships yet. Document
them only." None of these ten relationships are implemented by this
package - `Workspace` holds no `projects` field, no `users` field, and
so on. Ten owned entity categories are named here, versus six for
`Project` (036) - `Workspace`'s own "highest-level organizational
boundary" role names a broader set of concerns (identity, shared
resources, automation, security, configuration) than `Project`'s own
narrower "long-running work" role, matching the Architectural
Position's own description of a Workspace as the boundary "for
identity, memory, permissions, configuration, automation, and
collaboration" - broader in kind, not merely in count, than the work a
single Project undertakes.

A future package would most likely add each such relationship the
same way `Task` gained `relationships` in Package 031: a new,
defaulted, ordered collection field declared after `status` and
before `metadata`, with a corresponding
`with_<relationship>()`/`with_<relationship>s()`/`clear_<relationship>s()`
trio added to `WorkspaceBuilder`, mirroring `TaskBuilder`'s own shape.
This is a documented expectation about a future package's own likely
shape, not a commitment this package makes.

---

## Example Workspace Structures

Illustrative only - no code in this package constructs any of these;
they exist to show how the five example names this package's own work
order gives might map onto genuinely different real-world boundaries:

- **"Joel Christensen"** - a personal Workspace, its eventual Projects
  spanning whatever mix of personal and professional work one person
  manages under a single identity.
- **"Deline Box & Display"** / **"Just Tallow"** - two distinct
  business Workspaces, each presumably owning its own Projects, Users,
  Credentials, and Configuration, kept separate from each other and
  from the personal Workspace above - the same "organizational
  boundary" the work order's own Objective names, made concrete as
  two businesses that should never share Automations or Shared Assets
  by default.
- **"Family"** - a Workspace scoped to shared household concerns,
  plausibly owning Shared Knowledge and Shared Assets relevant to
  multiple people rather than one.
- **"Sandbox"** - a Workspace explicitly for experimentation, its
  eventual Policies and Configuration presumably far looser than a
  production business Workspace's own.

---

## Engineering Decision

**Why `WorkspaceMetadata`'s own field order follows `ProjectMetadata`'s
precedent rather than this package's own literal listed order.**
Every metadata module's own "follow existing conventions" instruction
has settled a field-*order* tension since Package 028; this package's
own explicit "Follow the metadata conventions established throughout
ArgusOS" is the same instruction, but this time "established... 
throughout ArgusOS" has a direct answer, since `ProjectMetadata` (036)
already resolved this exact six-field composition (including
`owner`/`tags`) in a specific order. Following that order exactly,
rather than the current work order's own different literal ordering
(`created_at, owner, correlation_id, version, ...`), is both more
consistent with the dominant instruction's own plain meaning and
produces two structurally identical metadata modules differing only in
what domain object they describe - the more defensible outcome.

**Why `owner`/`tags` are not settable through `WorkspaceBuilder`.**
Identical reasoning to `ProjectMetadata`'s own precedent (036):
`WorkspaceBuilder`'s own Responsibilities list names exactly "assign
name, assign description, assign status, assign metadata" - one
bullet for metadata, not separate bullets for `owner`/`tags`.
Extending the established "system-managed metadata fields are not
builder-overridable" rule to these two fields (already applied to
`ProjectMetadata`) keeps both sibling packages' own builders
symmetric, rather than introducing an inconsistency where `Project`
and `Workspace` - two structurally near-identical packages - diverge
on this one point for no principled reason.

**Why `WorkspaceStatus`'s own default is `ACTIVE`, not a
"not-yet-begun" state like `ProjectStatus.PLANNING`.** Both
`ProjectStatus` and `WorkspaceStatus` default to their own
first-listed member, per this codebase's own established convention.
The two enums' own first-listed members simply differ in meaning
because the work orders themselves list them differently
(`ProjectStatus`: `PLANNING, ACTIVE, PAUSED, COMPLETED, ARCHIVED`;
`WorkspaceStatus`: `ACTIVE, INACTIVE, ARCHIVED`) - a Workspace's own
work order never lists a "not yet begun" state at all, so there is no
literal member this package could have defaulted to instead.
`WorkspaceStatus.ACTIVE` as the default is the literal, unforced
consequence of applying an existing convention to a different member
list, not a new or separately-justified design choice.

**Why no `Goal` object is introduced, even minimally.** Identical
reasoning to Package 036's own equivalent decision: the work order's
own Constraints are explicit ("Do NOT... redesign Goal"), and nothing
in this codebase has ever had a standalone `Goal` object to redesign
in the first place - there is genuinely nothing to touch.

---

## Repository Verification Note

Before writing any code, the uploaded repository ("ArgusOS (36).zip")
was verified fresh against this package's own general pre-flight
instruction. No anomaly was found - the twenty-third consecutive
clean pre-flight (015-037). HEAD (`9868b49`, "Synchronize repository
version with v0.3.6 release") is a clean, single-commit descendant of
tag `v0.3.6` (which points to `ddfd630`, "Implement Package 036
Project Framework"), confirmed via `git merge-base --is-ancestor
v0.3.6 HEAD`. `git diff v0.3.6..HEAD --stat` shows exactly the
expected one-line version-sync commit - `CORE_SERVICES_VERSION` moved
from `"0.3.5"` to `"0.3.6"`, a patch increment, the Founder's own
release choice following Package 036's own integration. `python -m
pytest` passing (2369 passed, 38 subtests); `python -m unittest
discover -s tests` passing (2281); `python -m unittest discover -s
argus/tests` passing (64); `python main.py` starting and shutting down
cleanly (exit 0); `CORE_SERVICES_VERSION == "0.3.6"` matching tag
`v0.3.6`. `argus/workspace/` confirmed absent from the repository
prior to this package, and no `Workspace` naming collision anywhere.
No anomaly of any kind was found during pre-flight for this package.

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
    workspace/
        __init__.py                              (new)
        workspace.py                              (new)
        metadata.py                               (new)
        builder.py                                (new)
        status.py                                 (new)
        interfaces.py                              (new)
        exceptions.py                              (new)
factory/
    packages/
        037_WORKSPACE_FRAMEWORK.md                (new)
tests/
    test_workspace.py                             (new)
    test_workspace_builder.py                     (new)
    test_workspace_metadata.py                    (new)
    test_workspace_status.py                      (new)
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
source file anywhere in the repository was touched. This is the
second consecutive package (after 036) whose own "Files Modified"
list contains no source or test file at all - purely additive to
`argus/workspace/` and this package's own documentation.

---

## Test Results

New workspace suites:
```
python -m pytest tests/test_workspace.py tests/test_workspace_builder.py tests/test_workspace_metadata.py tests/test_workspace_status.py -q
73 passed in 0.06s
```

Canonical suite (`tests/`):
```
python -m unittest discover -s tests
Ran 2354 tests in 0.168s
OK
```

Per this package's own explicit testing instruction:
```
python -m pytest
2442 passed, 38 subtests passed in 1.61s
```

The duplicate `argus/tests/` also verified passing (unmodified by
this package):
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
immutability, builder behavior, metadata defaults, enum behavior,
equality, serialization consistency:

- `tests/test_workspace_status.py` (new, 8 tests): members, values,
  plain-Enum shape, no-extra-methods, round trips, equality/identity.
- `tests/test_workspace_metadata.py` (new, 22 tests): defaults, field
  set/order (matching `ProjectMetadata`'s own precedent), `owner`
  acceptance, `tags` tuple-wrapping/defensive-copy, `extra`
  wrapping/defensive-copy/immutability, dataclass immutability,
  equality.
- `tests/test_workspace.py` (new, 19 tests): defaults, field set/order
  (`metadata` last), every example name from the work order, default
  status confirmation, object immutability, deepcopy/pickle/JSON-
  suitability, equality.
- `tests/test_workspace_builder.py` (new, 24 tests): identity/not-an-
  IService/no `with_workspace_id()`/no `with_owner()`/no
  `with_tags()`, every `with_*()` method's chaining/overwrite/
  validation behavior, confirmation that `with_metadata("owner", ...)`
  populates `extra` only, `build()` independence/full chain.

---

## Coverage

Measured with `coverage.py`,
`python -m coverage run --source=argus.workspace -m pytest`:

| Module | Stmts | Miss | Cover |
|---|---|---|---|
| `argus/workspace/__init__.py` | 7 | 0 | 100% |
| `argus/workspace/builder.py` | 35 | 0 | 100% |
| `argus/workspace/exceptions.py` | 2 | 0 | 100% |
| `argus/workspace/interfaces.py` | 15 | 0 | 100% |
| `argus/workspace/metadata.py` | 17 | 0 | 100% |
| `argus/workspace/status.py` | 5 | 0 | 100% |
| `argus/workspace/workspace.py` | 11 | 0 | 100% |

100% coverage across the entire new `argus/workspace/` package (92
statements) - reached on the first measurement, no post-hoc
gap-closing needed. No other module was modified by this package, so
no other module's coverage is reported here.

---

## Known Limitations

- **No ownership relationships exist yet** - `Workspace` holds no
  reference to `Project`, `User`, `Shared Knowledge`, `Shared Asset`,
  `Automation`, `Credential`, `Configuration`, `Policy`, `Model`, or
  `Memory`. "Do NOT implement these relationships yet. Document them
  only."
- **`Goal` does not exist as a domain object anywhere in this
  codebase** - the ownership chain `Workspace -> Project -> Goal ->
  Plan -> Task` has two implemented links (`Workspace`, `Project`),
  one missing link (`Goal`), and two pre-existing links (`Plan`,
  `Task`).
- **`owner`/`tags` are not settable through `WorkspaceBuilder`** - a
  deliberate consequence of this codebase's own "system-managed
  metadata fields are not builder-overridable" convention, matching
  `ProjectMetadata`'s own identical treatment (036).
- **No transition logic on `WorkspaceStatus`** - nothing advances a
  `Workspace` from `ACTIVE` to `INACTIVE`/`ARCHIVED`, or between any
  other pair of states; every state is reachable only via an explicit
  `WorkspaceBuilder.with_status()` call.
- **No persistence, no concurrency, no scheduling, no runtime
  behavior of any kind** - "Workspace is a passive domain object
  only."
- **No integration with any existing package** - `Project`, `Planner`,
  `Response`, `Runtime`, `ExecutionEngine`, `CapabilityExecutor`,
  `CapabilityContext`, and `bootstrap.py` are all completely
  untouched.

---

## Release Rules

Per the Founder's standing release process, this package was
implemented and verified entirely within the supplied repository. No
`git commit`, `git tag`, push, or git-history modification of any
kind was performed. `CORE_SERVICES_VERSION` was not changed and
remains `"0.3.6"`. This package is not being reported as complete -
final validation, integration, version bump, commit, tag, and release
remain the Founder's responsibility, to be performed against the live
repository after independent regression testing.
