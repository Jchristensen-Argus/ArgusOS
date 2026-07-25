# ArgusOS Implementation Report — Package 010: Workflow Engine

## 1. Package Overview

Package 010 adds `argus/workflow/`, ArgusOS's first multi-step, deterministic orchestration layer. `Workflow` and `WorkflowStep` are immutable value objects; `WorkflowEngine` maintains an in-memory registry of workflows and executes a `PENDING` workflow's steps strictly in registration order, threading each step's returned context into the next. A failing step publishes `WorkflowFailed`, marks the workflow `FAILED`, and stops execution without the exception propagating out of `execute()`. `IWorkflowEngine` inherits `IService`; `execute()` is genuinely gated on the engine's own lifecycle state being `RUNNING` (mirroring `Scheduler.tick()`), while `register_workflow()`/`cancel()`/`get_workflow()` remain ungated registry operations. `WorkflowEngine` is registered as ArgusOS's tenth core service. All 353 pre-existing canonical tests still pass; 63 new tests were added (416 total in `tests/`), all passing under `python -m unittest discover -s tests`. No pytest anywhere in this package. `python main.py` starts and shuts down cleanly.

## 2. Repository Verification Note

This package was implemented against a repository the Founder explicitly designated as the only authoritative source, per the standing instruction to compare expectations against the uploaded repository before writing any code and to stop rather than guess if a discrepancy is found. An initial upload provided for this request was still at Package 008 (`bd30e29`, `CORE_SERVICES_VERSION == "0.0.8"`, no `argus/intent/`) despite the work order's premise that Package 009 was already released - this was caught by fresh extraction and direct inspection (not assumed from memory of prior sessions) and reported before any Package 010 code was written. A corrected upload was then provided and verified fresh: commit `6b2e298` ("Implement Package 009 Intent Router") on top of `bd30e29`, `argus/intent/` present, `CORE_SERVICES_VERSION == "0.0.9"`, 353 canonical tests passing. Every file that Package 009 touched was additionally diffed against the original Package 009 delivery and found byte-identical, confirming a clean, unmodified merge before Package 010 work began.

One incidental, out-of-scope observation from that verification, unrelated to Package 010: the repository's stray duplicate `argus/tests/test_bootstrap.py` (part of the pre-existing, untouched legacy/duplicate tree flagged during Package 009) picked up a 1-line addition (`"intent_router"` added to its own `CORE_SERVICE_NAMES`) sometime after Package 009's delivery. This package did not make that edit and does not touch that file; noted for the record only.

Per the Founder's mid-request instruction, this implementation was built, tested, and verified entirely within the supplied repository. No `git commit`, `git tag`, or push was performed, and this package is not being reported as released or complete - final validation, commit, tagging, and release are the Founder's responsibility against the live repository.

## 3. Architectural Rationale

No `design/specifications/WORKFLOW.md` exists in the repository - the same situation as Packages 002 and 009. Every structural decision below traces to an explicit line in the Founder's work order, not an invented architecture.

The central design tension, stated almost verbatim in the work order itself: "The Workflow Engine coordinates multiple Argus services to complete a workflow" versus "The Workflow Engine must never directly invoke unrelated services outside its defined interfaces." Resolved the same way Package 009 resolved Intent Router's analogous tension, but via a different mechanism suited to synchronous orchestration rather than event-driven reaction: a `WorkflowStep`'s `action` is an opaque, plain callable (`StepAction = Callable[[Mapping[str, Any]], Mapping[str, Any]]`) that `WorkflowEngine` invokes without any knowledge of what it does. `engine.py` never imports `argus.knowledge`, `argus.memory`, `argus.scheduler`, or `argus.intent` - verified structurally, not just by convention, via a test that inspects the module's own source for those import strings. Coordinating "multiple Argus services" happens *inside* a step's action - constructed by whoever builds the `WorkflowStep` (e.g. resolving a service from the Container) - never inside the engine.

## 4. IService Adoption — A Third Data Point for ADR-0002

`IWorkflowEngine` inherits `IService`, per the Founder's explicit instruction, making `WorkflowEngine` a third real adopter after Scheduler (Package 008) and IntentRouter (Package 009). This finding reinforces Scheduler's rather than IntentRouter's: `execute()` genuinely requires the engine's own `LifecycleState` to be `RUNNING`, raising `WorkflowError` otherwise - exactly mirroring `Scheduler.tick()`'s gating. `register_workflow()`, `cancel()`, and `get_workflow()` remain unaffected by lifecycle state, mirroring Scheduler's `schedule`/`cancel`/`pause`/`resume`.

Across all three adopters to date: two (Scheduler, WorkflowEngine) use `IService` for a genuine behavioral gate on their single "do the actual work" method; one (IntentRouter) adopts it with no behavioral gate, purely to satisfy an explicit interface requirement. This continues to support the criterion originally proposed in ADR-0002 ("adopt `IService` only when `start()`/`stop()` would do real, distinct work") as a good discriminator. This finding has been appended to ADR-0002 (`design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`); its Status remains `Proposed`, per standing instruction - this package adds evidence, it does not resolve the open question.

## 5. Directory Tree (files touched)

```
argus/
    workflow/
        __init__.py
        exceptions.py
        interfaces.py
        state.py
        workflow.py
        engine.py
    bootstrap.py                       (modified)
    events/
        event_types.py                 (modified)
design/
    decisions/
        0002_ISERVICE_ADOPTION_CRITERION.md   (modified — appended finding)
factory/
    packages/
        010_WORKFLOW_ENGINE.md         (new)
    ROADMAP.md                          (modified)
tests/
    test_bootstrap.py                   (modified)
    test_workflow.py                    (new)
    test_workflow_engine.py             (new)
CHANGELOG.md                            (modified)
DEVLOG.md                               (modified)
IMPLEMENTATION_REPORT.md                (replaced — this file)
```

No file outside this list was created, deleted, moved, or modified. `argus/tests/`, `argus/lifecycle/test_lifecycle.py`, `argus/CHANGELOG.md`, `argus/DEVLOG.md`, `argus/IMPLEMENTATION_REPORT.md`, `argus/factory/`, and every legacy pre-Factory file were left completely untouched, per the Founder's explicit repository rules.

## 6. Integration Notes

- `WorkflowEngine(event_bus: IEventBus)` — constructed in `bootstrap.py` immediately after the Intent Router, since it depends only on the Event Bus.
- Registered in the Container as `"workflow_engine"`, in the Service Registry as a `ServiceDescriptor` (version `"0.0.10"`), and in the Lifecycle Manager as `LifecycleState.REGISTERED` — matching the treatment of all nine prior core services. Not initialized or started by bootstrap; because `execute()` is genuinely gated (Section 4), a caller must call `engine.initialize()`/`start()` directly before `execute()` will do anything, exactly as Scheduler already requires for `tick()`.
- `argus/events/event_types.py` extended with six new members: `WORKFLOW_STARTED`, `WORKFLOW_STEP_STARTED`, `WORKFLOW_STEP_COMPLETED`, `WORKFLOW_COMPLETED`, `WORKFLOW_FAILED`, `WORKFLOW_CANCELLED`.
- Fully backward compatible: no existing public interface, method signature, or stored data format was changed. `CORE_SERVICES_VERSION` bumped `"0.0.9"` → `"0.0.10"`.
- Naming (`"workflow_engine"`) verified against the live repository's own `tests/test_bootstrap.py::CORE_SERVICE_NAMES` convention before implementation (`"scheduler"`, `"intent_router"` — no `_service` suffix on the three newest entries), not assumed.

## 7. Test Results

```
python -m unittest discover -s tests
Ran 416 tests in 0.037s
OK
```

`python main.py`:
```
2026-07-25 10:12:59 [INFO] argus: ArgusOS application started.
2026-07-25 10:12:59 [INFO] argus: ArgusOS application shutting down.
```
Exit code 0.

## 8. Coverage Summary

Measured with `coverage.py`, `python -m coverage run -m unittest discover -s tests`:

| Module | Stmts | Miss | Cover |
|---|---|---|---|
| `argus/bootstrap.py` | 46 | 0 | 100% |
| `argus/workflow/__init__.py` | 6 | 0 | 100% |
| `argus/workflow/engine.py` | 93 | 0 | 100% |
| `argus/workflow/exceptions.py` | 5 | 0 | 100% |
| `argus/workflow/interfaces.py` | 17 | 4 | 76% (lines 78, 105, 124, 135 — unreachable abstract-method stub bodies, same structural pattern as every other ABC in this codebase, e.g. `Trigger.next_fire_time`) |
| `argus/workflow/state.py` | 7 | 0 | 100% |
| `argus/workflow/workflow.py` | 24 | 0 | 100% |

Package 010 total (`argus/workflow/*`): 198 statements, 98% covered. Full `argus/*` coverage: 1,292 statements, 98% covered.

## 9. Engineering Decisions / Deviations from the Work Order

- **`get_workflow(workflow_id) -> Workflow` added beyond the four literally-named Required Methods.** The work order lists `register_workflow`/`execute`/`cancel`/`status` as required, but also lists "Status reporting" as an expected test-coverage area; `IService.status()` reports only the *engine's* lifecycle state, with no way to query an individual workflow's `WorkflowState` otherwise. Added as a minimal, necessary lookup method, mirroring the precedent of Scheduler's `get_task()`/`list_tasks()` (Package 008) — though Scheduler's work order named those explicitly, so this addition is flagged more prominently as a judgment call, not a literal requirement.
- **`execute()` genuinely gated on the engine's own `RUNNING` state; registry operations are not.** See Section 4.
- **A failing step's exception is caught and never propagates out of `execute()`.** `WorkflowExecutionError` is constructed to wrap the original exception (for a documented, catchable type and message) but is never raised to the caller — `execute()` returns the accumulated context normally, and the workflow's own state (via `get_workflow`) is how a caller learns of failure. This mirrors `TaskExecutionError`'s role in Scheduler's `tick()` exactly.
- **`cancel()` only succeeds against a `PENDING` workflow.** Because execution is fully synchronous with no threading, a workflow is never observably `RUNNING` to a caller outside of `execute()`'s own call stack — mid-execution cancellation is structurally impossible in this version, by design, per the work order's own "no threading, no background execution."
- **Exception base named `WorkflowError`**, matching the `<Subsystem>Error` convention (`SchedulerError`, `IntentError`).

## 10. Known Limitations

- Steps execute strictly sequentially with no parallelism, branching, or conditional logic.
- No retry/backoff for a failing step.
- Workflows are held only in memory; nothing persists across process restarts.
- A step's action has no declared input/output schema beyond "receives and returns a context mapping" — the engine validates only that it is callable.
- The repository's stray `argus/` duplicate tree and legacy pre-Factory files remain unresolved, out of scope for this package per the Founder's explicit repository rules (Section 2).

## 11. Repository-Derived Package Metrics (measured, not estimated)

Measured via `git diff --stat` against the working tree's unmodified base commit `6b2e298` (no commit was made — see Section 2):

- Files Created: 9 (6 `argus/workflow/*.py`, `factory/packages/010_WORKFLOW_ENGINE.md`, 2 new test files)
- Files Modified: 8 (`argus/bootstrap.py`, `argus/events/event_types.py`, `design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`, `factory/ROADMAP.md`, `tests/test_bootstrap.py`, `CHANGELOG.md`, `DEVLOG.md`, `IMPLEMENTATION_REPORT.md`)
- Lines Added: 1,611 / Lines Removed: 30
- Unit Tests: 416 passing in canonical `tests/` (63 new: 14 model + 48 engine + 1 bootstrap)
- Coverage: 98% (Package 010 modules), 98% (full `argus/*`)
- Public Classes: 3 (`Workflow`, `WorkflowStep`, `WorkflowEngine`) plus 1 Enum (`WorkflowState`)
- Public Interfaces: 1 (`IWorkflowEngine`)
- New Dependencies: 0
- External Libraries: 0 (standard library only)
- Architecture Deviations: 0 (the `get_workflow()` addition is documented in Section 9, not a deviation from architecture)

## 12. Pre-Completion Checklist (per the Founder's explicit checklist)

- ✓ **Bootstrap registration** — `WorkflowEngine(event_bus=event_bus)` constructed in `bootstrap.py`, registered in the Container as `"workflow_engine"`. Confirmed via `test_bootstrap_registers_workflow_engine_in_container`.
- ✓ **Service Registry registration** — recorded as a `ServiceDescriptor` (version `"0.0.10"`) alongside all nine prior core services. Confirmed via `test_bootstrap_registers_core_services_in_service_registry`.
- ✓ **Lifecycle registration** — registered in the Lifecycle Manager as `LifecycleState.REGISTERED`. Confirmed via `test_core_services_report_registered_lifecycle_state`.
- ✓ **Event Bus integration** — all six workflow events verified published at the correct points via `tests/test_workflow_engine.py`'s `ExecuteSuccessTests`, `ExecuteFailureTests`, and `CancelTests`.
- ✓ **Naming consistency** — `"workflow_engine"` verified against the repository's own `CORE_SERVICE_NAMES` convention before implementation, not assumed.
- ✓ **All regression tests passing** — `python -m unittest discover -s tests` reports `Ran 416 tests ... OK`.
- ✓ **`python main.py` starts cleanly** — exit code 0.
- ✓ **No legacy files modified** — confirmed via `git status`/`git diff --stat`; only the 15 files listed in Section 5 were touched.

## 13. Concise Implementation Summary

Package 010 adds `argus/workflow/`: an immutable `Workflow`/`WorkflowStep` model, a `WorkflowState` enum, and a `WorkflowEngine` that registers and sequentially executes deterministic, callable-based steps, threading context from one step to the next. `IWorkflowEngine` inherits `IService`, and unlike IntentRouter, `execute()` is genuinely gated on the engine's own `RUNNING` state — mirroring Scheduler and reinforcing that finding in ADR-0002 (kept `Proposed`, unchanged). A failing step publishes `WorkflowFailed`, marks the workflow `FAILED`, and stops without raising out of `execute()`. The engine never imports another core service directly, verified structurally by test. Registered as ArgusOS's tenth core service, `REGISTERED`-only. 416 tests pass in `tests/` (63 new), 98% coverage on `argus/workflow/`, `python main.py` starts and shuts down cleanly. Built and verified entirely within the Founder-supplied repository; no commit, tag, or push was performed, per instruction — final validation and release remain the Founder's responsibility.

## 14. Architectural Observations

- The `IService` adoption pattern is now well-established across three packages with a consistent, testable shape: gate the single "do real work" method, leave registry/query operations ungated. If ADR-0002's duplication concern is eventually resolved in a dedicated package, this consistent shape (not just the duplication mechanism itself) is worth preserving in whatever replaces or refines `IService`.
- `WorkflowStep`'s opaque-callable design is deliberately the same shape as `ScheduledTask.callback` (Package 008) and `IIntentRouter`'s registered handlers (Package 009): three separate packages have now independently arrived at "a plain callable is how ArgusOS core services accept caller-supplied behavior without creating an import dependency." This is worth naming as a de facto convention if a future architectural package formalizes cross-package standards.
- No workflow step in this package's own test suite invokes another core service (by design — the engine doesn't care), so end-to-end proof that a Workflow can actually coordinate Knowledge/Memory/Scheduler/IntentRouter in practice does not yet exist anywhere in the codebase. That would require a future package (or example) where a step's action is constructed with a resolved service from the Container — worth flagging since "coordinates multiple Argus services" is this package's stated mission but is only structurally possible today, not yet demonstrated.
