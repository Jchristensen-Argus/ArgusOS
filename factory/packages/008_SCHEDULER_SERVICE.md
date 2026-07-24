# Implementation Package 008 - Scheduler Service

## Objective

Build ArgusOS's time-orchestration service: deterministic, tick-driven
scheduling and execution of deferred and recurring tasks, per
design/specifications/SCHEDULER.md and the Founder's Package 008 work order.

---

## Scope Reduction Relative to design/specifications/SCHEDULER.md

design/specifications/SCHEDULER.md lists "Navigator" as a Required
Dependency ("Execute Tasks... Trigger workflows"). Navigator does not exist
yet (see factory/packages/007_MEMORY_SERVICE.md's dependency-graph audit).
This package does not invent Navigator or its contract. Instead, a
ScheduledTask's `callback` is a plain Python callable in this version;
Scheduler invokes it directly. Routing execution through Navigator instead
of a bare callback is deferred until Navigator is specified and built - a
future package's responsibility, not this one's.

The specification also lists cron scheduling, time-zone awareness, and
missed-schedule recovery/catch-up under Future Enhancements. All three are
explicitly out of scope here, per the Founder's work order ("Do NOT
implement cron support yet... Do not introduce speculative features").

---

## IService Adoption

IScheduler inherits IService. This is not a new architectural decision -
IService's own docstring (Package 005) names Scheduler as an anticipated
future adopter - but it is the *first* real one. Per ADR-0002
(design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md), Scheduler was
identified as the strongest candidate for genuine IService adoption, since
start()/stop() can gate whether tick() is permitted to execute tasks at
all - real, distinct behavior at each phase, even without a background
thread.

Scheduler tracks its own internal LifecycleState to satisfy
IService.status(). This is deliberately NOT synchronized with whatever a
LifecycleManager tracks for the same registered name; per the Founder's
standing instruction, ADR-0002 remains Proposed and IService is left
unchanged for this package. Scheduler is Package 008's empirical test of
whether the predicted duplicate-state risk is real. It is - see
IMPLEMENTATION_REPORT.md's ADR Recommendation section for the confirmed
finding and the recommended next step.

---

## Specifications Referenced

- design/specifications/SCHEDULER.md
- design/specifications/INTERFACES.md
- design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md
- factory/packages/005_SERVICE_LIFECYCLE.md (IService, LifecycleManager)
- factory/packages/006_KNOWLEDGE_SERVICE.md,
  factory/packages/007_MEMORY_SERVICE.md (precedent patterns)
- factory/standards/CODING_STANDARD.md

---

## Files to Create

argus/scheduler/
    __init__.py
    interfaces.py
    scheduler.py
    task.py
    triggers.py
    exceptions.py

tests/
    test_scheduler.py
    test_scheduler_task.py
    test_triggers.py

---

## Files to Modify

- argus/bootstrap.py (construct and register Scheduler as the eighth core
  service; bump CORE_SERVICES_VERSION to "0.0.8")
- argus/events/event_types.py (add TASK_SCHEDULED, TASK_STARTED,
  TASK_COMPLETED, TASK_FAILED, TASK_CANCELLED, TASK_PAUSED, TASK_RESUMED;
  reuse the existing, previously-unused SCHEDULER_TICK as a per-tick
  heartbeat)
- tests/test_bootstrap.py (extend core-service assertions to eight services)
- CHANGELOG.md, DEVLOG.md

ARCHITECTURE.md is not modified by this package: IScheduler inheriting
IService was already anticipated by IService's own Package 005 docstring,
not a new architectural change. (See IMPLEMENTATION_REPORT.md for a
separate, flagged finding about two conflicting ARCHITECTURE.md-adjacent
documents already present in the repository, unrelated to this package.)

---

## Acceptance Criteria

- `python main.py` starts and shuts down cleanly.
- All pre-existing tests continue to pass.
- Scheduler resolves from the Container and appears in the Service
  Registry and Lifecycle Manager (LifecycleState.REGISTERED), alongside
  the seven existing core services - registered only, not started, per
  the pattern established for every core service to date.
- schedule / cancel / pause / resume / get_task / list_tasks / tick all
  behave per this document and the Founder's work order.
- tick() only executes tasks while the Scheduler's own IService state is
  RUNNING; otherwise it raises SchedulerError.
- Every operation publishes its corresponding event; tick() additionally
  publishes SCHEDULER_TICK once per call.
- OneShotTrigger, IntervalTrigger, and DailyTrigger each behave
  deterministically given an explicit `now`, with no reliance on real
  time or sleeping, in both the implementation and its tests.

---

## Out of Scope

- Cron expression support.
- Time-zone conversion (DailyTrigger operates on whatever `now` is
  expressed in; ArgusOS uses UTC throughout).
- Missed-schedule recovery/catch-up.
- Background threads, timers, or automatic ticking.
- Retry/backoff logic for failed callbacks.
- Any direct or indirect dependency on argus.memory.
- Navigator integration (see Scope Reduction above).
- Resolving the IService `status()` duplication question itself - this
  package's role is to confirm or refute the concern empirically, per the
  Founder's standing instruction, not to revise IService.
