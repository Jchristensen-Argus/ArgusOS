# Implementation Package 010 - Workflow Engine

## Objective

Give ArgusOS deterministic, multi-step orchestration: a way to
register a named sequence of steps as a Workflow and execute it
strictly in order, per the Founder's Package 010 work order.

---

## Specification Note

No `design/specifications/WORKFLOW.md` exists in the repository -
the same situation as Package 002 (Bootstrap) and Package 009 (Intent
Router). This package is built directly from the Founder's explicit
work order; no architecture was invented to fill the gap.

---

## Constraints (Explicit, Non-Negotiable)

- Not an AI planner, not an LLM - deterministic orchestration only.
- No threading, no background execution, no retries, no persistence,
  no external libraries.
- The engine never directly invokes another core service. A step's
  `action` is a plain, opaque callable (`StepAction`); the engine
  invokes it without knowing or caring what it does. If a workflow
  needs to touch Knowledge/Memory/Scheduler/IntentRouter, that
  happens inside the step's action (constructed by whoever builds the
  WorkflowStep, e.g. via the Container) - never inside
  `argus/workflow/engine.py` itself.

---

## IService Adoption

`IWorkflowEngine` inherits `IService`, per the Founder's explicit
instruction. Unlike IntentRouter (Package 009), `execute()` **is**
gated on the engine's own lifecycle state: it raises `WorkflowError`
unless `WorkflowEngine`'s self-tracked state is `RUNNING`. This
mirrors `Scheduler.tick()` (Package 008) exactly, and is a deliberate
architectural choice, not an oversight - running a workflow's steps is
precisely the kind of "active work" `IService.start()`/`stop()`'s own
docstring describes gating, unlike IntentRouter's stateless
`parse()`/`route()`. `register_workflow()`, `cancel()`, and
`get_workflow()` remain ungated registry operations, matching
Scheduler's own `schedule`/`cancel`/`pause`/`resume` precedent.

This is a third empirical data point for ADR-0002
(design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md): it reinforces
Scheduler's finding (IService can carry genuine behavior) rather than
IntentRouter's (IService adopted with no behavioral gate). ADR-0002 is
updated with this finding; its Status remains `Proposed`, per standing
instruction.

---

## Specifications Referenced

- factory/packages/005_SERVICE_LIFECYCLE.md (`IService`, `LifecycleManager`)
- factory/packages/008_SCHEDULER_SERVICE.md (nearest precedent: an
  `IService`-inheriting core service with a genuine behavioral gate)
- factory/packages/009_INTENT_ROUTER.md (nearest precedent: an
  `IService`-inheriting core service, and the Event-Bus-only
  invocation discipline)
- design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md
- design/specifications/INTERFACES.md
- factory/standards/CODING_STANDARD.md

---

## Files to Create

argus/workflow/
    __init__.py
    interfaces.py
    workflow.py
    engine.py
    state.py
    exceptions.py

tests/
    test_workflow.py
    test_workflow_engine.py

---

## Files to Modify

- argus/bootstrap.py (construct and register `WorkflowEngine` as the
  tenth core service; bump `CORE_SERVICES_VERSION` to `"0.0.10"`)
- argus/events/event_types.py (add `WORKFLOW_STARTED`,
  `WORKFLOW_STEP_STARTED`, `WORKFLOW_STEP_COMPLETED`,
  `WORKFLOW_COMPLETED`, `WORKFLOW_FAILED`, `WORKFLOW_CANCELLED`)
- tests/test_bootstrap.py (extend core-service assertions to ten
  services)
- CHANGELOG.md, DEVLOG.md, IMPLEMENTATION_REPORT.md,
  design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md

`design/ARCHITECTURE.md` is not modified by this package:
`IWorkflowEngine` inheriting `IService` is not a new architectural
decision (Scheduler already established the gated-IService pattern in
Package 008).

---

## Acceptance Criteria

- `python main.py` starts and shuts down cleanly.
- All pre-existing canonical tests continue to pass.
- `WorkflowEngine` resolves from the Container and appears in the
  Service Registry and Lifecycle Manager (`LifecycleState.REGISTERED`),
  alongside the nine existing core services - registered only, not
  started.
- `register_workflow` / `execute` / `cancel` / `get_workflow` /
  `status` behave per this document and the Founder's work order.
- `execute()` only runs a workflow's steps while the engine's own
  `IService` state is `RUNNING`, and only if the workflow itself is
  `PENDING`; otherwise it raises `WorkflowError`.
- Steps execute strictly in registration order; context returned by
  one step is passed as the input to the next.
- A failing step publishes `WorkflowFailed`, marks the workflow
  `FAILED`, and stops execution - remaining steps do not run, and the
  exception does not propagate out of `execute()`.
- `WorkflowStarted`/`WorkflowStepStarted`/`WorkflowStepCompleted`/
  `WorkflowCompleted`/`WorkflowFailed`/`WorkflowCancelled` are each
  published at the correct point, per `engine.py`'s docstrings.
- The engine never imports `argus.knowledge`, `argus.memory`,
  `argus.scheduler`, or `argus.intent`.

---

## Out of Scope

- Any AI/ML-based planning or step generation.
- Threading, background execution, or automatic scheduling of
  workflow execution.
- Retry/backoff logic for failing steps.
- Persistence of workflows across process restarts.
- Parallel or conditional/branching step execution (steps run
  strictly sequentially, unconditionally).
- Direct invocation of any named service (Knowledge, Memory,
  Scheduler, IntentRouter) from the engine itself.
- Resolving the `IService` duplication question itself - this
  package adds a third empirical data point, per the Founder's
  standing instruction, not a resolution.
