# ArgusOS Implementation Report — Package 015: Planner

## 1. Package Overview

Package 015 adds `argus/planner/`, a reasoning-only layer that converts an Intent into an ordered, inspectable Execution Plan before any capability resolution, dispatch, or execution occurs. `Planner` is a pure in-memory registry (`create_plan`/`add_step`/`remove_step`/`reorder_steps`/`validate_plan`/`get_plan`/`list_plans`) that performs no execution, no dispatch, and has no awareness of plugins whatsoever. `Plan` and `PlanStep` are immutable value objects; every Planner mutation replaces rather than mutates, and any structural change to a Plan's steps resets its status to `CREATED`, requiring re-validation. `validate_plan()`'s only touchpoint with the rest of the system is a read-only `ICapabilityRegistry.contains()` existence check - it never invokes a capability, dispatches an action, or calls a plugin. `Planner` is registered as ArgusOS's 15th core service, constructed last (immediately after the Intent Dispatcher) since it depends on a live Capability Registry reference, even though the target architecture diagram places it conceptually above Intent and the Capability Registry. `argus/dispatcher/`, `argus/capability/`, `argus/workflow/`, and `argus/plugins/` are all untouched by this package. All 674 pre-existing canonical tests still pass unchanged; 759 tests total pass under `python -m unittest discover -s tests`, and `python -m pytest` also passes (847 passed, 38 subtests passed). `python main.py` starts and shuts down cleanly.

## 2. Repository Verification Note

Before writing any code, the uploaded repository ("ArgusOS (14).zip") was verified fresh against the Founder's four explicit preconditions. All four passed on the first attempt, continuing the pattern established with Package 014's upload:

- Package 014 (Plugin Manager) present: `argus/plugins/` contains all five expected files.
- HEAD (`5fb57f1`, "Synchronize repository version with v0.1.4 release") confirmed a clean descendant of tag `v0.1.4` via `git merge-base --is-ancestor v0.1.4 HEAD`; `git diff 6c319ac..HEAD --stat` (where `6c319ac` is the commit `v0.1.4` itself points to, "Implement Package 014 Plugin Manager") confirmed the one intervening commit touches only `argus/bootstrap.py`, 1 insertion/1 deletion.
- `python -m pytest` passing (762 passed, 38 subtests) and `python -m unittest discover -s tests` passing (674), before any Package 015 code was written.
- `python main.py` starting and shutting down cleanly (exit 0).
- `CORE_SERVICES_VERSION == "0.1.4"` confirmed at `argus/bootstrap.py`.

No discrepancies of any kind were found this time - the filename matched the work order's own reference exactly.

Per the Founder's explicit release rules, this implementation was built, tested, and verified entirely within the supplied repository. No `git commit`, `git tag`, push, or git-history modification of any kind was performed, `CORE_SERVICES_VERSION` was not changed by this package, and this package is not being reported as complete — final validation, integration, release, tagging, and git operations are the Founder's responsibility, to be performed against the live repository after independent regression testing.

## 3. Architectural Rationale

No `design/specifications/PLANNER.md` exists — the same situation as Packages 002, 009, 010, 011, 012, 013, and 014. Every structural decision traces to the Founder's explicit work order. The full rationale for each decision below is also recorded in `factory/packages/015_PLANNER.md`'s "Architectural Decisions" section, in the source code's own module docstrings, and is only summarized here.

**Decision 1 — construction order follows dependency order, not diagram order.** The target architecture places Planner above Intent and the Capability Registry, but `Planner` still needs a live `ICapabilityRegistry` reference for `validate_plan()`, so it is constructed last (15th) in `bootstrap.py` - the same distinction Package 013 already drew for Capability Registry versus Intent Dispatcher.

**Decision 2 — `order` is recomputed by Planner, never set directly.** Every step-mutating method recomputes affected steps' `order` fields to match actual tuple position, avoiding a two-independent-trackers-of-the-same-fact risk this codebase has actively avoided since Package 005's `ServiceDescriptor`/`LifecycleManager` revision.

**Decision 3 — any structural mutation resets status to CREATED.** An inferred, not explicitly specified, business rule: a Plan's `VALIDATED`/`FAILED` status is a claim about its *current* steps, which becomes stale the instant those steps change.

**Decision 4 — `PLAN_REMOVED` (a suggested example event) was not added.** No "delete an entire Plan" operation exists in this package's scope; all three step-mutation operations are folded into `PLAN_UPDATED` with a `"change"` payload field instead.

**Decision 5 — `validate_plan()` failure raises and persists FAILED, but publishes nothing.** Mirrors `CapabilityRegistry.register()`'s/`PluginManager.register()`'s "failure raises, publishes nothing" precedent rather than `WorkflowEngine`'s/`IntentDispatcher`'s paired `*_FAILED`-event precedent - `validate_plan()` is a single validation gate, not a multi-step engine.

**Decision 6 — `PlanStatus.READY`/`COMPLETED` are defined but unreachable in Version 1.** Reserved for a future dispatch-integration and completion-reporting package, the same treatment Package 012 gave `workflow_id`s with no registered Workflow behind them yet.

## 4. IService Adoption — A Third Consecutive Non-Adopter Data Point for ADR-0002

`IPlanner` does NOT inherit `IService` — `Planner` is architecturally identical to Knowledge Service (006), Memory Service (007), Capability Registry (013), and Plugin Manager (014): fully usable the instant it is constructed, nothing for `start()`/`stop()` to meaningfully gate. `validate_plan()` was explicitly checked against ADR-0002's criterion since it performs the closest thing to "real work" of any non-adopter so far (a registry lookup plus a status transition) - it still has no phase distinct from any other method call, and the work order's own Objective ("It performs reasoning only") rules out a background phase by design. This is the third consecutive new deliberate non-adopter, appended to `design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md` as evidence the proposed criterion continues to work as a design-time filter even against the "closest call yet" case. Its Status remains `Proposed`, per standing instruction.

## 5. Directory Tree (files touched)

```
argus/
    planner/
        __init__.py                        (new)
        plan.py                            (new)
        step.py                            (new)
        planner.py                         (new)
        interfaces.py                      (new)
        exceptions.py                      (new)
    bootstrap.py                           (modified)
    events/
        event_types.py                     (modified)
design/
    decisions/
        0002_ISERVICE_ADOPTION_CRITERION.md   (modified — appended finding)
factory/
    packages/
        015_PLANNER.md                      (new)
    ROADMAP.md                              (modified)
tests/
    test_bootstrap.py                       (modified)
    test_step.py                            (new)
    test_plan.py                            (new)
    test_planner.py                         (new)
argus/tests/test_bootstrap.py               (modified — CORE_SERVICE_NAMES tuple only, per explicit instruction)
CHANGELOG.md                                (modified)
DEVLOG.md                                   (modified)
IMPLEMENTATION_REPORT.md                    (replaced — this file)
```

No file outside this list was created, deleted, moved, or modified. `argus/dispatcher/`, `argus/capability/`, `argus/workflow/`, `argus/plugins/`, `argus/lifecycle/test_lifecycle.py`, `argus/CHANGELOG.md`, `argus/DEVLOG.md`, `argus/IMPLEMENTATION_REPORT.md`, `argus/factory/`, and every legacy pre-Factory file were left completely untouched.

## 6. Integration Notes

- `Planner(event_bus, capability_registry)` — constructed in `bootstrap.py` immediately after the Intent Dispatcher, depending on the Event Bus and the Capability Registry only.
- This is now the 15th and last core service constructed in the bootstrap sequence.
- Registered in the Container (`"planner"`), in the Service Registry as a `ServiceDescriptor` (version `"0.1.4"`, the repository's currently released version — see Section 2), and in the Lifecycle Manager as `LifecycleState.REGISTERED` — matching the treatment of all fourteen prior core services. `Planner` has no gated method (not an `IService` adopter).
- `argus/events/event_types.py` extended with three new members: `PLAN_CREATED`, `PLAN_UPDATED`, `PLAN_VALIDATED`.
- Naming (`"planner"`) verified against the repository's own `tests/test_bootstrap.py::CORE_SERVICE_NAMES` convention before implementation.
- The repository's pre-existing, known stray duplicate `argus/tests/test_bootstrap.py` had its `CORE_SERVICE_NAMES` tuple synchronized with `"planner"` added, per the standing Repository Rule introduced in Package 011 — and only that tuple.
- Source-inspection confirms `argus/planner/planner.py` contains no `import argus.dispatcher`, `import argus.workflow`, or `import argus.plugins` statement anywhere - its only cross-package import beyond `argus.planner` itself is `argus.capability.interfaces.ICapabilityRegistry` (for typing/injection) and `argus.events`/`argus.intent` (Event Bus and Intent, both foundational, one-way dependencies already established by prior packages).

## 7. Test Results

Canonical suite (`tests/`):
```
python -m unittest discover -s tests
Ran 759 tests in 0.067s
OK
```

Per this package's explicit testing instruction:
```
python -m pytest
847 passed, 38 subtests passed in 0.54s
```

The synchronized duplicate `argus/tests/` also verified passing standalone (unaffected by the one-line sync):
```
python -m unittest discover -s argus/tests -p "test_*.py"
Ran 64 tests in 0.015s
OK
```

`pyflakes` on every new/modified module: clean, no warnings.

`python main.py`:
```
2026-07-25 16:11:52 [INFO] argus: ArgusOS application started.
2026-07-25 16:11:52 [INFO] argus: ArgusOS application shutting down.
```
Exit code 0.

## 8. Coverage Summary

Measured with `coverage.py`, `python -m coverage run -m pytest`:

| Module | Stmts | Miss | Cover |
|---|---|---|---|
| `argus/bootstrap.py` | 65 | 0 | 100% |
| `argus/events/event_types.py` | 57 | 0 | 100% |
| `argus/planner/__init__.py` | 6 | 0 | 100% |
| `argus/planner/exceptions.py` | 5 | 0 | 100% |
| `argus/planner/interfaces.py` | 19 | 0 | 100% |
| `argus/planner/plan.py` | 25 | 0 | 100% |
| `argus/planner/planner.py` | 82 | 0 | 100% |
| `argus/planner/step.py` | 14 | 0 | 100% |

Package 015 total (all `argus/planner/*` plus touched `argus/bootstrap.py`/`argus/events/event_types.py`): 273 statements, 100% covered — no accepted gaps. Full `argus/*` coverage: 99% (unchanged from Package 014; remaining gaps are pre-existing and out of scope).

## 9. Engineering Decisions / Deviations from the Work Order

- **`Planner` is constructed 15th (last), immediately after the Intent Dispatcher**, not in the diagram's top-to-bottom position — dependency order, not diagram order, governs construction. See Section 3, Decision 1.
- **`PlanStep.order` is recomputed by Planner on every structural mutation**, never set directly by a caller — avoids a two-trackers-of-the-same-fact risk. See Section 3, Decision 2.
- **Any structural mutation (`add_step`/`remove_step`/`reorder_steps`) resets a Plan's status to `CREATED`** — an inferred business rule protecting against a stale, no-longer-accurate `VALIDATED`/`FAILED` status. See Section 3, Decision 3.
- **`PLAN_REMOVED` was not added** despite being a work-order example — no corresponding "delete an entire Plan" operation exists; folded into `PLAN_UPDATED`'s payload instead. See Section 3, Decision 4.
- **`validate_plan()` failure raises `PlanValidationError` and publishes nothing** (rather than a paired `*_FAILED` event) — matches the simpler `CapabilityRegistry`/`PluginManager` registration-failure precedent. See Section 3, Decision 5.
- **`PlanStatus.READY`/`COMPLETED` are unreachable in Version 1** — reserved for future packages, per the work order's own status vocabulary. See Section 3, Decision 6.
- **`IPlanner` does not inherit `IService`** — a deliberate, ADR-0002-driven choice, explicitly checked against `validate_plan()`'s comparatively more substantial logic and still found not to qualify. See Section 4.
- **`CORE_SERVICES_VERSION` remains `"0.1.4"`, unchanged by this package.** Per the Founder's standing policy and this package's own explicit Version Policy.
- **`argus/tests/test_bootstrap.py` (duplicate tree) synchronized, tuple-only**, per the standing Repository Rule introduced in Package 011.

## 10. Known Limitations

- `PlanStatus.READY` and `PlanStatus.COMPLETED` are never produced by any Version 1 Planner method.
- `validate_plan()` checks capability-id existence only — it does not check a matching Capability's `enabled` flag or whether it actually supports the Plan's originating Intent's `IntentType`.
- The Planner is not wired to the Capability Registry/Dispatcher path in any direction beyond its one read-only check — nothing automatically creates a Plan from a resolved Intent, and nothing consumes a validated Plan to dispatch it.
- Plans are held only in memory; nothing persists across process restarts.
- The repository's stray `argus/` duplicate tree (beyond the one explicitly-required `test_bootstrap.py` sync) and legacy pre-Factory files remain unresolved, out of scope per the Founder's explicit repository rules.

## 11. Repository-Derived Package Metrics (measured, not estimated)

Measured via `git diff --stat`/`--numstat` against the working tree's unmodified base commit `5fb57f1` (no commit was made — see Section 2):

- Files Created: 9 (6 `argus/planner/*.py`, `factory/packages/015_PLANNER.md`, 3 new test files)
- Files Modified: 9 (`argus/bootstrap.py`, `argus/events/event_types.py`, `design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`, `factory/ROADMAP.md`, `tests/test_bootstrap.py`, `argus/tests/test_bootstrap.py`, `CHANGELOG.md`, `DEVLOG.md`, `IMPLEMENTATION_REPORT.md`)
- Lines Added: 2,035 / Lines Removed: 95 (measured via `git diff --stat` across all 19 touched files, including this report's own replacement)
- Unit Tests: 759 passing in canonical `tests/` (net +85 vs. Package 014's 674: +13 `test_step.py`, +17 `test_plan.py`, +52 `test_planner.py`, +3 `test_bootstrap.py` [20->23])
- Coverage: 100% (Package 015 modules), 99% (full `argus/*`)
- Public Classes: 3 (`Plan`, `PlanStep`, `Planner`)
- Public Interfaces: 1 (`IPlanner`)
- New Dependencies: 0
- External Libraries: 0 (standard library only)
- Architecture Deviations: 0 (see Section 9 for documented, non-architectural deviations)

## 12. Pre-Completion Checklist (per the Founder's explicit checklist)

- ✓ **Bootstrap registration** — `Planner(...)` constructed in `bootstrap.py`, registered in the Container as `"planner"`. Confirmed via `test_bootstrap_registers_planner_in_container`.
- ✓ **Service registration** — recorded as a `ServiceDescriptor` (version `"0.1.4"`) alongside all fourteen prior core services.
- ✓ **Lifecycle integration** — registered in the Lifecycle Manager as `LifecycleState.REGISTERED`.
- ✓ **No plans registered at bootstrap** — confirmed via `test_bootstrap_planner_has_no_plans_initially` (unlike Capability Registry/Plugin Manager, the Planner has nothing to pre-populate; "Behavior of existing packages must remain unchanged" holds trivially since Planner starts empty).
- ✓ **Capability Registry integration** — confirmed via `test_bootstrap_planner_validates_plan_against_capability_registry`, validating a Plan referencing a real capability id already registered by the Capability Registry's own Package 013 population step.
- ✓ **Event Bus integration** — all three new planning events verified published at the correct points, in order, only on success, via `tests/test_planner.py`.
- ✓ **Naming consistency** — `"planner"` verified against the repository's own `CORE_SERVICE_NAMES` convention before implementation.
- ✓ **No plugin awareness** — confirmed via source inspection: `argus/planner/` contains no import of `argus.plugins` anywhere.
- ✓ **No dispatch/execution capability** — confirmed via source inspection: `argus/planner/` contains no import of `argus.dispatcher` or `argus.workflow` anywhere.
- ✓ **Regression suite passes** — `python -m unittest discover -s tests` reports `Ran 759 tests ... OK`; `python -m pytest` reports `847 passed, 38 subtests passed`.
- ✓ **`python main.py` starts cleanly** — exit code 0.
- ✓ **`pyflakes` clean** — no warnings on any new/modified module.
- ✓ **No unintended repository modifications** — confirmed via `git status`/`git diff --stat`; only the files listed in Section 5 were touched.
- ✓ **`CORE_SERVICES_VERSION` not modified** — confirmed still `"0.1.4"`.
- ✓ **No commit created** — confirmed via `git log` (HEAD unchanged at `5fb57f1`).
- ✓ **No tag created** — confirmed via `git tag -l` (unchanged: `v0.1.1`-`v0.1.4`).
- ✓ **Repository ready for integration and release** — all regression, smoke, and pyflakes checks pass locally; final integration, version bump, commit, and tag remain the Founder's responsibility.

## 13. Concise Implementation Summary

Package 015 adds `argus/planner/`: `PlanStatus`/`Plan` (an immutable Execution Plan snapshot), `PlanStep` (an immutable, ordered unit of work referencing a required capability id), `IPlanner` (a plain ABC, deliberately not an `IService`), and `Planner`, a pure reasoning-only registry with replace-not-mutate semantics, automatic `order` recomputation, automatic status-reset-on-mutation, and `PlanCreated`/`PlanUpdated`/`PlanValidated` event publication. `bootstrap.py` registers `Planner` as ArgusOS's 15th core service, constructed last since it depends on a live Capability Registry reference for `validate_plan()`'s one read-only `contains()` check. `argus/dispatcher/`, `argus/capability/`, `argus/workflow/`, and `argus/plugins/` are all untouched. `Planner` is the third consecutive new non-`IService`-adopter data point for ADR-0002, explicitly checked against its most substantial method (`validate_plan()`) and still found not to qualify. 759 tests pass in `tests/` (`python -m pytest` also passes: 847 passed, 38 subtests), 100% coverage across all Package 015 modules. Built and verified entirely within the Founder-supplied repository; no commit, tag, push, or git-history change was made, and `CORE_SERVICES_VERSION` was not advanced, per instruction.

## 14. Architectural Observations

- This is the third consecutive package (013, 014, 015) whose core service deliberately does not adopt `IService`, and the first where that non-adoption was explicitly checked against a method doing genuinely non-trivial work (`validate_plan()`'s registry lookup plus status transition) rather than a purely trivial CRUD operation - strengthening ADR-0002's criterion as something that discriminates on *behavior*, not on how much a method superficially "does."
- The Planner is the first package since Capability Registry (013) to add a genuinely new upstream position in the target architecture diagram rather than a downstream one - Packages 013 and 014 both inserted layers between existing pipeline stages, while Planner sits above the pipeline's existing entry point (Intent). This confirms the diagram-position-versus-construction-order distinction generalizes in both directions (a layer below its dependents and a layer conceptually above its dependencies both still construct in dependency order), not just for the one specific case Package 013 first encountered.
- The "currently-unowned architectural gap" flagged in Packages 011 through 014's own reports - nothing yet takes a raw user message all the way through classification, planning, capability resolution, plugin-aware execution, and response generation automatically - remains open after this package, now with one more explicit seam (Intent -> Plan) added to the chain that a future integration package will need to close.
- `Plan`/`PlanStep`'s replace-not-mutate, recompute-derived-fields pattern (`order` always matching tuple position) is a slightly stricter application of the same immutable-value-object discipline used everywhere else in this codebase (`Workflow`/`WorkflowStep`, `Capability`, `Plugin`) - worth noting as the first package where a derived field's consistency is actively enforced by the owning service on every mutation, rather than merely being possible to keep consistent by convention.
