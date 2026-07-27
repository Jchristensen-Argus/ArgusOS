# ArgusOS Implementation Report — Package 038: Goal Framework

## 1. Package Overview

Package 038 introduces the Goal domain. "A Goal represents a desired outcome within a Project. Projects own Goals. Goals own Plans. Plans own Tasks. Goals are passive domain objects only." A new package, `argus/goal/` (`__init__.py`, `goal.py`, `metadata.py`, `builder.py`, `status.py`, `priority.py`, `interfaces.py`, `exceptions.py`), introduces `Goal` (immutable — `goal_id`, `name`, `description`, `status`, `priority`, `metadata`, six fields, one more than `Project`/`Workspace`, every field defaulted), `GoalStatus` (a plain `Enum`, five members — `PLANNING`, `ACTIVE`, `PAUSED`, `COMPLETED`, `ABANDONED` — with no transition logic anywhere; `PLANNING` is the default), `GoalPriority` (a plain `Enum`, NOT an `IntEnum`, four members — `LOW`, `NORMAL`, `HIGH`, `CRITICAL` — no ordering behavior; `NORMAL` is the default, the first deliberate exception to this codebase's own "first-listed member is the default" convention), `GoalMetadata` (the identical `created_at`/`version`/`correlation_id`/`owner`/`tags`/`extra` composition `ProjectMetadata` (036) and `WorkspaceMetadata` (037) established, in the identical order), and `GoalBuilder` (the one mutable object in this package, the first of the three sibling builders to expose a genuinely new singular setter, `with_priority()`). This package introduces no runtime behavior, no integration with any existing package, and no bootstrap changes of any kind — the third consecutive package (after 036, 037) whose own "Files Modified" list contains no pre-existing source or test file at all, purely additive. `CORE_SERVICES_VERSION` remains `"0.3.7"`. 2,446 tests total pass under `python -m unittest discover -s tests`, and `python -m pytest` also passes (2,534 passed, 38 subtests passed). `python main.py` starts and shuts down cleanly.

## 2. Repository Verification Note

Before writing any code, the uploaded repository ("ArgusOS (37).zip") was verified fresh against this package's own general pre-flight instruction ("verify repository state, verify version consistency, verify HEAD/tag ancestry, run smoke validation").

No anomaly was found — the twenty-fourth consecutive clean pre-flight (015-038). HEAD (`7666b8d`, "Synchronize repository version with v0.3.7 release") is a clean, single-commit descendant of tag `v0.3.7` (which points to `c44f3ef`, "Implement Package 037 Workspace Framework"), confirmed via `git merge-base --is-ancestor v0.3.7 HEAD`. `git diff v0.3.7..HEAD --stat` shows exactly the expected one-line version-sync commit — `CORE_SERVICES_VERSION` moved from `"0.3.6"` to `"0.3.7"`, a patch increment, the Founder's own release choice following Package 037's own integration; no anomaly. Every substantive check passed cleanly: `argus/goal/` confirmed absent from the repository prior to this package; `python -m pytest` passing (2442 passed, 38 subtests, prior to this package's own new tests); `python -m unittest discover -s tests` passing (2354); `python -m unittest discover -s argus/tests` passing (64); `python main.py` starting and shutting down cleanly (exit 0); `CORE_SERVICES_VERSION == "0.3.7"` matching tag `v0.3.7`. No naming collision or other architectural surprise arose during this package's own pre-flight — no `Goal` object exists anywhere in this codebase prior to this package, confirmed by inspection, matching this package's own explicit scope (Goal only, filling the one remaining gap between `Project` and `Plan`).

Per the Founder's explicit release rules, this implementation was built, tested, and verified entirely within the supplied repository. No `git commit`, `git tag`, push, or git-history modification of any kind was performed, `CORE_SERVICES_VERSION` was not changed by this package, and this package is not being reported as complete — final validation, integration, release, tagging, and git operations are the Founder's responsibility, to be performed against the live repository after independent regression testing.

## 3. Architectural Rationale

No `design/specifications/GOAL_FRAMEWORK.md` exists — the same situation as every package since 002 that lacked its own upstream specification file. Every structural decision traces to the Founder's explicit work order. The full rationale for each decision below is also recorded in `factory/packages/038_GOAL_FRAMEWORK.md`, in the source code's own module docstrings, and is only summarized here.

**Decision 1 — `GoalMetadata`'s own field order follows `ProjectMetadata`'s and `WorkspaceMetadata`'s own established precedent (036, 037) directly, with no genuine tension to resolve.** This package's own work order names "Project and Workspace" outright as the convention source — "Follow the existing metadata conventions established by Project and Workspace" — leaving no ambiguity between a literal listed order and an established precedent, unlike Packages 036 and 037's own more interpretive resolutions. `GoalMetadata` follows the identical `created_at`, `version`, `correlation_id`, `owner`, `tags`, `extra` order a third time.

**Decision 2 — `owner`/`tags` are not settable through `GoalBuilder`.** Identical reasoning to `ProjectMetadata`'s and `WorkspaceMetadata`'s own precedent (036, 037) — `GoalBuilder`'s own Responsibilities list names exactly "assign name, assign description, assign status, assign priority, assign metadata," one bullet for metadata. Extending the established "system-managed metadata fields are not builder-overridable" rule keeps `GoalBuilder` consistent with its two siblings for these two specific fields.

**Decision 3 — `with_priority()` IS implemented on `GoalBuilder`, unlike `with_owner()`/`with_tags()`.** Although `priority` is, like `owner`/`tags` before it, a genuinely new field no sibling package's own builder exposed, the distinguishing factor is twofold: `priority` is a top-level `Goal` field, not a `GoalMetadata` sub-field, and this package's own Responsibilities list names "assign priority" as its own explicit bullet, structurally identical to "assign status" — not folded under a single "assign metadata" bullet the way `owner`/`tags` are. `with_priority()` is therefore implemented as a full validated singular-field setter.

**Decision 4 — `GoalPriority.NORMAL`, not `GoalPriority.LOW`, is the default.** Every enum-typed field default in this codebase to date has matched its enum's own first-listed member (`TaskStatus.PENDING`, `PlanStatus.CREATED`, `ProjectStatus.PLANNING`, `WorkspaceStatus.ACTIVE`, `GoalStatus.PLANNING`). Applying that same pattern mechanically to `GoalPriority` would default `Goal.priority` to `LOW`, but this would misrepresent "priority never specified" as "known to be low priority." `Goal.priority` therefore deliberately defaults to `GoalPriority.NORMAL`, documented in `priority.py`'s own module docstring as the first genuine exception to the convention — a deliberate deviation, not an oversight, and flagged explicitly rather than folded in silently.

**Decision 5 — `GoalPriority` is a plain `Enum`, not an `IntEnum` or other ordered variant.** The work order states "No ordering behavior" despite `LOW, NORMAL, HIGH, CRITICAL` reading as an intuitively ordered scale. Confirmed directly via `issubclass(GoalPriority, int)` returning `False` and `GoalPriority.LOW < GoalPriority.HIGH` raising `TypeError`, both directly tested rather than assumed from the class declaration alone.

**Decision 6 — `GoalStatus`'s terminal member is `ABANDONED`, not `ARCHIVED`.** A literal reading of this package's own distinct member list, which differs from `ProjectStatus`'s and `WorkspaceStatus`'s own shared `ARCHIVED` vocabulary. Nothing in this package's own instructions suggested unifying the terminology, and a Goal that's abandoned is conceptually distinct from a Project or Workspace that's archived.

## 4. IService Adoption

No new `IService` adopter is introduced by this package. `IGoalBuilder` does not inherit `IService` — the same "not an IService" shape every prior builder interface in this codebase already established. This package contributes no directed-adoption data point to `design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`, the same "contributes no data point" situation Packages 033, 035, 036, and 037 were all in — no new core service, no new `resolve()`/`execute()`-style method to evaluate against ADR-0002's own criterion.

## 5. Directory Tree (files touched)

```
argus/
    goal/
        __init__.py                          (new)
        goal.py                              (new)
        metadata.py                          (new)
        builder.py                           (new)
        status.py                            (new)
        priority.py                          (new)
        interfaces.py                        (new)
        exceptions.py                        (new)
factory/
    packages/
        038_GOAL_FRAMEWORK.md                (new)
    ROADMAP.md                               (modified)
tests/
    test_goal.py                             (new)
    test_goal_builder.py                     (new)
    test_goal_metadata.py                    (new)
    test_goal_status.py                      (new)
    test_goal_priority.py                    (new)
CHANGELOG.md                                 (modified)
DEVLOG.md                                    (modified)
IMPLEMENTATION_REPORT.md                     (replaced — this file)
```

No file outside this list was created, deleted, moved, or modified. Per this package's own explicit constraints — "Do not redesign Workspace, Project, Plan, Task, Execution, Bootstrap. Do not introduce persistence, AI, automation, plugins" — `argus/bootstrap.py`, `argus/project/`, `argus/workspace/`, `argus/task/`, `argus/task_relationship/`, `argus/planner/`, `argus/planning/`, `argus/pipeline/`, `argus/response/`, `argus/trace/`, `argus/runtime/`, `argus/dispatcher/`, `argus/plugins/`, `argus/connectors/`, `argus/knowledge_graph/`, `argus/capability/`, `argus/capability_executor/`, `argus/capability_context/`, `argus/execution_engine/`, `argus/agent/`, and `argus/events/event_types.py` were left completely untouched — confirmed via `git diff --stat` showing zero lines changed in any of them. This is the third consecutive package (after 036, 037) whose own Directory Tree contains no `(modified)` entry under `argus/` at all.

## 6. Integration Notes

- None. "No runtime behavior yet. No Planner changes. No Execution changes. No Capability changes. No Bootstrap changes. No Response changes. Introduce the Goal model only."
- `argus/goal/*.py` imports nothing outside its own sibling modules and the standard library (`uuid`, `dataclasses`, `datetime`, `types`, `enum`, `abc`, `typing`) — confirmed via source inspection.
- Source-inspection confirms no file anywhere else in the repository imports anything from `argus.goal` — this package is a genuinely isolated leaf, referenced by nothing, structurally identical in shape to `argus/project/` (036) and `argus/workspace/` (037).

## 7. Test Results

New goal suites:
```
python -m pytest tests/test_goal.py tests/test_goal_builder.py tests/test_goal_metadata.py tests/test_goal_status.py tests/test_goal_priority.py -q
92 passed in 0.08s
```

Canonical suite (`tests/`):
```
python -m unittest discover -s tests
Ran 2446 tests in 0.181s
OK
```

Per this package's explicit testing instruction:
```
python -m pytest
2534 passed, 38 subtests passed in 1.68s
```

The duplicate `argus/tests/` also verified passing (unmodified by this package):
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

## 8. Coverage Summary

Measured with `coverage.py`, `python -m coverage run --source=argus.goal -m pytest`:

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

100% coverage across the entire new `argus/goal/` package (113 statements) — reached on the first measurement, no post-hoc gap-closing needed. No other module was modified by this package.

## 9. Engineering Decisions / Deviations from the Work Order

- **`GoalMetadata`'s own field order follows `ProjectMetadata`'s/`WorkspaceMetadata`'s established precedent, directly named by the work order itself.** See Section 3, Decision 1.
- **`owner`/`tags` are not settable through `GoalBuilder`.** See Section 3, Decision 2.
- **`with_priority()` IS implemented, unlike `with_owner()`/`with_tags()`.** See Section 3, Decision 3.
- **`GoalPriority.NORMAL`, not `GoalPriority.LOW`, is the default — the first exception to the "first-listed member is the default" convention.** See Section 3, Decision 4.
- **`GoalPriority` is a plain `Enum`, verified to have no ordering behavior.** See Section 3, Decision 5.
- **`GoalStatus`'s terminal member is `ABANDONED`, not `ARCHIVED`.** See Section 3, Decision 6.
- **`CORE_SERVICES_VERSION` remains `"0.3.7"`, unchanged by this package.**
- **No coverage gap required a post-hoc fix** — 100% was reached on the first `coverage run`.

## 10. Known Limitations

- **No ownership relationships exist yet** — `Goal` holds no reference to `Project`, `Plan`, `Success metric`, `Milestone`, `Decision`, `Deadline`, `Risk`, or `Dependency`.
- **`Goal` does not own `Plan` anywhere in this codebase** — the ownership chain `Workspace -> Project -> Goal -> Plan -> Task` is now fully populated with domain objects at every link, but no ownership relationship between adjacent links is implemented.
- **`owner`/`tags` are not settable through `GoalBuilder`** — only via `with_metadata()`'s own `extra` mapping or direct `GoalMetadata` construction.
- **No transition logic on `GoalStatus`, no ordering behavior on `GoalPriority`.**
- **No persistence, no concurrency, no scheduling, no runtime behavior of any kind** — "Goals are passive domain objects only."
- **No integration with any existing package** — genuinely isolated, referenced by nothing.

## 11. Repository-Derived Package Metrics (measured, not estimated)

Measured via `git diff --stat` against the working tree's unmodified base commit `7666b8d` (no commit was made — see Section 2):

- Files Created: 13 (`argus/goal/__init__.py`, `goal.py`, `metadata.py`, `builder.py`, `status.py`, `priority.py`, `interfaces.py`, `exceptions.py`, `factory/packages/038_GOAL_FRAMEWORK.md`, `tests/test_goal.py`, `tests/test_goal_builder.py`, `tests/test_goal_metadata.py`, `tests/test_goal_status.py`, `tests/test_goal_priority.py` — fourteen counting all five test files individually)
- Files Modified: 3 (`factory/ROADMAP.md`, `CHANGELOG.md`, `DEVLOG.md`) plus `IMPLEMENTATION_REPORT.md` itself (replaced) — matching Packages 036/037's own minimal count
- Unit Tests: 2,446 passing in canonical `tests/` (net +92 from Package 037's 2,354: +8 `test_goal_status.py`, +11 `test_goal_priority.py`, +22 `test_goal_metadata.py`, +20 `test_goal.py`, +31 `test_goal_builder.py`)
- Coverage: 100% (all 8 statement-bearing modules across `argus/goal/`, 113 statements total)
- Public Classes: 2 new (`Goal`, `GoalMetadata`), 0 new services
- Public Interfaces: 1 new (`IGoalBuilder`)
- New Exceptions: 2 (`GoalError`, `InvalidGoalError`)
- New Core Services: 0 — `bootstrap.py` unmodified, twenty-six core services remain, sixteen `IService` adopters remain
- New Dependencies: 0 external, 0 internal — `argus/goal/` depends on nothing outside itself and the standard library, matching `argus/project/`'s and `argus/workspace/`'s own identical shape (036, 037)
- External Libraries: 0 (standard library only)
- Architecture Deviations: 0 breaking changes; 6 documented interpretive judgment calls (see Section 9)

## 12. Pre-Completion Checklist (per the Founder's explicit checklist)

- ✓ **`argus/goal/` implemented with all eight files** — confirmed via directory listing and `git diff --stat`.
- ✓ **`Goal`/`GoalStatus`/`GoalPriority`/`GoalMetadata` implemented per spec; GoalBuilder is the only mutable object** — confirmed via `Goal`/`GoalMetadata` being frozen dataclasses, `GoalStatus`/`GoalPriority` being plain Enums, and `GoalBuilder` being the sole class with mutable instance state.
- ✓ **Immutability, builder behavior, metadata defaults, enum behavior, equality, serialization consistency all tested** — confirmed via the corresponding dedicated test classes across all five new test files.
- ✓ **No Planner/Execution/Capability/Bootstrap/Response changes** — confirmed via `git diff --stat` showing zero lines changed in any of those packages.
- ✓ **No Workspace/Project/Plan/Task/Execution/Bootstrap redesign** — confirmed via `git diff --stat` on `argus/workspace/`, `argus/project/`, `argus/planner/`, `argus/planning/`, `argus/task/`, `argus/execution_engine/`, `argus/bootstrap.py`, zero lines changed in any of them.
- ✓ **No persistence, AI, automation, or plugins anywhere in this package** — confirmed via source inspection of `argus/goal/*.py`.
- ✓ **100% coverage across the new package** — confirmed via `coverage.py` (113/113 statements).
- ✓ **No regressions** — `python -m unittest discover -s tests` reports `Ran 2446 tests ... OK`; `python -m pytest` reports `2534 passed, 38 subtests passed`; every one of Package 037's own 2,442 passing pytest tests still passes.
- ✓ **`python main.py` starts cleanly** — exit code 0.
- ✓ **No unintended repository modifications** — confirmed via `git status`/`git diff --stat`.
- ✓ **`CORE_SERVICES_VERSION` not modified** — confirmed still `"0.3.7"`.
- ✓ **No commit created** — confirmed via `git log` (HEAD unchanged at `7666b8d`).
- ✓ **No tag created** — confirmed via `git tag -l` (unchanged: ending `v0.3.5`, `v0.3.6`, `v0.3.7`).
- ✓ **Repository ready for architectural review** — all regression, smoke, and coverage checks pass locally; final integration, version bump, commit, and tag remain the Founder's responsibility.

## 13. Concise Implementation Summary

Package 038 adds `argus/goal/`, the first-generation Goal Framework: `Goal` (immutable, `goal_id`/`name`/`description`/`status`/`priority`/`metadata`, six fields, every field defaulted), `GoalStatus` (a plain `Enum`, five members — `PLANNING`, `ACTIVE`, `PAUSED`, `COMPLETED`, `ABANDONED` — no transition logic, defaulting to `PLANNING`), `GoalPriority` (a plain `Enum`, NOT an `IntEnum`, four members — `LOW`, `NORMAL`, `HIGH`, `CRITICAL` — no ordering behavior, defaulting to `NORMAL` rather than `LOW`, the first deliberate exception to this codebase's own "first-listed member is the default" convention), `GoalMetadata` (the identical `created_at`/`version`/`correlation_id`/`owner`/`tags`/`extra` composition and order `ProjectMetadata`/`WorkspaceMetadata` established in Packages 036/037), and `GoalBuilder` (the one mutable object, exposing `with_name()`/`with_description()`/`with_status()`/`with_priority()`/`with_metadata()` but no `with_goal_id()`/`with_owner()`/`with_tags()`). This package introduces zero runtime behavior, zero integration with any existing package, and zero bootstrap changes — the third consecutive package whose own Files Modified list contains no pre-existing source or test file at all, purely additive. `argus/bootstrap.py`, `Project`, `Workspace`, `Plan`, `Task`, and every other existing package remain completely untouched. 2,446 tests pass in `tests/` (`python -m pytest` also passes: 2,534 passed, 38 subtests), 100% coverage across the entire new package (113 statements). Built and verified entirely within the Founder-supplied repository; no commit, tag, push, or git-history change was made, and `CORE_SERVICES_VERSION` was not advanced, per instruction.

## 14. Architectural Observations

- This is the third consecutive package (after 036, 037) to modify zero pre-existing source or test files, confirming this discipline is now a settled pattern for the organizational-tier domain packages, not a one-off or a two-package coincidence.
- The "value object with a dedicated builder, every field defaults" family gains its eleventh member with `Goal` — the third consecutive member (after `Project`, `Workspace`) whose own role is organizational rather than pipeline-related, and the first of the three to introduce both a genuinely new top-level field (`priority`) and a genuinely new enum type (`GoalPriority`) rather than simply mirroring its siblings' shape exactly.
- The ownership hierarchy above the execution pipeline, `Workspace -> Project -> Goal -> Plan -> Task`, is now fully populated with domain objects at every link for the first time in this codebase's history — three consecutive packages (036, 037, 038) each filling exactly one link, in top-down then gap-filling order. No ownership relationship between any two adjacent links has been implemented yet; a future package connecting any pair of these five objects would be the first to do so.
- The metadata field-order question, a genuine interpretive tension in Package 036 and a precedent-recognition exercise in Package 037, required no judgment at all in Package 038 — the work order named its own precedent directly. Three data points now agree exactly on `GoalMetadata`'s/`WorkspaceMetadata`'s/`ProjectMetadata`'s shared six-field composition and order, suggesting this shape is durable for any future organizational-tier metadata module, though that remains to be confirmed by a fourth.
- `GoalPriority.NORMAL` is the first deliberate break from the "first-listed member is the default" convention in this codebase's entire history — every prior enum default was a byproduct of mechanical dataclass field-default construction matching whatever a work order's own member list happened to name first, not an independently-reasoned choice. This package is the first to recognize that the convention itself is not a rule worth following blindly when it would produce a semantically incorrect default, and to document the deviation explicitly rather than let it pass unremarked.
