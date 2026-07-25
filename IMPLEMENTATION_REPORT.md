# ArgusOS Implementation Report — Package 016: Agent Runtime

## 1. Package Overview

Package 016 adds `argus/runtime/`, the only component in ArgusOS permitted to execute a validated Plan. `AgentRuntime` dispatches a Plan's `PlanStep`s sequentially, in order, through the existing, unmodified `IIntentDispatcher.dispatch()` - never a plugin, workflow, or service directly, and never by creating, validating, or reordering Plans (all Planner's responsibility). `Execution` is an immutable value object recording one run of one Plan: identity, status, progress (`current_step`), collected step results, and timing. `start_execution()`/`resume_execution()` are gated on the Runtime's own `IService` lifecycle state being `RUNNING`; `pause_execution()`/`cancel_execution()`/`get_execution()`/`list_executions()` remain ungated registry-style operations - the Runtime's first genuine `IService` adoption after three consecutive non-adopting packages (013, 014, 015). Because `IIntentDispatcher.dispatch()` resolves a Capability purely by `IntentType`, with no capability-id-specific entry point, and this package's Constraints forbid modifying Dispatcher's contract, the Runtime constructs a synthetic `Intent` per step (reusing the Plan's own originating `IntentType`) and passes each step's real `required_capability` id through `dispatch()`'s `context` parameter for traceability only - a documented, load-bearing Version 1 limitation, not an oversight. `AgentRuntime` is registered as ArgusOS's 16th core service, constructed immediately after the Planner. All 759 pre-existing canonical tests still pass unchanged; 831 tests total pass under `python -m unittest discover -s tests`, and `python -m pytest` also passes (919 passed, 38 subtests passed). `python main.py` starts and shuts down cleanly.

## 2. Repository Verification Note

Before writing any code, the uploaded repository ("ArgusOS (15).zip") was verified fresh against this package's own general pre-flight instruction ("verify repository state, verify version consistency, run smoke validation") - this work order did not specify the fixed, numbered checklist Packages 013-015's did.

**A genuine process variation was found and is worth recording plainly.** HEAD (`1230851`, "Implement Package 015 Planner") is exactly the commit tag `v0.1.5` points to - unlike the five prior packages, no separate "Synchronize repository version" commit sits on top of the tagged commit this time. Instead, the working tree contained one **uncommitted** modification to `argus/bootstrap.py`: `CORE_SERVICES_VERSION` already read `"0.1.5"` in the file itself, but `git diff` showed this as an unstaged, uncommitted 1-insertion/1-deletion change against HEAD (which still has `"0.1.4"` committed). This is a different shape of the same underlying fact pattern seen before Packages 012/013 (a version constant needing to catch up to a release) - except this time the correction was already applied to the working tree, just not yet committed, rather than needing a fresh corrected upload.

This was evaluated against the actual substance of what pre-flight verification protects, not the literal shape of prior packages' git history: the working tree's real, effective state - the state Package 016's code would actually be built on top of - had the correct `CORE_SERVICES_VERSION` value matching the latest tag, and every other substantive check passed cleanly: Package 015 (`argus/planner/`) present; `python -m pytest` passing (847 passed, 38 subtests); `python -m unittest discover -s tests` passing (759); `python main.py` starting and shutting down cleanly (exit 0). Proceeding was judged correct - this is reported here transparently rather than either silently ignored or treated as a blocking failure it substantively is not.

Per the Founder's explicit release rules, this implementation was built, tested, and verified entirely within the supplied repository. No `git commit`, `git tag`, push, or git-history modification of any kind was performed, `CORE_SERVICES_VERSION` was not changed by this package, and this package is not being reported as complete — final validation, integration, release, tagging, and git operations are the Founder's responsibility, to be performed against the live repository after independent regression testing.

## 3. Architectural Rationale

No `design/specifications/AGENT_RUNTIME.md` exists — the same situation as Packages 002, 009-015. Every structural decision traces to the Founder's explicit work order. The full rationale for each decision below is also recorded in `factory/packages/016_AGENT_RUNTIME.md`'s "Architectural Decisions" section, in the source code's own module docstrings, and is only summarized here.

**Decision 1 — `start_execution()` runs synchronously; pause/cancel are only reachable via a reentrant call.** Given "No concurrent execution," there is no background thread to drive step dispatch independently of the calling stack. The step loop checks its Execution's stored status at the top of every iteration; the only way that status can change mid-loop is a dispatched step's own action calling back into `pause_execution()`/`cancel_execution()` before its `dispatch()` call returns - single-threaded, but genuinely reentrant, and the mechanism this package's own required pause/resume tests exercise.

**Decision 2 — synthetic-Intent dispatch, with a documented resulting limitation.** `IIntentDispatcher.dispatch()` accepts only an `Intent`, resolving purely by `IntentType`; `PlanStep.required_capability` (a specific id) cannot be honored without modifying Dispatcher, which this package forbids. The Runtime reuses the Plan's own `originating_intent.name` for every step's synthetic Intent, passing `required_capability` through `context` for traceability only - meaning every step of a Plan currently resolves to the same Capability in Version 1, regardless of its own `required_capability` value.

**Decision 3 — no dedicated event for pause/resume/cancel.** This package's Events section names exactly six event types; none correspond to these three operations. No new event types were invented to fill that gap - state changes are observable via `get_execution()`/`list_executions()` instead.

**Decision 4 — `start_execution()` re-fetches the Planner's canonical Plan and requires VALIDATED status.** Rather than trusting a possibly-stale passed-in `Plan`, `start_execution()` calls `IPlanner.get_plan(plan.id)` (read-only, never `validate_plan()`) and executes the canonical record's own steps, giving real functional meaning to this package's "Runtime depends on Planner" bootstrap requirement.

**Decision 5 — `Execution.id`, not `execution_id`, for the model's own identity.** Follows the established `id`-for-self-identity / `<noun>_id`-for-references convention already set by `Capability`, `Plugin`, `Plan`, and `PlanStep`, per "Follow repository conventions established in previous packages."

**Decision 6 — `PlanStep.optional` has no effect on execution.** This package's Failure Rules are stated unconditionally ("If a step fails... stop execution immediately"); no exception for optional steps is specified, so none was added.

## 4. IService Adoption — Breaking the Three-Consecutive-Non-Adopter Streak

`IAgentRuntime` DOES inherit `IService` — `start_execution()`/`resume_execution()` are genuinely gated on the Runtime's own `RUNNING` state, architecturally identical to `WorkflowEngine.execute()` (010), `ConversationManager.receive()` (011), and `IntentDispatcher.dispatch()` (012). `pause_execution()`/`cancel_execution()`/`get_execution()`/`list_executions()` remain ungated, matching `Scheduler.pause()`/`resume()`'s (008) precedent for per-item operations unaffected by the owning service's own lifecycle. This is the sixth `IService` adopter overall and the fifth genuinely gated one, breaking the three-consecutive-non-adopter streak set by Capability Registry (013), Plugin Manager (014), and Planner (015) - appended to `design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md` as clear evidence the criterion discriminates correctly in both directions. Its Status remains `Proposed`, per standing instruction.

## 5. Directory Tree (files touched)

```
argus/
    runtime/
        __init__.py                        (new)
        execution.py                       (new)
        runtime.py                         (new)
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
        016_AGENT_RUNTIME.md                (new)
    ROADMAP.md                              (modified)
tests/
    test_bootstrap.py                       (modified)
    test_execution.py                       (new)
    test_runtime.py                         (new)
argus/tests/test_bootstrap.py               (modified — CORE_SERVICE_NAMES tuple only, per explicit instruction)
CHANGELOG.md                                (modified)
DEVLOG.md                                   (modified)
IMPLEMENTATION_REPORT.md                    (replaced — this file)
```

No file outside this list was created, deleted, moved, or modified. `argus/dispatcher/`, `argus/capability/`, `argus/workflow/`, `argus/plugins/`, `argus/planner/`, `argus/lifecycle/test_lifecycle.py`, `argus/CHANGELOG.md`, `argus/DEVLOG.md`, `argus/IMPLEMENTATION_REPORT.md`, `argus/factory/`, and every legacy pre-Factory file were left completely untouched.

## 6. Integration Notes

- `AgentRuntime(event_bus, dispatcher, planner)` — constructed in `bootstrap.py` immediately after the Planner, depending on the Event Bus, the Intent Dispatcher, and the Planner.
- This is now the 16th core service constructed in the bootstrap sequence.
- Registered in the Container (`"agent_runtime"`), in the Service Registry as a `ServiceDescriptor` (version `"0.1.5"`, the repository's currently released version — see Section 2), and in the Lifecycle Manager as `LifecycleState.REGISTERED` — matching the treatment of all fifteen prior core services. Unlike Capability Registry/Plugin Manager/Planner, `AgentRuntime`'s own `initialize()`/`start()` are NOT called by bootstrap either, for the same divergence-avoidance reasoning already applied to every other `IService` adopter.
- `argus/events/event_types.py` extended with six new members: `EXECUTION_CREATED`, `EXECUTION_STARTED`, `STEP_STARTED`, `STEP_COMPLETED`, `EXECUTION_COMPLETED`, `EXECUTION_FAILED`.
- Naming (`"agent_runtime"`) verified against the repository's own `tests/test_bootstrap.py::CORE_SERVICE_NAMES` convention before implementation.
- The repository's pre-existing, known stray duplicate `argus/tests/test_bootstrap.py` had its `CORE_SERVICE_NAMES` tuple synchronized with `"agent_runtime"` added, per the standing Repository Rule introduced in Package 011 — and only that tuple.
- Source-inspection confirms `argus/runtime/runtime.py` contains no `import argus.workflow` or `import argus.plugins` statement anywhere - its only cross-package imports beyond `argus.runtime` itself are `argus.dispatcher.interfaces.IIntentDispatcher`, `argus.planner.interfaces.IPlanner`/`argus.planner.plan.Plan`/`argus.planner.exceptions`, `argus.intent.intent.Intent`, `argus.events`, and `argus.lifecycle.lifecycle.LifecycleState` - all pre-existing, unmodified public interfaces.

## 7. Test Results

Canonical suite (`tests/`):
```
python -m unittest discover -s tests
Ran 831 tests in 0.073s
OK
```

Per this package's explicit testing instruction:
```
python -m pytest
919 passed, 38 subtests passed in 0.58s
```

The synchronized duplicate `argus/tests/` also verified passing standalone (unaffected by the one-line sync):
```
python -m unittest discover -s argus/tests -p "test_*.py"
Ran 64 tests in 0.014s
OK
```

`pyflakes` on every new/modified module: clean, no warnings.

`python main.py`:
```
2026-07-25 16:37:49 [INFO] argus: ArgusOS application started.
2026-07-25 16:37:49 [INFO] argus: ArgusOS application shutting down.
```
Exit code 0.

## 8. Coverage Summary

Measured with `coverage.py`, `python -m coverage run -m pytest`:

| Module | Stmts | Miss | Cover |
|---|---|---|---|
| `argus/bootstrap.py` | 68 | 0 | 100% |
| `argus/events/event_types.py` | 63 | 0 | 100% |
| `argus/runtime/__init__.py` | 5 | 0 | 100% |
| `argus/runtime/exceptions.py` | 5 | 0 | 100% |
| `argus/runtime/execution.py` | 26 | 0 | 100% |
| `argus/runtime/interfaces.py` | 18 | 0 | 100% |
| `argus/runtime/runtime.py` | 125 | 0 | 100% |

Package 016 total (all `argus/runtime/*` plus touched `argus/bootstrap.py`/`argus/events/event_types.py`): 310 statements, 100% covered — no accepted gaps. Full `argus/*` coverage: 99% (unchanged from Package 015; remaining gaps are pre-existing and out of scope).

## 9. Engineering Decisions / Deviations from the Work Order

- **`start_execution()` runs the entire step loop synchronously**, with `pause_execution()`/`cancel_execution()` only reachable via a reentrant call from within a dispatched step's own action - the only physically coherent design given "No concurrent execution." See Section 3, Decision 1.
- **A synthetic Intent, not a capability-id-aware dispatch call, drives every step's execution** - `IIntentDispatcher.dispatch()`'s contract cannot be modified, and has no other entry point for a specific capability id. See Section 3, Decision 2, and Section 10's first Known Limitation.
- **No `PLAN_REMOVED`-style extra events were invented for pause/resume/cancel** - exactly the six named event types were added. See Section 3, Decision 3.
- **`start_execution()` re-fetches and trusts only the Planner's own canonical Plan record**, not the possibly-stale object a caller passes in. See Section 3, Decision 4.
- **`Execution.id` (not `execution_id`) is the model's own field name**, following established repository convention over the work order's literal suggestion. See Section 3, Decision 5.
- **`PlanStep.optional` is not consulted during execution** - Failure Rules are unconditional. See Section 3, Decision 6.
- **`IAgentRuntime` DOES inherit `IService`** - a deliberate, ADR-0002-driven choice, breaking three consecutive packages' non-adoption. See Section 4.
- **`CORE_SERVICES_VERSION` remains `"0.1.5"`, unchanged by this package.** Per the Founder's standing policy and this package's own explicit Version Policy.
- **`argus/tests/test_bootstrap.py` (duplicate tree) synchronized, tuple-only**, per the standing Repository Rule introduced in Package 011.

## 10. Known Limitations

- **Per-step capability targeting is not honored by Dispatcher resolution** - every step of a Plan resolves to whatever Capability the Dispatcher selects for the Plan's originating `IntentType`, regardless of each step's own `required_capability` id. See Section 3, Decision 2. A future package must extend `IIntentDispatcher` (outside this package's own bounds) to close this gap.
- `PlanStep.optional` has no effect on execution outcomes.
- No persistence — Executions are held only in memory.
- No concurrency, no retries, no rollback — explicit Version 1 constraints.
- `pause_execution()`/`cancel_execution()` are only reachable on a `RUNNING` Execution via a reentrant call from within a dispatched step's own action - fully functional and tested, but not an out-of-band "pause from another thread" mechanism, which is out of Version 1 scope by construction.
- The repository's stray `argus/` duplicate tree (beyond the one explicitly-required `test_bootstrap.py` sync) and legacy pre-Factory files remain unresolved, out of scope per the Founder's explicit repository rules.

## 11. Repository-Derived Package Metrics (measured, not estimated)

Measured via `git diff --stat`/`--numstat` against the working tree's unmodified base commit `1230851` (no commit was made — see Section 2; the pre-existing uncommitted `CORE_SERVICES_VERSION` edit is part of that same unmodified base and is excluded from this package's own measured diff):

- Files Created: 8 (5 `argus/runtime/*.py`, `factory/packages/016_AGENT_RUNTIME.md`, 2 new test files)
- Files Modified: 9 (`argus/bootstrap.py`, `argus/events/event_types.py`, `design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`, `factory/ROADMAP.md`, `tests/test_bootstrap.py`, `argus/tests/test_bootstrap.py`, `CHANGELOG.md`, `DEVLOG.md`, `IMPLEMENTATION_REPORT.md`)
- Lines Added: 2,227 / Lines Removed: 112 (measured via `git diff --stat` across all 17 touched files, including this report's own replacement)
- Unit Tests: 831 passing in canonical `tests/` (net +72 vs. Package 015's 759: +22 `test_execution.py`, +47 `test_runtime.py`, +3 `test_bootstrap.py` [23->26])
- Coverage: 100% (Package 016 modules), 99% (full `argus/*`)
- Public Classes: 2 (`Execution`, `AgentRuntime`)
- Public Interfaces: 1 (`IAgentRuntime`)
- New Dependencies: 0
- External Libraries: 0 (standard library only)
- Architecture Deviations: 0 (see Section 9 for documented, non-architectural deviations)

## 12. Pre-Completion Checklist (per the Founder's explicit checklist)

- ✓ **Bootstrap registration** — `AgentRuntime(...)` constructed in `bootstrap.py`, registered in the Container as `"agent_runtime"`. Confirmed via `test_bootstrap_registers_agent_runtime_in_container`.
- ✓ **Service registration** — recorded as a `ServiceDescriptor` (version `"0.1.5"`) alongside all fifteen prior core services.
- ✓ **Lifecycle integration** — registered in the Lifecycle Manager as `LifecycleState.REGISTERED`, not started. Confirmed via `test_bootstrap_agent_runtime_is_not_started`.
- ✓ **Planner integration** — confirmed via `test_bootstrap_agent_runtime_executes_validated_plan_end_to_end`, running a real Planner-validated Plan through the real Intent Dispatcher.
- ✓ **Dispatcher-only execution** — confirmed via source inspection: `argus/runtime/runtime.py` contains no import of `argus.workflow` or `argus.plugins` anywhere; every dispatched effect goes through `IIntentDispatcher.dispatch()`.
- ✓ **No Plan mutation** — confirmed via source inspection: `argus/runtime/runtime.py` never calls `create_plan()`, `add_step()`, `remove_step()`, `reorder_steps()`, or `validate_plan()` on the injected `IPlanner` - only `get_plan()`.
- ✓ **Event Bus integration** — all six new execution events verified published at the correct points, in order, via `tests/test_runtime.py`.
- ✓ **Naming consistency** — `"agent_runtime"` verified against the repository's own `CORE_SERVICE_NAMES` convention before implementation.
- ✓ **Regression suite passes** — `python -m unittest discover -s tests` reports `Ran 831 tests ... OK`; `python -m pytest` reports `919 passed, 38 subtests passed`.
- ✓ **`python main.py` starts cleanly** — exit code 0.
- ✓ **`pyflakes` clean** — no warnings on any new/modified module.
- ✓ **No unintended repository modifications** — confirmed via `git status`/`git diff --stat`; only the files listed in Section 5 were touched.
- ✓ **`CORE_SERVICES_VERSION` not modified** — confirmed still `"0.1.5"`.
- ✓ **No commit created** — confirmed via `git log` (HEAD unchanged at `1230851`).
- ✓ **No tag created** — confirmed via `git tag -l` (unchanged: `v0.1.1`-`v0.1.5`).
- ✓ **Repository ready for architectural review** — all regression, smoke, and pyflakes checks pass locally; final integration, version bump, commit, and tag remain the Founder's responsibility.

## 13. Concise Implementation Summary

Package 016 adds `argus/runtime/`: `ExecutionStatus`/`Execution` (an immutable record of one run of one Plan), `IAgentRuntime(IService)`, and `AgentRuntime`, the sole component permitted to execute a validated Plan by dispatching its steps sequentially through the existing `IIntentDispatcher`. `start_execution()`/`resume_execution()` are gated on the Runtime's own `RUNNING` state - the sixth `IService` adopter and fifth genuinely gated one, breaking a three-package non-adoption streak. Pause/resume are implemented via a reentrant-call mechanism, the only design coherent with this package's "no concurrency" constraint. A synthetic per-step Intent (reusing the Plan's originating `IntentType`) drives every `dispatch()` call, since Dispatcher's contract cannot be modified to accept a specific capability id - a documented Version 1 limitation. `argus/dispatcher/`, `argus/capability/`, `argus/workflow/`, `argus/plugins/`, and `argus/planner/` are all untouched. 831 tests pass in `tests/` (`python -m pytest` also passes: 919 passed, 38 subtests), 100% coverage across all Package 016 modules. Built and verified entirely within the Founder-supplied repository; no commit, tag, push, or git-history change was made, and `CORE_SERVICES_VERSION` was not advanced, per instruction.

## 14. Architectural Observations

- This package's reentrant pause/cancel mechanism is a new pattern for this codebase - every prior "stop something mid-operation" precedent (`WorkflowEngine.cancel()`, `Scheduler.cancel()`) operates on work that has not yet started, not on work already in progress within the same call stack. Worth flagging as a genuinely new technique, not a repetition of an existing one, introduced specifically because "no concurrency" made every other approach to interruptible synchronous execution unavailable.
- `AgentRuntime` is the first package since Package 012 (Intent Dispatcher) to reintroduce a genuine `IService` adopter after a run of non-adopters, giving ADR-0002 its first "the streak breaks, and it breaks for a clear, principled reason" data point rather than a steadily lengthening one-directional trend - useful evidence that the criterion is a real filter, not a default answer that happens to always come out the same way once a run of similar packages establishes momentum.
- The synthetic-Intent limitation (Decision 2) is the most consequential open architectural question this package leaves behind, more so than any of Packages 011-015's own flagged gaps: it means multi-capability Plans do not yet behave as their own step-level metadata implies, which will need deliberate resolution (extending `IIntentDispatcher`, out of bounds for this package) before Plans with heterogeneous steps can be relied upon in practice - worth prioritizing explicitly for whichever future package is scoped to touch the Dispatcher's contract.
- The "currently-unowned architectural gap" flagged in Packages 011 through 015's own reports - nothing yet takes a raw user message all the way through classification, planning, and execution automatically - remains open after this package, though it is now one seam closer to closed: Planner produces validated Plans, and AgentRuntime can now execute them, but nothing yet wires a resolved Intent through both automatically.
