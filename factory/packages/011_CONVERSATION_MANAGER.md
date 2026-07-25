# Implementation Package 011 - Conversation Manager

## Objective

Give ArgusOS a single point of coordination for a user conversation:
track session state and message history, and route each message
through the two existing core services responsible for the actual
work - the Intent Router (classification) and the Workflow Engine
(execution) - per the Founder's Package 011 work order.

---

## Specification Note

No `design/specifications/CONVERSATION.md` exists in the repository -
the same situation as Packages 002, 009, and 010. This package is
built directly from the Founder's explicit work order.

---

## Constraints (Explicit, Non-Negotiable)

- Never performs AI reasoning, never parses intents itself, never
  executes workflows itself - it coordinates `IIntentRouter` and
  `IWorkflowEngine` through their own published interfaces only.
  `manager.py` never imports `argus.intent.parser` (the actual
  classification logic) or any of `argus.knowledge`/`argus.memory`/
  `argus.scheduler`, verified structurally by test.
- Exactly one active (non-CLOSED) session at a time in Version 1.
- No persistence, no networking, no streaming, no plugins, no AI, no
  LLM, no external libraries, no threading, no background execution.

---

## Repository Verification Note

Before writing any code, the uploaded repository was verified fresh
to actually contain Package 010 (commit `77a32ac`, `argus/workflow/`
present, 416 canonical tests) and a version marker at or beyond
`v0.1.0` (git tag `v0.1.0`, confirmed pointing exactly at that same
commit) - both explicit preconditions of the Founder's work order.

One discrepancy was found and is resolved here, not silently: the
repository's git tag scheme changed from per-package `v0.0.N` to
semantic `v0.1.0` at the Package 010 tag, but `argus/bootstrap.py`'s
`CORE_SERVICES_VERSION` constant was left at the superseded `"0.0.10"`
string value. Per the Founder's standing policy - `CORE_SERVICES_VERSION`
always reflects the repository's last actual release, not the package
currently being implemented, and only advances after integration,
validation, commit, and tag - this package leaves the constant at
`"0.1.0"`, the currently released version, rather than bumping it
during implementation. Documented in `bootstrap.py`'s own comment and
in `IMPLEMENTATION_REPORT.md`.

---

## IService Adoption

`IConversationManager` inherits `IService`, per the Founder's explicit
instruction, making `ConversationManager` a fourth real adopter after
Scheduler (008), IntentRouter (009), and WorkflowEngine (010). Like
Scheduler and WorkflowEngine (and unlike IntentRouter),
`receive()` - the manager's single "do real work" method - is
genuinely gated on the manager's own lifecycle state being `RUNNING`.
`start_session()`, `end_session()`, `history()`, and `active_session()`
remain ungated registry operations, matching the precedent from both
prior gated adopters. This continues to reinforce ADR-0002's original
proposed criterion; see IMPLEMENTATION_REPORT.md's ADR section for
the appended finding.

---

## Specifications Referenced

- factory/packages/005_SERVICE_LIFECYCLE.md (`IService`, `LifecycleManager`)
- factory/packages/008_SCHEDULER_SERVICE.md, factory/packages/
  010_WORKFLOW_ENGINE.md (nearest precedent for genuine `IService`
  gating on a single "do real work" method)
- factory/packages/009_INTENT_ROUTER.md (delegation target;
  `IIntentRouter.parse()`)
- factory/packages/010_WORKFLOW_ENGINE.md (delegation target;
  `IWorkflowEngine.execute()`)
- design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md
- design/specifications/INTERFACES.md
- factory/standards/CODING_STANDARD.md

---

## Files to Create

argus/conversation/
    __init__.py
    interfaces.py
    manager.py
    session.py
    message.py
    state.py
    exceptions.py

tests/
    test_conversation.py
    test_conversation_manager.py

---

## Files to Modify

- argus/bootstrap.py (construct and register `ConversationManager` as
  the eleventh core service; `CORE_SERVICES_VERSION` remains
  `"0.1.0"`, the repository's currently released version - see the
  Repository Verification Note above)
- argus/events/event_types.py (add `CONVERSATION_STARTED`,
  `MESSAGE_RECEIVED`, `INTENT_RESOLVED`, `WORKFLOW_EXECUTED`,
  `RESPONSE_GENERATED`, `CONVERSATION_ENDED`)
- tests/test_bootstrap.py (extend core-service assertions to eleven
  services; new dedicated test)
- argus/tests/test_bootstrap.py (the repository's known, pre-existing
  stray duplicate of tests/test_bootstrap.py - per the Founder's
  explicit instruction, only its `CORE_SERVICE_NAMES` tuple was
  synchronized with `"conversation_manager"` added, matching exactly
  how `"intent_router"` and `"workflow_engine"` were previously added
  there; no other line in that file, and no other duplicate-tree file
  anywhere in the repository, was touched)
- CHANGELOG.md, DEVLOG.md, IMPLEMENTATION_REPORT.md,
  design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md

`design/ARCHITECTURE.md` is not modified: `IConversationManager`
inheriting `IService` with a genuine gate is not a new architectural
decision (Scheduler and WorkflowEngine already established it).

---

## Acceptance Criteria

- `python main.py` starts and shuts down cleanly.
- All pre-existing canonical tests continue to pass.
- `ConversationManager` resolves from the Container and appears in
  the Service Registry and Lifecycle Manager
  (`LifecycleState.REGISTERED`), alongside the ten existing core
  services - registered only, not started.
- `start_session` / `end_session` / `receive` / `history` /
  `active_session` / `status` behave per this document and the
  Founder's work order.
- `receive()` only runs while the manager's own `IService` state is
  `RUNNING`, and only against an active, non-CLOSED session;
  otherwise it raises.
- Exactly one session may be active at a time; `start_session()` while
  one is already active raises `ActiveSessionExistsError`.
- `receive()` delegates classification to `IIntentRouter.parse()` and,
  when a `workflow_id` is supplied and currently registered, execution
  to `IWorkflowEngine.execute()` - `manager.py` never classifies text
  or runs workflow steps itself, verified structurally by test.
- `ConversationStarted`/`MessageReceived`/`IntentResolved`/
  `WorkflowExecuted`/`ResponseGenerated`/`ConversationEnded` are each
  published at the correct point.
- The manager never imports `argus.intent.parser`, `argus.knowledge`,
  `argus.memory`, or `argus.scheduler`.

---

## Out of Scope

- Any AI/ML-based response generation - responses are a small, fixed
  set of deterministic templates keyed on the resolved Intent's name.
- Multiple concurrent active sessions (Version 1 constraint).
- Persistence of sessions across process restarts.
- Networking, streaming, or plugin support of any kind.
- Automatic mapping from an Intent to a specific workflow_id - the
  caller of `receive()` supplies `workflow_id` explicitly; no
  intent-to-workflow routing table is invented here.
- Calling `IIntentRouter.route()` or `register_handler()` - this
  manager only uses `parse()`'s direct return value for its own,
  synchronous use of the classification.
- Calling `IWorkflowEngine.register_workflow()` - workflows are
  assumed to already exist; this manager only ever executes an
  existing `workflow_id`.
- Resolving the `IService` duplication question itself - this
  package adds a fourth empirical data point, per the Founder's
  standing instruction, not a resolution.
