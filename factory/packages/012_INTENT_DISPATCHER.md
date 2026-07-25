# Implementation Package 012 - Intent Dispatcher

## Objective

Translate a resolved Intent into an executable Action and delegate its
execution, closing the gap between the Intent Router (classification,
Package 009) and the Workflow Engine (execution, Package 010) with a
mapping layer that is configurable rather than hard-coded, per the
Founder's Package 012 work order.

---

## Specification Note

No `design/specifications/DISPATCHER.md` exists in the repository - the
same situation as Packages 002, 009, 010, and 011. This package is
built directly from the Founder's explicit work order.

---

## Constraints (Explicit, Non-Negotiable)

- Never parses intents, never executes workflows itself, never
  performs AI reasoning - it determines the appropriate Action and
  delegates execution to that Action's own `execute()` method.
  `dispatcher.py` never imports `argus.workflow` (any submodule),
  `argus.intent.router`, `argus.intent.parser`, or `argus.conversation`,
  verified structurally by test.
- Mappings are deterministic and configurable at runtime
  (`register_mapping()` / `remove_mapping()`), and are not hard-coded
  inside `dispatcher.py` - the Version 1 default mapping *values* live
  in `argus/dispatcher/mapping.py`, pure data with no service
  dependency; `dispatcher.py` itself contains no mapping literals at
  all.
- The Action abstraction (`argus/dispatcher/action.py`) permits future
  Action kinds (e.g. `PluginAction`, `AgentAction`, `ConnectorAction`)
  without redesigning `dispatcher.py`: `Action` declares one abstract
  method, `execute()`; each concrete Action is constructed with
  whatever backend it needs (a `WorkflowAction` takes an
  `IWorkflowEngine` and a `workflow_id`), and `dispatcher.py` calls
  only `action.execute()`, never anything specific to any one Action
  kind, other than an `isinstance(action, WorkflowAction)` check used
  solely to publish the workflow-specific `WorkflowSelected` event.
- No AI, no LLM, no networking, no persistence, no plugins, no
  retries. Deterministic behavior only.

---

## Architectural Note: IntentDispatcher Does Not Depend on IWorkflowEngine

Unlike ConversationManager (Package 011), which is constructed with a
live `IWorkflowEngine` and calls `execute()` on it directly,
`IntentDispatcher.__init__` takes only an `IEventBus`. The dependency
on `IWorkflowEngine` lives entirely inside whichever `WorkflowAction`
instances are registered via `register_mapping()` - constructed by
`bootstrap.py` in Version 1, not by the dispatcher itself. This is a
deliberate design choice, not an oversight: it is what actually
satisfies the work order's "should permit future Action implementations
... without redesigning the dispatcher" requirement literally -
`dispatcher.py` has zero lines of code that would need to change to
support a `PluginAction` or `AgentAction` alongside or instead of
`WorkflowAction`. See `argus/dispatcher/dispatcher.py`'s module
docstring and `argus/dispatcher/action.py`'s module docstring for the
full rationale.

---

## The Five "Initial Mappings" and the Workflows They Reference

The work order's five Version 1 initial mappings (QUESTION -> Answer
Workflow, COMMAND -> Command Workflow, MEMORY -> Memory Workflow,
SCHEDULE -> Reminder Workflow, UNKNOWN -> Unknown Handler Workflow) are
registered at bootstrap time as five `WorkflowAction` instances, each
referencing a conventional `workflow_id` string defined in
`argus/dispatcher/mapping.py`'s `DEFAULT_WORKFLOW_IDS` table
(`"answer_workflow"`, `"command_workflow"`, `"memory_workflow"`,
`"reminder_workflow"`, `"unknown_handler_workflow"`).

**This package does not create any actual Workflow with real "answer,"
"command," "memory," "reminder," or "unknown handling" business logic**
- doing so would mean inventing unspecified Workflow step content,
which is out of this package's scope (the work order describes the
Dispatcher's own architecture, not the content of any particular
workflow). This mirrors the precedent already set by
`ConversationManager.receive()` (Package 011), which accepts a
caller-supplied `workflow_id` and assumes "workflows are assumed to
already be registered elsewhere" without ConversationManager ever
calling `register_workflow()` itself.

The practical consequence, and an explicitly tested one (see
`tests/test_intent_dispatcher.py::DispatchFailureTests`): until some
other component registers an actual workflow under one of these five
`workflow_id`s, `dispatch()`-ing any of these five intents will raise
`ActionExecutionError` (wrapping `IWorkflowEngine`'s own
`WorkflowNotFoundError`), and publish `DispatchFailed` with
`stage="execute"`. This is the expected, by-design Version 1 behavior,
not a bug - exactly analogous to calling
`ConversationManager.receive(text, workflow_id="something-unregistered")`
today.

---

## IService Adoption

`IIntentDispatcher` inherits `IService`, per the Founder's explicit
instruction, making `IntentDispatcher` a fifth real adopter after
Scheduler (008), IntentRouter (009), WorkflowEngine (010), and
ConversationManager (011). Like Scheduler, WorkflowEngine, and
ConversationManager (and unlike IntentRouter), `dispatch()` - the
dispatcher's single "do real work" method - is genuinely gated on the
dispatcher's own lifecycle state being `RUNNING`.
`register_mapping()`/`remove_mapping()`/`resolve()`/`list_mappings()`
remain ungated registry operations, matching the precedent from all
three prior gated adopters. This continues to reinforce ADR-0002's
originally proposed criterion; see `IMPLEMENTATION_REPORT.md`'s ADR
section and `design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`'s
newly appended finding.

---

## Repository Verification Note

Before writing any code, the uploaded repository was verified fresh
against the Founder's four explicit preconditions: it contains Package
011 (commit `7dbfb80`, `argus/conversation/` present), and a version
marker at or beyond `v0.1.1` (git tag `v0.1.1`, pointing exactly at
that commit).

One discrepancy was found on the first upload for this package and
reported rather than worked around: `CORE_SERVICES_VERSION` in
`argus/bootstrap.py` still read `"0.1.0"` while the repository's own
released git tag was `v0.1.1` - the constant had not been advanced to
match the actual Package 011 release. Per this package's own explicit
"if any verification fails, STOP" instruction, this was reported to
the Founder rather than silently resolved. The Founder corrected the
repository directly (commit `1df8dbb`, "Synchronize repository version
with v0.1.1 release," bumping `CORE_SERVICES_VERSION` to `"0.1.1"` and
rewriting the constant's comment to match this package's own Version
Policy wording) and supplied a corrected upload. Pre-flight
verification was re-run against that corrected repository and passed:
`CORE_SERVICES_VERSION == "0.1.1"`, matching tag `v0.1.1`; 487 canonical
tests passing; `python main.py` starting and shutting down cleanly.
Package 012 itself does not touch `CORE_SERVICES_VERSION` at all, per
this package's own explicit Version Policy - see
`IMPLEMENTATION_REPORT.md`.

---

## Specifications Referenced

- factory/packages/005_SERVICE_LIFECYCLE.md (`IService`, `LifecycleManager`)
- factory/packages/008_SCHEDULER_SERVICE.md, factory/packages/
  010_WORKFLOW_ENGINE.md, factory/packages/011_CONVERSATION_MANAGER.md
  (nearest precedent for genuine `IService` gating on a single "do
  real work" method, and for the "delegate through an existing
  service's own public interface, never its internals" pattern)
- factory/packages/009_INTENT_ROUTER.md (`Intent`, `IntentType` - the
  data types this package's `resolve()`/`dispatch()` consume)
- factory/packages/010_WORKFLOW_ENGINE.md (`IWorkflowEngine.execute()`
  - the delegation target `WorkflowAction` calls)

---

## Files Created

```
argus/
    dispatcher/
        __init__.py
        action.py
        dispatcher.py
        exceptions.py
        interfaces.py
        mapping.py
tests/
    test_dispatcher.py
    test_intent_dispatcher.py
```

## Files Modified

```
argus/bootstrap.py                 (construct + register IntentDispatcher
                                     as the twelfth core service; five
                                     WorkflowAction mappings registered
                                     at bootstrap; CORE_SERVICES_VERSION
                                     left at "0.1.1" - not advanced)
argus/events/event_types.py        (6 new event types)
argus/tests/test_bootstrap.py      (CORE_SERVICE_NAMES tuple only, per
                                     the standing Package 011 rule)
tests/test_bootstrap.py            (CORE_SERVICE_NAMES tuple + 2 new
                                     tests)
design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md (Empirical Finding
                                     appended; Status remains Proposed)
CHANGELOG.md, DEVLOG.md, IMPLEMENTATION_REPORT.md, factory/ROADMAP.md
```

---

## Test Totals

553 tests passing (487 existing + 66 new): 19 in `test_dispatcher.py`
(Action/WorkflowAction/DEFAULT_WORKFLOW_IDS), 45 in
`test_intent_dispatcher.py` (IntentDispatcher itself), 2 added to
`tests/test_bootstrap.py`.

---

## Release Rules

Per the Founder's explicit instruction: no commit, tag, or push was
performed. `CORE_SERVICES_VERSION` was not changed. This package is
not reported as complete or released - implementation ends after
successful local verification; final validation, integration, release,
version update, commit, and tag are the Founder's responsibility
against the live repository.
