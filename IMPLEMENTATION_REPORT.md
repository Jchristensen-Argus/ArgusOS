# ArgusOS Implementation Report — Package 030: Plan Task Integration

## 1. Package Overview

Package 030 extends the Planning domain so that a Plan owns an ordered collection of immutable Task objects. "This package does not execute tasks. It only allows the Planner to describe work at a finer level of detail." Unlike Package 029 (Task Model), which was deliberately isolated and modified no pre-existing file, this package is the first to connect `Task` to anything else in this codebase — "The Planner owns Tasks, but does not perform them." `Plan` (`argus/planner/plan.py`) and `PlanningSession` (`argus/planning/session.py`) both gained a new `tasks: Sequence[Task]` field, defaulting to an empty tuple and preserving insertion order; `PlanningSessionBuilder` (`argus/planning/builder.py`) gained `with_task()`, `with_tasks()`, and `clear_tasks()`; `Planner.create_plan()` (`argus/planner/planner.py`) gained an optional `tasks` keyword parameter validated by a new `_validate_tasks()` helper (rejecting non-list/tuple input, non-`Task` items, and duplicate `task_id`s), and `Planner.plan_session()` now carries `PlanningSession.tasks` through to the returned `Plan.tasks` unchanged. The central engineering decision — resolving a genuine conflict between the work order's own "Plan" section (literally naming the class `Plan`) and its own Architectural Position diagram (whose field list exactly matches `PlanningSession`, not `Plan`) — was to implement `tasks` on both objects, bridged by `plan_session()`, rather than picking one reading and leaving the other's own literal instruction unaddressed. `argus/bootstrap.py` is completely unchanged — confirmed via `git diff --stat` showing zero lines changed; `CORE_SERVICES_VERSION` remains `"0.2.9"`. 1,709 tests total pass under `python -m unittest discover -s tests`, and `python -m pytest` also passes (1,797 passed, 38 subtests passed). `python main.py` starts and shuts down cleanly.

## 2. Repository Verification Note

Before writing any code, the uploaded repository ("ArgusOS (29).zip") was verified fresh against this package's own general pre-flight instruction ("verify repository state, verify version consistency, verify HEAD/tag ancestry, run smoke validation").

No anomaly was found — the sixteenth consecutive clean pre-flight (015-030). HEAD (`14bb4fc`, "Synchronize repository version with v0.2.9 release") is a clean, single-commit descendant of tag `v0.2.9` (which points to `88f3e41`, "Implement Package 029 Task Model"), confirmed via `git merge-base --is-ancestor v0.2.9 HEAD`. `git diff v0.2.9..HEAD --stat` shows exactly the expected one-line version-sync commit (`argus/bootstrap.py`, 1 insertion, 1 deletion) — no anomaly. Every substantive check passed cleanly: `python -m pytest` passing (1756 passed, 38 subtests); `python -m unittest discover -s tests` passing (1668); `python -m unittest discover -s argus/tests` passing (64); `python main.py` starting and shutting down cleanly (exit 0); `CORE_SERVICES_VERSION == "0.2.9"` matching tag `v0.2.9`.

Per the Founder's explicit release rules, this implementation was built, tested, and verified entirely within the supplied repository. No `git commit`, `git tag`, push, or git-history modification of any kind was performed, `CORE_SERVICES_VERSION` was not changed by this package, and this package is not being reported as complete — final validation, integration, release, tagging, and git operations are the Founder's responsibility, to be performed against the live repository after independent regression testing.

## 3. Architectural Rationale

No `design/specifications/PLAN_TASK_INTEGRATION.md` exists — the same situation as every package since 002 that lacked its own upstream specification file. Every structural decision traces to the Founder's explicit work order. The full rationale for each decision below is also recorded in `factory/packages/030_PLAN_TASK_INTEGRATION.md`, in the source code's own module docstrings, and is only summarized here.

**Decision 1 — `tasks` is implemented on both `Plan` and `PlanningSession`, not just one.** The work order's own "Plan" section literally names the class `Plan` ("Extend the existing immutable: Plan. Add: tasks"), but its own Architectural Position diagram's field list ("Goals / Constraints / Metadata / Tasks") exactly matches `PlanningSession`'s actual fields, not `Plan`'s — `Plan` has never had `goals`/`constraints`. The "Planning Builder" section's own "the existing PlanningBuilder" can only mean `PlanningSessionBuilder`, the only class with "Builder" in its own name in either package. Implementing both, bridged by `Planner.plan_session()` carrying `PlanningSession.tasks` through to `Plan.tasks` (mirroring the identical Package 024 precedent for `constraints`), is the only reading under which every sentence in the work order is literally true simultaneously. See Section 9 and `factory/packages/030_PLAN_TASK_INTEGRATION.md`'s own "Engineering Decision" section for the full reasoning.

**Decision 2 — duplicate `task_id` rejection is identity-based, enforced in the builder/service, never in the frozen value objects.** Consistent with this codebase's established id-based duplicate-prevention pattern (`CapabilityRegistry`, `PluginManager`) and its established "validation lives in the builder/service, not the value object" division of responsibility — `Plan.steps` has never rejected duplicates at the dataclass level either. Enforced in two places, mirroring Decision 1's dual-object resolution: `PlanningSessionBuilder.with_task()` and a new `Planner._validate_tasks()` helper used by `create_plan()`.

**Decision 3 — "Only the Planning package changes" is read as "the planning domain" (both `argus/planning/` and `argus/planner/`), not the single literal directory.** The work order's own Planner section explicitly names "Planner," a class living in `argus/planner/`, as needing an update — only consistent with the broader reading. The explicitly-excluded packages (Agent, Pipeline, Response, Execution Trace, Runtime, Scheduler) remain completely untouched regardless.

**Decision 4 — `Planner.create_plan()` gained an optional `tasks` parameter beyond what the work order's own Testing section explicitly names.** The Testing section focuses on `plan_session()`'s carry-through; `create_plan()`'s own direct API needed some way to set `Plan.tasks` too, mirroring how `metadata` is already an optional keyword parameter there.

## 4. IService Adoption

None. This package introduces no new class of any kind — it extends four already-shipped classes (`Plan`, `PlanningSession`, `PlanningSessionBuilder`, `Planner`), none of which is or has ever been an `IService` implementation. No new entry was added to `design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`.

## 5. Directory Tree (files touched)

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
factory/
    packages/
        030_PLAN_TASK_INTEGRATION.md          (new)
    ROADMAP.md                               (modified)
tests/
    test_plan.py                             (modified)
    test_planner.py                          (modified)
    test_planner_session_integration.py      (modified)
    test_planning_session.py                 (modified)
    test_planning_builder.py                 (modified)
CHANGELOG.md                                 (modified)
DEVLOG.md                                    (modified)
IMPLEMENTATION_REPORT.md                     (replaced — this file)
```

No file outside this list was created, deleted, moved, or modified. Per this package's own explicit Integration Rules — "Do not modify: Agent, Pipeline, Response, Execution Trace, Runtime, Scheduler. Only the Planning package changes." — `argus/bootstrap.py`, `argus/task/`, `argus/agent/`, `argus/pipeline/`, `argus/response/`, `argus/trace/`, `argus/runtime/`, `argus/reasoning/`, `argus/decision/`, `argus/memory/`, `argus/memory_integration/`, `argus/knowledge/`, `argus/knowledge_graph/`, `argus/context/`, `argus/conversation/`, `tests/test_bootstrap.py`, `argus/tests/test_bootstrap.py`, and `argus/events/event_types.py` were left completely untouched — confirmed via `git diff --stat` showing zero lines changed in any of them.

## 6. Integration Notes

- `argus/bootstrap.py` was not modified at all — confirmed via `git diff --stat -- argus/bootstrap.py` showing zero lines changed. `CORE_SERVICES_VERSION` remains `"0.2.9"`.
- No `tests/test_bootstrap.py`/`argus/tests/test_bootstrap.py` change — no new core service was registered.
- `argus/events/event_types.py` was not modified — no new `EventType` members; `Planner.create_plan()`/`plan_session()` continue publishing the same `PLAN_CREATED`/`PLAN_UPDATED` events with unchanged payloads.
- `argus/task/` was not modified at all — only new inbound dependencies were added *onto* `Task` from four Planning/Planner modules (`argus/planner/plan.py`, `argus/planner/planner.py`, `argus/planning/session.py`, `argus/planning/builder.py`, plus the two `interfaces.py` files), all typing-only or direct-construction-validation usages.
- `IPlanner.create_plan()` and `IPlanningSessionBuilder`'s three new abstract methods were both updated in lockstep with their concrete implementations, keeping interface and implementation in sync per this codebase's established convention.

## 7. Test Results

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

Per this package's explicit testing instruction:
```
python -m pytest
1797 passed, 38 subtests passed in 1.15s
```

The duplicate `argus/tests/` also verified passing standalone (unaffected — not touched by this package):
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

Measured with `coverage.py`, `python -m coverage run -m pytest`:

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

100% coverage across every modified Planning/Planner file (339 statements total) — reached on the first measurement, no post-hoc gap-closing needed.

## 9. Engineering Decisions / Deviations from the Work Order

- **`tasks` implemented on both `Plan` and `PlanningSession`, bridged by `Planner.plan_session()`.** The work order's own "Plan" section and its own Architectural Position diagram describe two different objects when read literally against each other — see Section 3, Decision 1, and `factory/packages/030_PLAN_TASK_INTEGRATION.md`'s own dedicated "Engineering Decision" section for the full reasoning, including the two rejected alternative readings.
- **Duplicate `task_id` rejection is identity-based, enforced twice (once per object), never in the frozen value objects themselves.** See Section 3, Decision 2.
- **"Only the Planning package changes" read broadly as "the planning domain."** See Section 3, Decision 3 — distinguished from a loosening of scope, since the explicitly-excluded packages remain completely untouched.
- **`Planner.create_plan()` gained an optional `tasks` parameter beyond the work order's own explicit Testing-section focus on `plan_session()`.** See Section 3, Decision 4.
- **`CORE_SERVICES_VERSION` remains `"0.2.9"`, unchanged by this package.**
- **`argus/bootstrap.py` required zero changes** — a direct, verified consequence of this package introducing no new class of any kind, not an oversight.
- **No coverage gap required a post-hoc fix** — 100% was reached on the first `coverage run` across every modified Planning/Planner file.
- **One edit script required a diagnostic-and-retry pass** — the first attempt to edit `argus/planner/plan.py`'s own module docstring failed its fifth of six sequential assertions because the actual "Responsibilities:" text didn't match this session's own assumed wording; none of the six edits landed on that attempt (confirmed via `git diff --stat` showing no change), diagnosed with a standalone substring-check script, and fixed by correcting the one mismatched block before re-running the rest successfully. Every other file in this package applied cleanly on the first attempt.

## 10. Known Limitations

- **A `Plan`/`PlanningSession` constructed directly (not via `Planner`/`PlanningSessionBuilder`) performs no duplicate-`task_id` rejection of its own** — `Plan(originating_intent=..., tasks=[t1, t1_duplicate])` succeeds silently at the dataclass level, exactly like `Plan`'s own pre-existing, identical behavior toward duplicate `steps`.
- **Tasks are never generated, decomposed, or scheduled by anything in this package** — by design. A `Plan`'s `tasks` collection is populated exclusively by whatever the caller explicitly supplies; no goal, constraint, or intent is ever translated into a `Task` automatically.
- **No task graph, dependency ordering, or workflow relationship between Tasks exists** — `Plan.tasks`/`PlanningSession.tasks` are flat, ordered sequences with no notion of one Task depending on another.
- **`clear_tasks()` has no counterpart on `goals`/`constraints`** — an intentional asymmetry, since this package's own work order names `clear_tasks()` explicitly and neither prior package's own work order asked for the equivalent on any other collection field.
- **Nothing yet reads `Plan.tasks` back out for any purpose** — no `AgentService`, `ResponseEngine`, or `ExecutionTrace` step references `Task` in any way; this package stops at storage and pass-through, per its own explicit "does not execute tasks" constraint.
- No execution, no scheduling, no workflows, no tools, no persistence, no concurrency — unchanged from every prior package in this phase.
- The repository's stray `argus/` duplicate tree and legacy pre-Factory files remain unresolved, out of scope per the Founder's explicit repository rules.

## 11. Repository-Derived Package Metrics (measured, not estimated)

Measured via `git diff --stat` against the working tree's unmodified base commit `14bb4fc` (no commit was made — see Section 2):

- Files Created: 1 (`factory/packages/030_PLAN_TASK_INTEGRATION.md`)
- Files Modified: 14 (`argus/planner/plan.py`, `argus/planner/planner.py`, `argus/planner/interfaces.py`, `argus/planning/session.py`, `argus/planning/builder.py`, `argus/planning/interfaces.py`, `tests/test_plan.py`, `tests/test_planner.py`, `tests/test_planner_session_integration.py`, `tests/test_planning_session.py`, `tests/test_planning_builder.py`, `factory/ROADMAP.md`, `CHANGELOG.md`, `DEVLOG.md`) plus `IMPLEMENTATION_REPORT.md` itself (replaced) — 15 total
- Lines Added: 1,295 / Lines Removed: 156 (measured via `git diff --stat` across all 16 touched files, including this report's own replacement; every touched file outside this report's own self-replacement is purely additive — the 156 removed lines are entirely this file's own prior Package 029 content being overwritten with Package 030's own, plus incidental docstring-block replacements in `argus/planner/plan.py`/`planner.py`/`interfaces.py` and `argus/planning/session.py`/`builder.py`/`interfaces.py` where existing module docstrings were amended in place rather than purely appended to)
- Unit Tests: 1,709 passing in canonical `tests/` (net +41 vs. Package 029's 1,668: +5 `test_plan.py`, +4 `test_planning_session.py`, +14 `test_planning_builder.py`, +11 `test_planner.py`, +9 `test_planner_session_integration.py` — entirely additive, no test removed or replaced)
- Coverage: 100% (all 14 statements-bearing modules across `argus/planner/` and `argus/planning/`, 339 statements total)
- Public Classes: 0 new (four already-shipped classes extended: `Plan`, `PlanningSession`, `PlanningSessionBuilder`, `Planner`)
- Public Interfaces: 0 new (two already-shipped interfaces extended: `IPlanner`, `IPlanningSessionBuilder`)
- New Exceptions: 0 (existing `InvalidPlanError`/`InvalidPlanningSessionError` reused for all new validation paths)
- New Dependencies: 0 external; `argus/planner/` and `argus/planning/` each gained one new internal dependency (`argus.task.task.Task`) — `argus/task/` itself gained no new outbound dependency and remains dependent on nothing but the standard library
- External Libraries: 0 (standard library only)
- Architecture Deviations: 0 breaking changes (every new field defaults to an empty tuple, preserving every pre-030 call site's own behavior unchanged); 4 documented interpretive judgment calls (see Section 9)

## 12. Pre-Completion Checklist (per the Founder's explicit checklist)

- ✓ **`Plan.tasks` and `PlanningSession.tasks` both implemented — ordered, immutable, default empty, no duplicates (enforced in builder/service), preserving insertion order** — confirmed via dedicated test classes in `tests/test_plan.py` and `tests/test_planning_session.py`.
- ✓ **`PlanningSessionBuilder.with_task()`/`with_tasks()`/`clear_tasks()` implemented, builder remains the only mutable object** — confirmed via `tests/test_planning_builder.py`'s own dedicated test coverage.
- ✓ **`Planner` updated so Plans can contain Tasks; no task generation, no AI, no decomposition** — confirmed via `tests/test_planner.py`'s "does not generate tasks automatically" test and `tests/test_planner_session_integration.py`'s "Planner never generates its own tasks" test.
- ✓ **Do not modify: Agent, Pipeline, Response, Execution Trace, Runtime, Scheduler** — confirmed via `git diff --stat` on all six, zero lines changed.
- ✓ **No bootstrap changes; no new core services** — confirmed via `git diff --stat -- argus/bootstrap.py` showing zero lines changed.
- ✓ **No new EventTypes** — confirmed via `git diff --stat -- argus/events/event_types.py` showing zero lines changed.
- ✓ **Empty task list, single task, multiple tasks, duplicate rejection, insertion order, immutability, builder methods, planner propagation all tested** — confirmed via the corresponding dedicated test classes across all five modified test files.
- ✓ **100% coverage across all modified Planning files** — confirmed via `coverage.py` (339/339 statements).
- ✓ **No regressions** — `python -m unittest discover -s tests` reports `Ran 1709 tests ... OK`; `python -m pytest` reports `1797 passed, 38 subtests passed`; every one of Package 029's own 1,756 passing pytest tests still passes unchanged.
- ✓ **`python main.py` starts cleanly** — exit code 0.
- ✓ **No unintended repository modifications** — confirmed via `git status`/`git diff --stat`.
- ✓ **`CORE_SERVICES_VERSION` not modified** — confirmed still `"0.2.9"`.
- ✓ **No commit created** — confirmed via `git log` (HEAD unchanged at `14bb4fc`).
- ✓ **No tag created** — confirmed via `git tag -l` (unchanged: `v0.0.3`-`v0.2.9`, plus `charter-v1.0`).
- ✓ **Repository ready for architectural review** — all regression, smoke, and coverage checks pass locally; final integration, version bump, commit, and tag remain the Founder's responsibility.

## 13. Concise Implementation Summary

Package 030 extends the Planning domain so that a `Plan` (and, per the central Engineering Decision, a `PlanningSession` too) owns an ordered, immutable collection of `Task` objects. `Plan.tasks`/`PlanningSession.tasks` both default to an empty tuple, preserve insertion order, and reject no duplicates at the dataclass level (validation lives in the builder/service, matching `Plan.steps`'s own pre-existing precedent). `PlanningSessionBuilder` gained `with_task()`/`with_tasks()`/`clear_tasks()`, the first "reset a collection" method any builder in this codebase has ever exposed. `Planner.create_plan()` gained an optional `tasks` parameter validated by a new `_validate_tasks()` helper (identity-based duplicate rejection, matching `CapabilityRegistry`/`PluginManager`'s established pattern), and `Planner.plan_session()` now carries `PlanningSession.tasks` through to `Plan.tasks` unchanged — "The Planner simply preserves whatever Tasks are supplied during construction." The defining challenge was a genuine internal conflict in the work order itself between its "Plan" section (literally naming the class `Plan`) and its own Architectural Position diagram (whose field list matches `PlanningSession`, not `Plan`) — resolved by implementing both, rather than picking one reading and leaving the other's own literal instruction unaddressed. `argus/bootstrap.py` and every explicitly-excluded package (Agent, Pipeline, Response, Execution Trace, Runtime, Scheduler) remain completely untouched. 1,709 tests pass in `tests/` (`python -m pytest` also passes: 1,797 passed, 38 subtests), 100% coverage across every modified Planning/Planner file (339 statements). Built and verified entirely within the Founder-supplied repository; no commit, tag, push, or git-history change was made, and `CORE_SERVICES_VERSION` was not advanced, per instruction.

## 14. Architectural Observations

- This is the first package in this phase to extend two already-shipped objects simultaneously to resolve a single ambiguity, rather than choosing one interpretation outright (contrast Package 028's "Integration diagram vs. Dependency Rule" conflict, which was resolved by picking the Dependency Rule's own literal wording over the diagram's literal ordering). The dual-implementation approach taken here — implement both readings, then bridge them via the one delegation path (`plan_session()`) the work order's own third section already describes — is offered as a reusable precedent for any future package whose own work order similarly names one class in one section and describes a different class's fields in another.
- The Task Model (Package 029) named a concrete future architecture — "Plan -> Tasks -> Execution" — without wiring any of it up. This package wires up exactly the first arrow, "Plan -> Tasks," and stops there deliberately: nothing yet reads `Plan.tasks` back out for any purpose. The next arrow, "Tasks -> Execution," remains a named but entirely unbuilt target for a future package, per `factory/packages/030_PLAN_TASK_INTEGRATION.md`'s own "Future Execution Model" section.
- Every new field across this package defaults to an empty tuple, and every pre-030 call site — `Plan(originating_intent=...)`, `PlanningSession()`, `Planner.create_plan(intent)`, `Planner.plan_session(session)` — continues to produce the identical output it always has. This package's own regression suite is itself the clearest evidence of that: all 1,756 of Package 029's own passing pytest tests still pass completely unchanged, with zero modifications to any pre-existing assertion.
- The identity-based duplicate-rejection policy applied here (`task_id` equality) is now the third time this codebase has reached for the same `CapabilityRegistry`/`PluginManager` precedent rather than inventing a new duplicate-detection rule, reinforcing it as this codebase's own settled convention for "no duplicates" wherever a work order uses that phrase without further specification.
