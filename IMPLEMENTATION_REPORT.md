# ArgusOS Implementation Report — Package 012: Intent Dispatcher

## 1. Package Overview

Package 012 adds `argus/dispatcher/`, the layer that translates a resolved `Intent` into an executable `Action` and delegates its execution — closing the gap between classification (`IIntentRouter`, Package 009) and execution (`IWorkflowEngine`, Package 010). `IntentDispatcher` maintains a configurable, in-memory `IntentType -> Action` mapping (`register_mapping`/`remove_mapping`/`list_mappings`, all ungated registry operations) and a `dispatch()` method that resolves an Intent to its Action and calls that Action's own `execute()` — it never parses intents, never runs a workflow's steps itself, and never performs AI reasoning, verified structurally by test (the module never imports `argus.workflow`, `argus.intent.router`, `argus.intent.parser`, or `argus.conversation`). `IIntentDispatcher` inherits `IService`; `dispatch()` is genuinely gated on the dispatcher's own lifecycle state being `RUNNING` (mirroring Scheduler, WorkflowEngine, and ConversationManager), while the four registry methods remain ungated. `IntentDispatcher` is registered as ArgusOS's twelfth core service. All 487 pre-existing canonical tests still pass; 66 new tests were added (553 total in `tests/`), all passing under `python -m unittest discover -s tests`. No pytest anywhere in this package. `python main.py` starts and shuts down cleanly.

## 2. Repository Verification Note

Before writing any code, the uploaded repository was verified fresh against the Founder's four explicit preconditions: it already contains Package 011 (commit `7dbfb80`, "Implement Package 011 Conversation Manager"), `argus/conversation/` is present, and a version marker at or beyond `v0.1.1` exists (git tag `v0.1.1`).

The first upload failed the fourth precondition, "`CORE_SERVICES_VERSION` matches the latest released version": the repository's `v0.1.1` tag confirmed Package 011 had genuinely been integrated, committed, and released, but `argus/bootstrap.py`'s own `CORE_SERVICES_VERSION` constant still read `"0.1.0"` — the value that had been correct only *before* that release. Per this package's own explicit "if any verification fails, STOP" instruction, this was reported to the Founder rather than silently corrected or worked around. The Founder corrected the repository directly (a dedicated commit, `1df8dbb`, "Synchronize repository version with v0.1.1 release," bumping the constant to `"0.1.1"` and rewriting its comment) and supplied a corrected upload. Pre-flight verification was re-run against that corrected repository and passed cleanly: `CORE_SERVICES_VERSION == "0.1.1"` matching tag `v0.1.1`, 487 canonical tests passing, `python main.py` starting and shutting down cleanly — all confirmed before any Package 012 code was written.

Per the Founder's explicit release rules, this implementation was built, tested, and verified entirely within the supplied repository. No `git commit`, `git tag`, push, or git-history modification of any kind was performed, `CORE_SERVICES_VERSION` was not changed by this package, and this package is not being reported as complete — final validation, integration, release, tagging, and git operations are the Founder's responsibility, to be performed against the live repository after independent regression testing.

## 3. Architectural Rationale

No `design/specifications/DISPATCHER.md` exists — the same situation as Packages 002, 009, 010, and 011. Every structural decision traces to the Founder's explicit work order.

The central design question: how to satisfy "the architecture should allow future Action types without redesigning the dispatcher" literally, not just aspirationally. Rejected the approach that would have mirrored `ConversationManager`'s own precedent (Package 011) of taking `IWorkflowEngine` directly as a constructor dependency — that would tie `dispatcher.py` to one specific backend, exactly the coupling the work order's extensibility requirement warns against. Instead, `Action` is a one-method abstract base class (`execute()`), and each concrete Action is constructed with whatever backend it needs: `WorkflowAction` takes a `workflow_id` and an `IWorkflowEngine`; a future `PluginAction`, `AgentAction`, or `ConnectorAction` would each take their own backend, entirely outside `dispatcher.py`'s knowledge. `IntentDispatcher.__init__` takes only an `IEventBus` — confirmed via a source-inspection test that `dispatcher.py` contains no `argus.workflow` import at all, the same technique Packages 010 and 011 used to structurally prove their own loose-coupling claims.

The second design question: what do the five Version 1 "Initial mappings" (QUESTION -> Answer Workflow, etc.) actually point to, given no other package has ever created a real "answer" or "command" workflow with real business logic — inventing one would itself have meant writing exactly the kind of business logic this package's work order never asked for. Followed the precedent `ConversationManager.receive()` already set for its own `workflow_id` parameter: register the mapping as data (a conventional `workflow_id` string, defined in `argus/dispatcher/mapping.py`'s `DEFAULT_WORKFLOW_IDS`), and let `IWorkflowEngine.execute()`'s own `WorkflowNotFoundError` be the honest, tested answer — wrapped as `ActionExecutionError` and published as `DispatchFailed` with `stage="execute"` — when nothing is registered under that id yet. See Section 9 and `factory/packages/012_INTENT_DISPATCHER.md`'s "The Five Initial Mappings" section for the full reasoning.

## 4. IService Adoption — A Fifth Data Point for ADR-0002

`IIntentDispatcher` inherits `IService`, per the Founder's explicit instruction, making `IntentDispatcher` a fifth real adopter after Scheduler (008), IntentRouter (009), WorkflowEngine (010), and ConversationManager (011). `dispatch()` is genuinely gated on the dispatcher's own state being `RUNNING`, exactly mirroring `Scheduler.tick()`, `WorkflowEngine.execute()`, and `ConversationManager.receive()`; the four registry-style methods remain ungated, matching all three prior gated adopters' precedent.

Across all five adopters to date: four (Scheduler, WorkflowEngine, ConversationManager, IntentDispatcher) use `IService` for a genuine behavioral gate; one (IntentRouter) does not, having no "active work" phase to gate. This 4-to-1 pattern, now observed across five independently-specified packages, continues to support ADR-0002's originally proposed criterion. This finding has been appended to `design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`; its Status remains `Proposed`, per standing instruction.

## 5. Directory Tree (files touched)

```
argus/
    dispatcher/
        __init__.py
        action.py
        dispatcher.py
        exceptions.py
        interfaces.py
        mapping.py
    bootstrap.py                       (modified)
    events/
        event_types.py                 (modified)
design/
    decisions/
        0002_ISERVICE_ADOPTION_CRITERION.md   (modified — appended finding)
factory/
    packages/
        012_INTENT_DISPATCHER.md       (new)
    ROADMAP.md                          (modified)
tests/
    test_bootstrap.py                   (modified)
    test_dispatcher.py                  (new)
    test_intent_dispatcher.py           (new)
argus/tests/test_bootstrap.py           (modified — CORE_SERVICE_NAMES tuple only, per explicit instruction)
CHANGELOG.md                            (modified)
DEVLOG.md                               (modified)
IMPLEMENTATION_REPORT.md                (replaced — this file)
```

No file outside this list was created, deleted, moved, or modified. `argus/lifecycle/test_lifecycle.py`, `argus/CHANGELOG.md`, `argus/DEVLOG.md`, `argus/IMPLEMENTATION_REPORT.md`, `argus/factory/`, and every legacy pre-Factory file were left completely untouched.

## 6. Integration Notes

- `IntentDispatcher(event_bus)` — constructed in `bootstrap.py` immediately after the Conversation Manager, depending only on the Event Bus. Five `WorkflowAction` instances are then constructed (one per `DEFAULT_WORKFLOW_IDS` entry, each wrapping the already-constructed `WorkflowEngine`) and registered via `register_mapping()` — the only place in this package a `WorkflowAction` is actually built.
- Registered in the Container as `"intent_dispatcher"`, in the Service Registry as a `ServiceDescriptor` (version `"0.1.1"`, the repository's currently released version — see Section 2), and in the Lifecycle Manager as `LifecycleState.REGISTERED` — matching the treatment of all eleven prior core services. Not initialized or started by bootstrap; `dispatch()` requires a caller to call `dispatcher.initialize()`/`start()` directly first, exactly as Scheduler, WorkflowEngine, and ConversationManager already require for their own gated methods.
- `argus/events/event_types.py` extended with six new members: `INTENT_DISPATCHED`, `ACTION_RESOLVED`, `WORKFLOW_SELECTED`, `DISPATCH_STARTED`, `DISPATCH_COMPLETED`, `DISPATCH_FAILED`.
- Naming (`"intent_dispatcher"`) verified against the repository's own `tests/test_bootstrap.py::CORE_SERVICE_NAMES` convention before implementation.
- The repository's pre-existing, known stray duplicate `argus/tests/test_bootstrap.py` had its `CORE_SERVICE_NAMES` tuple synchronized with `"intent_dispatcher"` added, per the standing Repository Rule introduced in Package 011 — and only that tuple. Matches the file's own established pattern (`"scheduler"`/`"intent_router"`/`"workflow_engine"`/`"conversation_manager"` were each added the same way: tuple entry only, no dedicated per-service test method).

## 7. Test Results

Canonical suite (`tests/`):
```
python -m unittest discover -s tests
Ran 553 tests in 0.057s
OK
```

The synchronized duplicate `argus/tests/` also verified passing standalone (unaffected by the one-line sync):
```
python -m unittest discover -s argus/tests -p "test_*.py"
Ran 64 tests in 0.016s
OK
```

`python main.py`:
```
2026-07-25 14:16:58 [INFO] argus: ArgusOS application started.
2026-07-25 14:16:58 [INFO] argus: ArgusOS application shutting down.
```
Exit code 0.

## 8. Coverage Summary

Measured with `coverage.py`, `python -m coverage run -m unittest discover -s tests`:

| Module | Stmts | Miss | Cover |
|---|---|---|---|
| `argus/bootstrap.py` | 54 | 0 | 100% |
| `argus/dispatcher/__init__.py` | 6 | 0 | 100% |
| `argus/dispatcher/action.py` | 23 | 1 | 96% (unreachable `raise NotImplementedError` in the abstract `Action.execute()` stub — Python's ABC machinery prevents instantiating a class with unimplemented abstract methods, so this line can never execute) |
| `argus/dispatcher/dispatcher.py` | 80 | 0 | 100% |
| `argus/dispatcher/exceptions.py` | 7 | 0 | 100% |
| `argus/dispatcher/interfaces.py` | 16 | 0 | 100% |
| `argus/dispatcher/mapping.py` | 4 | 0 | 100% |

Package 012 total (`argus/dispatcher/*`): 136 statements, 99% covered (135/136). Full `argus/*` coverage: 1,631 statements, 98% covered (1,597/1,631).

## 9. Engineering Decisions / Deviations from the Work Order

- **`IntentDispatcher` does not take an `IWorkflowEngine` constructor dependency**, unlike `ConversationManager`'s direct-dependency precedent. This is what actually makes the work order's "without redesigning the dispatcher" requirement true rather than aspirational — see Section 3 and `factory/packages/012_INTENT_DISPATCHER.md`'s Architectural Note. `WorkflowAction` carries the `IWorkflowEngine` dependency instead, and `bootstrap.py` is the only place a `WorkflowAction` is constructed.
- **The five "Initial mappings" reference `workflow_id`s with no real workflow registered against them anywhere in the repository.** This is a deliberate scope boundary, not an oversight — see Section 3. `mapping.py`'s own module docstring documents this explicitly, and `tests/test_intent_dispatcher.py::DispatchFailureTests` tests the resulting `ActionExecutionError` failure mode directly.
- **`WorkflowSelected` is the one dispatcher-level event that is Action-kind-specific.** It fires only when `isinstance(action, WorkflowAction)` is true — the single, deliberately narrow place `dispatcher.py` knows anything about a concrete Action subclass, used solely to read `WorkflowAction`'s own `workflow_id` property for the event payload, not to alter execution behavior.
- **`CORE_SERVICES_VERSION` remains `"0.1.1"`, unchanged by this package.** Per the Founder's standing policy and this package's own explicit Version Policy: the constant already matched the repository's actual release before this package began (see Section 2's Repository Verification Note for the correction that preceded this package).
- **`argus/tests/test_bootstrap.py` (duplicate tree) synchronized, tuple-only**, per the standing Repository Rule introduced in Package 011. This is the only duplicate-tree file touched.
- **Exception base named `DispatcherError`**, matching the `<Subsystem>Error` convention (`SchedulerError`, `IntentError`, `WorkflowError`, `ConversationError`).

## 10. Known Limitations

- The five Version 1 "Initial mappings" will raise `ActionExecutionError` when actually dispatched, until some future package registers real Workflows under their conventional `workflow_id`s (see Section 9).
- `IntentDispatcher` is not wired into `ConversationManager` — `manager.py` was not modified by this package; the two compose only if some future caller explicitly feeds a resolved Intent from one into the other (proven possible, not automatic, by `tests/test_intent_dispatcher.py::ConversationManagerIntegrationTests::test_end_to_end_conversation_manager_intent_flows_into_dispatcher`).
- Mappings are held only in memory; nothing persists across process restarts.
- Only `WorkflowAction` exists as a concrete Action in Version 1; `PluginAction`/`AgentAction`/`ConnectorAction` are architecturally anticipated but not implemented.
- The repository's stray `argus/` duplicate tree (beyond the one explicitly-required `test_bootstrap.py` sync) and legacy pre-Factory files remain unresolved, out of scope per the Founder's explicit repository rules.

## 11. Repository-Derived Package Metrics (measured, not estimated)

Measured via `git diff --stat` against the working tree's unmodified base commit `1df8dbb` (no commit was made — see Section 2):

- Files Created: 9 (6 `argus/dispatcher/*.py`, `factory/packages/012_INTENT_DISPATCHER.md`, 2 new test files)
- Files Modified: 9 (`argus/bootstrap.py`, `argus/events/event_types.py`, `design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`, `factory/ROADMAP.md`, `tests/test_bootstrap.py`, `argus/tests/test_bootstrap.py`, `CHANGELOG.md`, `DEVLOG.md`, `IMPLEMENTATION_REPORT.md`)
- Lines Added: 1,887 / Lines Removed: 92
- Unit Tests: 553 passing in canonical `tests/` (66 new: 19 model + 45 dispatcher + 2 bootstrap)
- Coverage: 99% (Package 012 modules), 98% (full `argus/*`)
- Public Classes: 2 (`WorkflowAction`, `IntentDispatcher`) plus 1 abstract base class (`Action`)
- Public Interfaces: 1 (`IIntentDispatcher`)
- New Dependencies: 0
- External Libraries: 0 (standard library only)
- Architecture Deviations: 0 (see Section 9 for documented, non-architectural deviations)

## 12. Pre-Completion Checklist (per the Founder's explicit checklist)

- ✓ **Bootstrap registration** — `IntentDispatcher(...)` constructed in `bootstrap.py`, registered in the Container as `"intent_dispatcher"`. Confirmed via `test_bootstrap_registers_intent_dispatcher_in_container`.
- ✓ **Service registration** — recorded as a `ServiceDescriptor` (version `"0.1.1"`, the repository's currently released version) alongside all eleven prior core services.
- ✓ **Lifecycle integration** — registered in the Lifecycle Manager as `LifecycleState.REGISTERED`.
- ✓ **Conversation Manager integration** — verified via `ConversationManagerIntegrationTests`: source-inspection proof that `argus/dispatcher/` never imports `argus.conversation`, plus an end-to-end composition test showing a real `ConversationManager`-classified `Intent` flows correctly into `IntentDispatcher.dispatch()`.
- ✓ **Workflow Engine delegation** — verified via `WorkflowEngineDelegationTests`, including that a real `IWorkflowEngine.execute()` call occurs and its result is reflected in the workflow's own state, and that `dispatcher.py` itself never imports `argus.workflow`.
- ✓ **Event Bus integration** — all six dispatch events verified published at the correct points, in order, via `tests/test_intent_dispatcher.py`.
- ✓ **Naming consistency** — `"intent_dispatcher"` verified against the repository's own `CORE_SERVICE_NAMES` convention before implementation.
- ✓ **Regression suite passes** — `python -m unittest discover -s tests` reports `Ran 553 tests ... OK`.
- ✓ **`python main.py` starts cleanly** — exit code 0.
- ✓ **No unintended repository modifications** — confirmed via `git status`/`git diff --stat`; only the 18 files listed in Section 5 were touched, and the one duplicate-tree file modified (`argus/tests/test_bootstrap.py`) was explicitly authorized by the standing Repository Rule.

## 13. Concise Implementation Summary

Package 012 adds `argus/dispatcher/`: an `Action` abstract base class (one method, `execute()`) with `WorkflowAction` as Version 1's sole concrete implementation, a pure-data `DEFAULT_WORKFLOW_IDS` mapping table, and an `IntentDispatcher` that maintains a configurable `IntentType -> Action` registry and resolves+delegates via `dispatch()` — never parsing intents, never running workflow steps, never reasoning, verified structurally by test. `IntentDispatcher` deliberately does not depend on `IWorkflowEngine` directly; that dependency lives entirely inside whichever `WorkflowAction` instances `bootstrap.py` constructs and registers, making the "future Action types without redesigning the dispatcher" requirement literally true. `IIntentDispatcher` inherits `IService`, with `dispatch()` genuinely gated on `RUNNING` — a fifth data point reinforcing ADR-0002's pattern (kept `Proposed`, unchanged). Registered as ArgusOS's twelfth core service. 553 tests pass in `tests/` (66 new), 99%/98% coverage on `argus/dispatcher/`/full `argus/*`. Built and verified entirely within the Founder-supplied repository; no commit, tag, push, or git-history change was made, and `CORE_SERVICES_VERSION` was not advanced, per instruction.

## 14. Architectural Observations

- Five packages in a row (Scheduler, IntentRouter, WorkflowEngine, ConversationManager, IntentDispatcher) have now independently implemented `IService`, and four of the five converge on the identical shape: one gated "do real work" method, N ungated registry methods. The pattern is stable enough across five independently-specified packages that a future ADR-0002 resolution package could reasonably codify it as a required shape, not just a documented tendency.
- This package demonstrates a different DI shape than every prior core service: instead of taking another core service's interface directly (the pattern `ConversationManager` set with `IIntentRouter`/`IWorkflowEngine`), `IntentDispatcher` takes only generic `Action` objects, and the concrete cross-service dependency is pushed one level down, into `WorkflowAction`, constructed exclusively by `bootstrap.py`. This is worth flagging as a second valid DI shape now proven out in this codebase — "depend on the service directly" (Package 011) versus "depend on an abstraction the caller configures with the service" (Package 012) — both work cleanly with the existing `Container`, and future packages needing extensibility across multiple possible backends now have a concrete precedent to follow instead of defaulting to direct dependency by habit.
- `IntentDispatcher` and `ConversationManager` are not wired together by this package — both exist, both can independently produce or consume an `Intent`, but no core service currently owns "take a raw user message all the way through classification, dispatch, and execution automatically." `tests/test_intent_dispatcher.py`'s `ConversationManagerIntegrationTests` proves the composition is *possible* end-to-end, not that it's automatic. This is the same "currently-unowned architectural gap" Package 011's own report flagged for whichever future package would need to close it — Package 012 narrows that gap (dispatch now exists) without closing it (nothing calls dispatch automatically yet), worth flagging again for whichever future package is expected to finish the wiring.
