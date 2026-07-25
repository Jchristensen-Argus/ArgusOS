# Implementation Package 016 - Agent Runtime

## Objective

Give ArgusOS the only component permitted to execute a validated Plan.
Per the Founder's Package 016 work order:

```
Conversation -> Intent -> Planner -> Execution Plan -> Agent Runtime -> Dispatcher -> Action -> Plugin Manager -> Workflow -> Services
```

extending Package 015's:

```
Conversation -> Intent -> Planner -> Execution Plan
```

The Runtime owns execution only. It never creates or validates Plans
(Planner's job), never resolves or invokes a Capability directly
(Dispatcher's/Capability Registry's job), and never calls a plugin or
workflow directly (Plugin Manager's/WorkflowEngine's job) - all
execution occurs exclusively through `IIntentDispatcher.dispatch()`.

---

## Specification Note

No `design/specifications/AGENT_RUNTIME.md` exists in the repository -
the same situation as Packages 002, 009, 010, 011, 012, 013, 014, and
015. This package is built directly from the Founder's explicit work
order.

---

## Execution Lifecycle

```
                 create_plan / add_step / validate_plan   (Planner - unchanged by this package)
                              |
                              v
                         Plan (VALIDATED)
                              |
                    start_execution(plan)
                              |
                              v
                    Execution: CREATED  --publish EXECUTION_CREATED-->
                              |
                    (immediately) --> RUNNING  --publish EXECUTION_STARTED-->
                              |
              +---------------+---------------+
              |                               |
   for each remaining PlanStep,      status changes away from
   in order:                          RUNNING mid-loop (reentrant
     publish STEP_STARTED               pause_execution()/
     dispatcher.dispatch(...)           cancel_execution() call
     publish STEP_COMPLETED             from within a step's own
     (advance current_step)             dispatched action - the
                                         only way this can happen,
                                         since Version 1 has no
                                         concurrency)
              |                               |
              v                               v
   all steps dispatched               loop stops immediately;
   successfully                       Execution reflects whatever
              |                       pause_execution()/
              v                       cancel_execution() set
        COMPLETED
   --publish EXECUTION_COMPLETED--

   (at any point, a step's dispatch() raises)
              |
              v
          FAILED  --publish EXECUTION_FAILED-- (raise StepExecutionError)
          [no further steps run; no retries; no rollback]
```

`pause_execution(execution_id)` (RUNNING -> PAUSED) and
`resume_execution(execution_id)` (PAUSED -> RUNNING, then continues
the loop above from `current_step`) and `cancel_execution(execution_id)`
(CREATED/RUNNING/PAUSED -> CANCELLED) are the three additional
state-transition entry points described in the work order's Runtime
API. None publish a dedicated event - see Architectural Decision 3.

---

## Dependency Graph

```
AgentRuntime
    depends on -> IEventBus            (publish execution events)
    depends on -> IIntentDispatcher    (the only way a step is ever executed)
    depends on -> IPlanner             (read-only: confirm a Plan's canonical
                                         status is VALIDATED before executing it)

AgentRuntime does NOT depend on:
    argus.workflow    (WorkflowEngine is reached only indirectly, through
                        whatever the Dispatcher's own action_factory does)
    argus.plugins     (PluginManager is never referenced)
    argus.capability  (CapabilityRegistry is never referenced directly -
                        only indirectly, through the Dispatcher's own
                        resolve() call)
```

Construction order in `bootstrap.py` follows this dependency graph,
not the target architecture diagram's top-to-bottom position:
`AgentRuntime` is constructed immediately after the Planner (which is
itself constructed after the Intent Dispatcher) - the same
diagram-position-versus-construction-order distinction Package 013
first established for Capability Registry/Intent Dispatcher, and
Package 015 reapplied for Planner/Intent Dispatcher.

---

## Architectural Decisions

### 1. `start_execution(plan)` runs synchronously to a terminal-or-paused outcome, in a single call

Given this package's explicit "No concurrent execution" constraint,
there is no background thread or async mechanism to drive step
dispatch independently of the calling stack. `start_execution()`
therefore loops through `plan.steps` synchronously, dispatching each
in turn, until every step succeeds (`COMPLETED`), one fails
(`FAILED`, raising `StepExecutionError`), or the Execution's status
changes away from `RUNNING` mid-loop. The third case is only reachable
via a **reentrant call**: a dispatched step's own action calling back
into `pause_execution()`/`cancel_execution()` before its `dispatch()`
call returns - single-threaded, but genuinely reentrant, exactly the
mechanism this package's own required test scenarios (pause, resume)
exercise. This is documented explicitly rather than left implicit,
since "pause a synchronous, concurrency-free loop" is not otherwise
obviously possible.

### 2. The synthetic-Intent dispatch design (and its resulting limitation)

`IIntentDispatcher.dispatch()` accepts only an `Intent`, resolving a
Capability purely by `intent.name` (`IntentType`) via
`ICapabilityRegistry.find_by_intent_type()` - it has no parameter for
a specific capability id, and this package's Constraints forbid
modifying Dispatcher's responsibilities. Since every `PlanStep` names
a specific `required_capability` id rather than an `IntentType`,
`AgentRuntime` cannot ask the Dispatcher to resolve that exact
capability directly. The Runtime instead constructs a synthetic
`Intent` for every dispatched step, reusing the Plan's own
`originating_intent.name`, and passes `required_capability` (plus
`step_id`/`plan_id`/`execution_id`) in `dispatch()`'s `context`
argument for traceability only - the *current* Dispatcher
implementation does not consult `context` to select a Capability.
**Known limitation, not an oversight:** in Version 1, every step of a
given Plan resolves to whichever Capability the Dispatcher would
select for the Plan's originating `IntentType` (the first enabled
match), regardless of each step's own `required_capability` value.
Reconciling Planner's step-level capability targeting with
Dispatcher's intent-level resolution granularity is left to a future
package - one that would need to extend `IIntentDispatcher` with a
capability-id-aware entry point, which this package's own Constraints
explicitly forbid attempting here.

### 3. No dedicated event for pause/resume/cancel

This package's Events section names exactly six event types to add -
`EXECUTION_CREATED`, `EXECUTION_STARTED`, `STEP_STARTED`,
`STEP_COMPLETED`, `EXECUTION_COMPLETED`, `EXECUTION_FAILED` - and none
of them correspond to `pause_execution()`, `resume_execution()`, or
`cancel_execution()`. Rather than inventing three additional event
types not listed, `AgentRuntime` publishes exactly these six and
nothing else; `pause_execution()`/`cancel_execution()`'s resulting
state change is observable via `get_execution()`/`list_executions()`
instead. `resume_execution()` does not re-publish `EXECUTION_STARTED`
(that already fired once for this Execution's original start) - it
silently transitions to `RUNNING` and continues the same step loop,
which itself publishes `STEP_STARTED`/`STEP_COMPLETED` and, eventually,
`EXECUTION_COMPLETED` or `EXECUTION_FAILED`.

### 4. `start_execution()` requires the Planner's own canonical Plan to be VALIDATED

The Runtime's first listed responsibility is "execute validated
Plans." Rather than trusting the `Plan` object a caller happens to
pass in (which could be stale), `start_execution()` calls
`IPlanner.get_plan(plan.id)` to fetch the Planner's own current,
canonical record, and requires its `status` to be `PlanStatus.VALIDATED`
before proceeding - raising `InvalidExecutionStateError` otherwise
(including when the Planner has no record of `plan.id` at all). This
is a read-only check, not a call to `validate_plan()` - the Runtime
never performs validation itself, per its explicit "shall NOT validate
Plans" constraint. The canonical Plan's own `steps` (not the possibly-
stale passed-in `plan.steps`) are what actually gets executed.

### 5. `Execution.id`, not `execution_id`, for the model's own self-identifier

The work order's suggested `Execution` fields list `execution_id`,
but every other value object in this codebase (`Capability`, `Plugin`,
`Plan`, `PlanStep`) uses a plain `id` field for its own identity,
reserving `<noun>_id` naming for references to a *different* model
(for example, `Capability.workflow_id`). `Execution.plan_id` follows
that second convention (referencing a `Plan` by id); `Execution.id`
follows the first, per "Follow the repository conventions established
in previous packages," this work order's own explicit standing
instruction. `execution_id` remains the parameter name used throughout
the public API (`get_execution(execution_id)`, event payload keys,
etc.) - only the model's own field name differs from the work order's
suggestion.

### 6. `PlanStep.optional` is not consulted during execution

Neither this package's Runtime Responsibilities nor its Failure Rules
mention any exception for optional steps - "If a step fails: mark
execution FAILED... stop execution immediately" is stated
unconditionally. `AgentRuntime` therefore treats every dispatched step
identically regardless of `PlanStep.optional` (a flag that, per
Package 015, currently only affects `Planner.validate_plan()`'s own
capability-existence check). Extending `optional`'s meaning to "skip
on execution failure, don't stop the run" is a natural future
enhancement, explicitly out of this package's intentionally-small
Version 1 scope.

---

## Events

Exactly the six event types this package's own Events section names:
`EXECUTION_CREATED`, `EXECUTION_STARTED`, `STEP_STARTED`,
`STEP_COMPLETED`, `EXECUTION_COMPLETED`, `EXECUTION_FAILED`.
`EXECUTION_COMPLETED` and `EXECUTION_FAILED` are mutually exclusive
outcomes for a single `start_execution()`/`resume_execution()` run,
matching the `WORKFLOW_COMPLETED`/`WORKFLOW_FAILED` (Package 010) and
`DISPATCH_COMPLETED`/`DISPATCH_FAILED` (Package 012) precedent. See
Architectural Decision 3 for why no pause/resume/cancel-specific event
was added.

---

## IService Adoption

`IAgentRuntime` DOES inherit `IService` - breaking the three-
consecutive-non-adopter streak set by Capability Registry (013),
Plugin Manager (014), and Planner (015). `start_execution()`/
`resume_execution()` are genuinely gated on the Runtime's own
`RUNNING` state, architecturally identical to `WorkflowEngine.execute()`
(010), `ConversationManager.receive()` (011), and
`IntentDispatcher.dispatch()` (012). `pause_execution()`/
`cancel_execution()`/`get_execution()`/`list_executions()` remain
ungated, matching `Scheduler.pause()`/`resume()`'s (008) precedent for
per-item registry operations that don't imply anything about the
owning service's own lifecycle. See `argus/runtime/interfaces.py`'s
Architectural Note and `design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`'s
newly appended Empirical Finding, which records `AgentRuntime` as the
sixth `IService` adopter and the fifth genuinely-gated one.

---

## Repository Verification Note

The uploaded repository ("ArgusOS (15).zip") was verified against this
package's own general "verify repository state, verify version
consistency, run smoke validation" pre-flight instruction (this work
order did not specify a fixed pre-flight checklist the way Packages
013-015's did). Findings: HEAD (`1230851`, "Implement Package 015
Planner") is exactly the commit tag `v0.1.5` points to - unlike the
prior five packages, no separate "Synchronize repository version"
commit sits on top of the tagged commit this time. Instead, the
working tree contained one **uncommitted** modification to
`argus/bootstrap.py`, bumping `CORE_SERVICES_VERSION` from `"0.1.4"`
to `"0.1.5"` (`git diff` confirmed exactly 1 insertion/1 deletion,
matching the shape of every prior sync). This is a process variation
worth surfacing, not a blocker: the working tree's actual, substantive
state - the only thing pre-flight verification is meant to protect -
was fully correct: `argus/planner/` (Package 015) present; `python -m
pytest` passing (847 passed, 38 subtests); `python -m unittest
discover -s tests` passing (759); `python main.py` starting and
shutting down cleanly (exit 0); `CORE_SERVICES_VERSION == "0.1.5"`
matching tag `v0.1.5`. All confirmed before any Package 016 code was
written.

---

## Files Created

```
argus/
    runtime/
        __init__.py
        execution.py
        runtime.py
        interfaces.py
        exceptions.py
tests/
    test_execution.py
    test_runtime.py
```

## Files Modified

```
argus/bootstrap.py            (construct + register Agent Runtime as
                                16th core service, immediately after
                                the Planner; depends on the Event Bus,
                                the Intent Dispatcher, and the Planner;
                                CORE_SERVICES_VERSION left at "0.1.5"
                                - not advanced by this package)
argus/events/event_types.py   (6 new event types)
argus/tests/test_bootstrap.py (CORE_SERVICE_NAMES tuple only, per the
                                standing Package 011 rule)
tests/test_bootstrap.py       (CORE_SERVICE_NAMES tuple + 3 new tests)
design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md (Empirical Finding
                                appended; Status remains Proposed)
CHANGELOG.md, DEVLOG.md, IMPLEMENTATION_REPORT.md, factory/ROADMAP.md
```

`argus/dispatcher/`, `argus/capability/`, `argus/workflow/`,
`argus/plugins/`, and `argus/planner/` are unchanged - the Runtime's
only touchpoints with the rest of the system are
`IIntentDispatcher.dispatch()` and `IPlanner.get_plan()`, both called
through their existing, unmodified public interfaces.

---

## Test Totals

831 tests passing via `python -m unittest discover -s tests` (759 from
Packages 002-015, plus 22 new in `test_execution.py`, plus 47 new in
`test_runtime.py`, plus 3 new in `test_bootstrap.py` [23->26]). `python -m unittest discover -s argus/tests` remains
at 64 (duplicate tree unaffected beyond the standing
`CORE_SERVICE_NAMES` sync). `python -m pytest` also passes: 919
passed, 38 subtests passed.

---

## Coverage

100% line coverage on every new/modified module measured for this
package: `argus/runtime/__init__.py`, `argus/runtime/execution.py`,
`argus/runtime/runtime.py`, `argus/runtime/interfaces.py`,
`argus/runtime/exceptions.py`, `argus/bootstrap.py`, and
`argus/events/event_types.py` - all 100%, no accepted gaps. Overall
repository coverage: 99%, unchanged from Package 015.

---

## Known Limitations

- **Per-step capability targeting is not honored by Dispatcher
  resolution in Version 1** - see Architectural Decision 2. Every step
  of a Plan resolves to the same Capability the Plan's originating
  `IntentType` would resolve to, regardless of each step's own
  `required_capability` id. A future package must extend
  `IIntentDispatcher` (without violating this package's own "do not
  modify Dispatcher responsibilities" constraint on *this* package) to
  resolve this gap.
- `PlanStep.optional` has no effect on execution - see Architectural
  Decision 6.
- No persistence - Executions are held only in memory; nothing
  survives a process restart.
- No concurrency, no retries, no rollback - explicit Version 1
  constraints, not omissions. A failed step stops the entire run
  immediately.
- `pause_execution()`/`cancel_execution()` are only reachable on a
  `RUNNING` Execution via a **reentrant** call from within a
  dispatched step's own action - there is no external, out-of-band way
  to pause or cancel a `start_execution()` call already in progress,
  since Version 1 has no concurrency. This is fully functional and
  tested (see `tests/test_runtime.py::PauseResumeTests`), but is a
  narrower mechanism than "pause a long-running execution from another
  thread," which is out of Version 1 scope by construction.
- The repository's stray `argus/` duplicate tree (beyond the one
  explicitly-required `test_bootstrap.py` sync) and legacy pre-Factory
  files remain unresolved, out of scope per the Founder's explicit
  repository rules.

---

## Future Expansion

- Resolve the synthetic-Intent limitation (Architectural Decision 2)
  by extending `IIntentDispatcher` with a capability-id-aware dispatch
  entry point, in a dedicated package that explicitly revisits
  Dispatcher's contract (out of bounds for this package).
- Wire `Planner.create_plan()` and `AgentRuntime.start_execution()`
  together automatically for a resolved Intent, closing the
  "currently-unowned architectural gap" flagged in Packages 011-015's
  own reports.
- Resolve `PlanStatus.READY`/`COMPLETED` (Package 015's own reserved,
  unreachable-in-V1 status values) by having a future package report
  Execution outcomes back onto the originating Plan.
- Add real concurrency (a background thread or async execution model)
  so `pause_execution()` can be called out-of-band, not only
  reentrantly from within a dispatched step.

---

## Release Rules

Per the Founder's explicit instruction: no commit, tag, or push was
performed. `CORE_SERVICES_VERSION` was not changed by this package -
it remains `"0.1.5"`. This package is not reported as complete or
released - implementation ends after successful local verification;
final validation, integration, release, version update, commit, and
tag are the Founder's responsibility against the live repository.
