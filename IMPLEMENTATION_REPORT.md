# ArgusOS Implementation Report — Package 011: Conversation Manager

## 1. Package Overview

Package 011 adds `argus/conversation/`, ArgusOS's first cross-service coordinator. `ConversationManager` tracks a single active session's state and full message history, and for each user message delegates classification to `IIntentRouter.parse()` and, when a `workflow_id` is supplied and currently registered, execution to `IWorkflowEngine.execute()` — it never classifies text or runs workflow steps itself, verified structurally by test (the module never imports `argus.intent.parser`, `argus.knowledge`, `argus.memory`, or `argus.scheduler`). Responses are generated from a small, fixed, deterministic template table keyed on the resolved intent's name — never AI/LLM inference. `IConversationManager` inherits `IService`; `receive()` is genuinely gated on the manager's own lifecycle state being `RUNNING` (mirroring Scheduler and WorkflowEngine), while `start_session`/`end_session`/`history`/`active_session` remain ungated registry operations. `ConversationManager` is registered as ArgusOS's eleventh core service. All 416 pre-existing canonical tests still pass; 71 new tests were added (487 total in `tests/`), all passing under `python -m unittest discover -s tests`. No pytest anywhere in this package. `python main.py` starts and shuts down cleanly.

## 2. Repository Verification Note

Before writing any code, the uploaded repository was verified fresh against the Founder's three explicit preconditions: it already contains Package 010 (commit `77a32ac`, "Implement Package 010 Workflow Engine"), `argus/workflow/` is present, and a version marker at or beyond `v0.1.0` exists (git tag `v0.1.0`, confirmed via `git rev-list -n 1 v0.1.0` to point at exactly that same commit). All three passed; 416 canonical tests confirmed passing on this baseline before any Package 011 file was touched.

One discrepancy was found during this verification, documented rather than silently resolved: the repository's git tag scheme changed from per-package `v0.0.N` to semantic `v0.1.0` starting at the Package 010 tag, but `argus/bootstrap.py`'s own `CORE_SERVICES_VERSION` constant had not been updated to match - it still read the superseded `"0.0.10"`. An initial delivery of this package bumped the constant to `"0.1.1"`, by direct analogy with every prior package's own convention of bumping it to that package's target version during implementation. The Founder corrected this with a standing policy: `CORE_SERVICES_VERSION` must always reflect the repository's *last actual release* (git tag + committed history), not the package currently being implemented, since advancing it during implementation makes the source code claim a version ahead of git history. Package 011 has not been integrated, committed, or tagged, so `CORE_SERVICES_VERSION` remains `"0.1.0"` - the currently released version - in this delivery. `bootstrap.py`'s comment at the constant's definition now states this policy explicitly for future packages.

Per the Founder's explicit release rules, this implementation was built, tested, and verified entirely within the supplied repository. No `git commit`, `git tag`, push, or git-history modification of any kind was performed, and this package is not being reported as complete - final validation, integration, release, tagging, and git operations are the Founder's responsibility, to be performed against the live repository after independent regression testing.

## 3. Architectural Rationale

No `design/specifications/CONVERSATION.md` exists - the same situation as Packages 002, 009, and 010. Every structural decision traces to the Founder's explicit work order.

The central open question the work order did not resolve explicitly: what concretely does "delegates execution to the Workflow Engine" mean, given no intent-to-workflow catalog or routing table was specified anywhere in the repository? Inventing one would itself have been exactly the kind of business logic the work order says this manager "should never contain." Instead, `receive()` accepts an optional, caller-supplied `workflow_id`. If given and currently registered, `receive()` calls `IWorkflowEngine.execute()` for real and publishes `WorkflowExecuted`; if omitted, or if the delegated call raises (`WorkflowNotFoundError` or `WorkflowError`, e.g. because the Workflow Engine hasn't been started), the attempt is skipped gracefully and `receive()` still returns a response. This keeps the delegation structurally genuine - a real `IWorkflowEngine.execute()` call happens end-to-end when a caller supplies a valid, ready workflow - without ConversationManager deciding, on its own, which workflow an intent "should" trigger.

## 4. IService Adoption — A Fourth Data Point for ADR-0002

`IConversationManager` inherits `IService`, per the Founder's explicit instruction, making `ConversationManager` a fourth real adopter after Scheduler (008), IntentRouter (009), and WorkflowEngine (010). `receive()` is genuinely gated on the manager's own state being `RUNNING`, exactly mirroring `Scheduler.tick()` and `WorkflowEngine.execute()`; the four registry-style methods remain ungated, matching both prior gated adopters' precedent.

Across all four adopters to date: three (Scheduler, WorkflowEngine, ConversationManager) use `IService` for a genuine behavioral gate; one (IntentRouter) does not, having no "active work" phase to gate. This 3-to-1 pattern, now observed across four independently-specified packages, continues to support ADR-0002's originally proposed criterion. This finding has been appended to `design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`; its Status remains `Proposed`, per standing instruction.

## 5. Directory Tree (files touched)

```
argus/
    conversation/
        __init__.py
        exceptions.py
        interfaces.py
        state.py
        message.py
        session.py
        manager.py
    bootstrap.py                       (modified)
    events/
        event_types.py                 (modified)
design/
    decisions/
        0002_ISERVICE_ADOPTION_CRITERION.md   (modified — appended finding)
factory/
    packages/
        011_CONVERSATION_MANAGER.md    (new)
    ROADMAP.md                          (modified)
tests/
    test_bootstrap.py                   (modified)
    test_conversation.py                (new)
    test_conversation_manager.py        (new)
argus/tests/test_bootstrap.py           (modified — CORE_SERVICE_NAMES tuple only, per explicit instruction)
CHANGELOG.md                            (modified)
DEVLOG.md                               (modified)
IMPLEMENTATION_REPORT.md                (replaced — this file)
```

No file outside this list was created, deleted, moved, or modified. `argus/lifecycle/test_lifecycle.py`, `argus/CHANGELOG.md`, `argus/DEVLOG.md`, `argus/IMPLEMENTATION_REPORT.md`, `argus/factory/`, and every legacy pre-Factory file were left completely untouched.

## 6. Integration Notes

- `ConversationManager(event_bus, intent_router, workflow_engine)` — constructed in `bootstrap.py` immediately after the Workflow Engine, depending on the Event Bus, Intent Router, and Workflow Engine (all already constructed by that point).
- Registered in the Container as `"conversation_manager"`, in the Service Registry as a `ServiceDescriptor` (version `"0.1.0"`, the repository's currently released version - see Section 2), and in the Lifecycle Manager as `LifecycleState.REGISTERED` — matching the treatment of all ten prior core services. Not initialized or started by bootstrap; `receive()` requires a caller to call `manager.initialize()`/`start()` directly first, exactly as Scheduler and WorkflowEngine already require for their own gated methods.
- `argus/events/event_types.py` extended with six new members: `CONVERSATION_STARTED`, `MESSAGE_RECEIVED`, `INTENT_RESOLVED`, `WORKFLOW_EXECUTED`, `RESPONSE_GENERATED`, `CONVERSATION_ENDED`.
- Naming (`"conversation_manager"`) verified against the repository's own `tests/test_bootstrap.py::CORE_SERVICE_NAMES` convention before implementation.
- The repository's pre-existing, known stray duplicate `argus/tests/test_bootstrap.py` had its `CORE_SERVICE_NAMES` tuple synchronized with `"conversation_manager"` added, per this package's explicit Repository Rules - and only that tuple. Confirmed by inspecting that file's prior history: `"intent_router"` and `"workflow_engine"` were each previously added there the same way (tuple entry only, no dedicated per-service test method), so this package's sync matches the file's own established, empirically-observed pattern rather than inventing a new one.

## 7. Test Results

Canonical suite (`tests/`):
```
python -m unittest discover -s tests
Ran 487 tests in 0.043s
OK
```

The synchronized duplicate `argus/tests/` also verified passing standalone (unaffected by the one-line sync):
```
python -m unittest discover -s argus/tests -p "test_*.py"
Ran 64 tests in 0.015s
OK
```

`python main.py`:
```
2026-07-25 11:27:10 [INFO] argus: ArgusOS application started.
2026-07-25 11:27:10 [INFO] argus: ArgusOS application shutting down.
```
Exit code 0.

## 8. Coverage Summary

Measured with `coverage.py`, `python -m coverage run -m unittest discover -s tests`:

| Module | Stmts | Miss | Cover |
|---|---|---|---|
| `argus/bootstrap.py` | 49 | 0 | 100% |
| `argus/conversation/__init__.py` | 7 | 0 | 100% |
| `argus/conversation/exceptions.py` | 5 | 0 | 100% |
| `argus/conversation/interfaces.py` | 21 | 5 | 76% (unreachable abstract-method stub bodies, same structural pattern as every other ABC in this codebase) |
| `argus/conversation/manager.py` | 107 | 0 | 100% |
| `argus/conversation/message.py` | 19 | 0 | 100% |
| `argus/conversation/session.py` | 18 | 0 | 100% |
| `argus/conversation/state.py` | 6 | 0 | 100% |

Package 011 total (`argus/conversation/*`): 183 statements, 97% covered. Full `argus/*` coverage: 1,486 statements, 98% covered.

## 9. Engineering Decisions / Deviations from the Work Order

- **`workflow_id` is an explicit, optional parameter to `receive()`**, not derived automatically from the resolved Intent. See Section 3 — this avoids inventing an intent-to-workflow routing table, which the work order's own "should never contain business logic from other services" line would have made a real violation.
- **A failed or absent workflow delegation never raises out of `receive()`.** `WorkflowNotFoundError`/`WorkflowError` are caught and treated as "no delegation occurred" - `WORKFLOW_EXECUTED` simply doesn't publish, and the conversation turn still completes normally.
- **Removed a provably-unreachable defensive branch during coverage review.** `receive()` originally contained an explicit `if session.state == ConversationState.CLOSED: raise ...` check. Tracing the state machine showed this can never trigger: `end_session()` is the only path that sets `CLOSED`, and it always clears the active-session pointer in the same call, so `_require_active_session()` already raises `NoActiveSessionError` first in every real scenario. Removed rather than left as untested dead code, per the coding standard's "no dead code" requirement; `interfaces.py`'s docstring was updated to explain the invariant instead.
- **`CORE_SERVICES_VERSION` remains `"0.1.0"`, not bumped to `"0.1.1"` or `"0.0.11"`.** Per the Founder's standing policy: this constant tracks the repository's last actual release, not the package being implemented. See Section 2's Repository Verification Note.
- **`argus/tests/test_bootstrap.py` (duplicate tree) synchronized, tuple-only**, per this package's explicit, new-for-this-package Repository Rule. This is the only duplicate-tree file touched.
- **Exception base named `ConversationError`**, matching the `<Subsystem>Error` convention (`SchedulerError`, `IntentError`, `WorkflowError`).

## 10. Known Limitations

- Response generation is template-based, not natural language generation.
- No automatic intent-to-workflow mapping (see Section 3).
- Exactly one active session at a time (Version 1 constraint).
- Sessions and messages are held only in memory.
- `receive()` does not call `IIntentRouter.route()` or `register_handler()`, so other Event Bus subscribers to `IntentRouted` are not triggered by a conversation turn - only `parse()`'s direct return value is used.
- The repository's stray `argus/` duplicate tree (beyond the one explicitly-required `test_bootstrap.py` sync) and legacy pre-Factory files remain unresolved, out of scope per the Founder's explicit repository rules.

## 11. Repository-Derived Package Metrics (measured, not estimated)

Measured via `git diff --stat` against the working tree's unmodified base commit `77a32ac` (no commit was made — see Section 2):

- Files Created: 9 (7 `argus/conversation/*.py`, `factory/packages/011_CONVERSATION_MANAGER.md`, 2 new test files)
- Files Modified: 9 (`argus/bootstrap.py`, `argus/events/event_types.py`, `design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`, `factory/ROADMAP.md`, `tests/test_bootstrap.py`, `argus/tests/test_bootstrap.py`, `CHANGELOG.md`, `DEVLOG.md`, `IMPLEMENTATION_REPORT.md`)
- Lines Added: 1,791 / Lines Removed: 31
- Unit Tests: 487 passing in canonical `tests/` (71 new: 21 model + 49 manager + 1 bootstrap)
- Coverage: 97% (Package 011 modules), 98% (full `argus/*`)
- Public Classes: 3 (`ConversationSession`, `ConversationMessage`, `ConversationManager`) plus 2 Enums (`ConversationState`, `ConversationRole`)
- Public Interfaces: 1 (`IConversationManager`)
- New Dependencies: 0
- External Libraries: 0 (standard library only)
- Architecture Deviations: 0 (see Section 9 for documented, non-architectural deviations)

## 12. Pre-Completion Checklist (per the Founder's explicit checklist)

- ✓ **Bootstrap registration** — `ConversationManager(...)` constructed in `bootstrap.py`, registered in the Container as `"conversation_manager"`. Confirmed via `test_bootstrap_registers_conversation_manager_in_container`.
- ✓ **Service Registry registration** — recorded as a `ServiceDescriptor` (version `"0.1.0"`, the repository's currently released version) alongside all ten prior core services.
- ✓ **Lifecycle integration** — registered in the Lifecycle Manager as `LifecycleState.REGISTERED`.
- ✓ **Event Bus integration** — all six conversation events verified published at the correct points via `tests/test_conversation_manager.py`.
- ✓ **Workflow Engine delegation** — verified via `WorkflowEngineDelegationTests`, including that a real `IWorkflowEngine.execute()` call occurs and its result is reflected in the workflow's own state.
- ✓ **Intent Router delegation** — verified via `IntentRouterDelegationTests`, including a spy on `IIntentRouter.parse()` confirming the manager calls it with the exact received text.
- ✓ **Naming consistency** — `"conversation_manager"` verified against the repository's own `CORE_SERVICE_NAMES` convention before implementation.
- ✓ **All regression tests passing** — `python -m unittest discover -s tests` reports `Ran 487 tests ... OK`.
- ✓ **`python main.py` starts cleanly** — exit code 0.
- ✓ **No unintended repository changes** — confirmed via `git status`/`git diff --stat`; only the 18 files listed in Section 5 were touched, and the one duplicate-tree file modified (`argus/tests/test_bootstrap.py`) was explicitly authorized by this package's own Repository Rules.

## 13. Concise Implementation Summary

Package 011 adds `argus/conversation/`: an immutable `ConversationSession`/`ConversationMessage` model, `ConversationState`/`ConversationRole` enums, and a `ConversationManager` that tracks one active session, records message history, and processes each `receive()` call by delegating classification to `IIntentRouter.parse()` and (when a caller-supplied `workflow_id` is registered) execution to `IWorkflowEngine.execute()` - never doing either itself, verified structurally by test. Responses are template-based, never AI-generated. `IConversationManager` inherits `IService`, with `receive()` genuinely gated on `RUNNING` - a fourth data point reinforcing ADR-0002's pattern (kept `Proposed`, unchanged). Registered as ArgusOS's eleventh core service. 487 tests pass in `tests/` (71 new), 97%/100% coverage on `argus/conversation/` modules (100% on `manager.py` itself after removing one provably-dead defensive branch). Built and verified entirely within the Founder-supplied repository; no commit, tag, push, or git-history change was made, per instruction.

## 14. Architectural Observations

- Four packages in a row (Scheduler, IntentRouter, WorkflowEngine, ConversationManager) have now independently implemented `IService`, and three of the four converge on the identical shape: one gated "do real work" method, N ungated registry methods. This is a strong, stable enough pattern that a future ADR-0002 resolution package could reasonably codify it as a required shape for any future `IService` adopter, not just a documented tendency.
- This package is the first to depend on *two* other core services' interfaces directly (`IIntentRouter` and `IWorkflowEngine`), constructed and injected in `bootstrap.py` exactly like every single-dependency service before it. The DI pattern scaled to two dependencies with no changes needed to `Container` or `bootstrap.py`'s overall shape - worth noting as a confirmation that the dependency injection design from Package 002 continues to hold under increasing cross-service coordination, which is precisely what this package (and presumably future ones) needs more of.
- `receive()`'s `workflow_id` parameter is a caller-supplied pointer, not something ConversationManager derives from the Intent itself. If a future package wants "the right workflow runs automatically based on what the user said," that mapping needs a home - it does not belong in ConversationManager (per this package's own Non-Goals) or in IntentRouter (per Package 009's routing-not-invoking design) or in WorkflowEngine (which is intentionally ignorant of what registers its workflows). This is a real, currently-unowned architectural gap worth flagging for whichever future package is expected to close it.
