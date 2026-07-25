# ArgusOS Implementation Report — Package 013: Capability Registry

## 1. Package Overview

Package 013 adds `argus/capability/`, the single source of truth describing everything ArgusOS knows how to do, and revises `argus/dispatcher/` (Package 012) to query it instead of holding its own capability knowledge. `CapabilityRegistry` is a pure metadata store (`register`/`unregister`/`get`/`find_by_intent_type`/`list_capabilities`/`contains`) that performs no execution — its only non-trivial logic is field validation at `register()` time. `IntentDispatcher.resolve()` now returns a `Capability` (queried live from an injected `ICapabilityRegistry`, applying a documented "first enabled match, in registration order" selection policy) instead of an `Action`; `dispatch()` obtains the `Action` a resolved `Capability` describes via an injected `action_factory` callable, never by importing `IWorkflowEngine` directly — preserving Package 012's zero-`argus.workflow`-dependency property in `dispatcher.py` itself. `register_mapping()`/`remove_mapping()`/`list_mappings()` were removed from `IIntentDispatcher` entirely, their responsibility now owned exclusively by `ICapabilityRegistry`. All 553 pre-existing canonical tests still pass (adjusted for the `test_intent_dispatcher.py` rewrite); 605 tests total pass under `python -m unittest discover -s tests`, and `python -m pytest` also passes (693 passed, 38 subtests passed). No pytest-incompatible code anywhere. `python main.py` starts and shuts down cleanly.

## 2. Repository Verification Note

Before writing any code, the uploaded repository was verified fresh against the Founder's four explicit preconditions: it already contains Package 012 (commit `ec2d279`, "Implement Package 012 Intent Dispatcher"), `argus/dispatcher/` is present, and a version marker at or beyond `v0.1.2` exists (git tag `v0.1.2`).

The first upload failed the fourth precondition, "`CORE_SERVICES_VERSION == "0.1.2"`": the repository's `v0.1.2` tag confirmed Package 012 had genuinely been integrated, committed, and released, but `argus/bootstrap.py`'s own `CORE_SERVICES_VERSION` constant still read `"0.1.1"` — the same category of one-release-behind mismatch already seen and corrected before Package 012. Per this package's own explicit "if any verification fails, STOP" instruction, this was reported to the Founder rather than silently corrected or worked around. The Founder corrected the repository directly (a dedicated commit, `a440c77`, "Synchronize repository version with v0.1.2 release") and supplied a corrected upload. Pre-flight verification was re-run against that corrected repository and passed cleanly: `CORE_SERVICES_VERSION == "0.1.2"` matching tag `v0.1.2` (HEAD a clean one-commit descendant of it, diff confirmed to touch only the version string), `python -m pytest` passing (641 passed, 38 subtests), `python -m unittest discover -s tests` passing (553), `python main.py` starting and shutting down cleanly — all confirmed before any Package 013 code was written.

Per the Founder's explicit release rules, this implementation was built, tested, and verified entirely within the supplied repository. No `git commit`, `git tag`, push, or git-history modification of any kind was performed, `CORE_SERVICES_VERSION` was not changed by this package, and this package is not being reported as complete — final validation, integration, release, tagging, and git operations are the Founder's responsibility, to be performed against the live repository after independent regression testing.

## 3. Architectural Rationale

No `design/specifications/CAPABILITY.md` exists — the same situation as Packages 002, 009, 010, 011, and 012. Every structural decision traces to the Founder's explicit work order. The full rationale for each decision below is also recorded in `factory/packages/013_CAPABILITY_REGISTRY.md`'s "Architectural Decisions" section, in the source code's own module docstrings, and is only summarized here.

**Decision 1 — `IntentDispatcher` still does not depend on `IWorkflowEngine`.** `Capability` is pure data, holding no live service reference (matching every value object in this codebase). Translating a Capability's metadata into an executable `Action` is `argus.dispatcher.action.build_action_from_capability()`'s job, called only via an injected `action_factory: Callable[[Capability], Action]` — `bootstrap.py` builds the actual closure via `functools.partial`. `dispatcher.py` itself still never imports `argus.workflow`, verified by the same source-inspection test technique Package 012 established.

**Decision 2 — `argus/capability/` has zero dependency on `argus/dispatcher/`.** `CapabilityRegistry.register()`'s validation (a `"workflow"`-kind capability requires a `workflow_id`) uses a local string constant instead of importing `WorkflowAction`, avoiding a circular import (`argus.capability.registry -> argus.dispatcher.action -> argus.capability.capability`) caught during an early smoke test.

**Decision 3 — `IIntentDispatcher`'s public contract changed.** `register_mapping`/`remove_mapping`/`list_mappings` removed (moved to `ICapabilityRegistry.register`/`unregister`/`list_capabilities`); `resolve(intent)` kept but now returns a `Capability`. A deliberate, explicitly-authorized breaking change to Package 012's interface — the target architecture requires it.

**Decision 4 — `Action` was NOT renamed.** Considered per this package's explicit rename allowance ("ONLY if it meaningfully improves the architecture") and rejected: `Action`'s one-method contract is completely unaffected by this refactor.

## 4. IService Adoption — A Non-Adopter Data Point for ADR-0002

`ICapabilityRegistry` does NOT inherit `IService` — `CapabilityRegistry` is architecturally identical to Knowledge Service (006) and Memory Service (007): fully usable the instant it is constructed, nothing for `start()`/`stop()` to meaningfully gate. This is the first new deliberate non-adopter since Memory Service, appended to `design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md` as evidence the proposed criterion works as a design-time filter, not merely a post-hoc classification. Its Status remains `Proposed`, per standing instruction.

## 5. Directory Tree (files touched)

```
argus/
    capability/
        __init__.py
        capability.py
        exceptions.py
        interfaces.py
        registry.py
    dispatcher/
        __init__.py                        (modified)
        action.py                          (modified - + build_action_from_capability)
        dispatcher.py                      (modified - constructor/resolve()/dispatch() rewritten)
        exceptions.py                      (modified - NoCapabilityError, etc.)
        interfaces.py                      (modified - resolve() now returns Capability)
        mapping.py                         (unchanged - reused as-is)
    bootstrap.py                           (modified)
    events/
        event_types.py                     (modified)
design/
    decisions/
        0002_ISERVICE_ADOPTION_CRITERION.md   (modified — appended finding)
factory/
    packages/
        013_CAPABILITY_REGISTRY.md         (new)
    ROADMAP.md                              (modified)
tests/
    test_bootstrap.py                       (modified)
    test_capability.py                      (new)
    test_capability_registry.py             (new)
    test_dispatcher.py                      (modified)
    test_intent_dispatcher.py               (modified - rewritten)
argus/tests/test_bootstrap.py               (modified — CORE_SERVICE_NAMES tuple only, per explicit instruction)
CHANGELOG.md                                (modified)
DEVLOG.md                                   (modified)
IMPLEMENTATION_REPORT.md                    (replaced — this file)
```

No file outside this list was created, deleted, moved, or modified. `argus/lifecycle/test_lifecycle.py`, `argus/CHANGELOG.md`, `argus/DEVLOG.md`, `argus/IMPLEMENTATION_REPORT.md`, `argus/factory/`, and every legacy pre-Factory file were left completely untouched.

## 6. Integration Notes

- `CapabilityRegistry(event_bus)` — constructed in `bootstrap.py` immediately after the Conversation Manager, depending only on the Event Bus. Five `Capability` instances are registered immediately after construction, one per `DEFAULT_WORKFLOW_IDS` entry (the same table Package 012 built), giving descriptive `name`/`description` fields derived programmatically from each `IntentType`.
- `IntentDispatcher(event_bus, capability_registry, action_factory)` — constructed immediately after `CapabilityRegistry`, with `action_factory = functools.partial(build_action_from_capability, workflow_engine=workflow_engine)`. This is now the 14th core service constructed (`CapabilityRegistry` is the 13th), one slot later than Package 012's registration order, since `IntentDispatcher` now depends on `CapabilityRegistry`.
- Both are registered in the Container (`"capability_registry"`, `"intent_dispatcher"`), in the Service Registry as `ServiceDescriptor`s (version `"0.1.2"`, the repository's currently released version — see Section 2), and in the Lifecycle Manager as `LifecycleState.REGISTERED` — matching the treatment of all eleven prior core services. `CapabilityRegistry` has no gated method to speak of (not an `IService` adopter); `IntentDispatcher.dispatch()` remains gated on `RUNNING`, unchanged from Package 012.
- `argus/events/event_types.py` extended with two new members: `CAPABILITY_REGISTERED`, `CAPABILITY_UNREGISTERED`.
- Naming (`"capability_registry"`) verified against the repository's own `tests/test_bootstrap.py::CORE_SERVICE_NAMES` convention before implementation.
- The repository's pre-existing, known stray duplicate `argus/tests/test_bootstrap.py` had its `CORE_SERVICE_NAMES` tuple synchronized with `"capability_registry"` added, per the standing Repository Rule introduced in Package 011 — and only that tuple.

## 7. Test Results

Canonical suite (`tests/`):
```
python -m unittest discover -s tests
Ran 605 tests in 0.065s
OK
```

Per this package's explicit testing instruction:
```
python -m pytest
693 passed, 38 subtests passed in 0.55s
```

The synchronized duplicate `argus/tests/` also verified passing standalone (unaffected by the one-line sync):
```
python -m unittest discover -s argus/tests -p "test_*.py"
Ran 64 tests in 0.021s
OK
```

`python main.py`:
```
2026-07-25 14:56:22 [INFO] argus: ArgusOS application started.
2026-07-25 14:56:22 [INFO] argus: ArgusOS application shutting down.
```
Exit code 0.

## 8. Coverage Summary

Measured with `coverage.py`, `python -m coverage run -m unittest discover -s tests`:

| Module | Stmts | Miss | Cover |
|---|---|---|---|
| `argus/bootstrap.py` | 58 | 0 | 100% |
| `argus/capability/__init__.py` | 5 | 0 | 100% |
| `argus/capability/capability.py` | 18 | 0 | 100% |
| `argus/capability/exceptions.py` | 4 | 0 | 100% |
| `argus/capability/interfaces.py` | 17 | 0 | 100% |
| `argus/capability/registry.py` | 60 | 0 | 100% |
| `argus/dispatcher/__init__.py` | 6 | 0 | 100% |
| `argus/dispatcher/action.py` | 28 | 1 | 96% (unreachable `raise NotImplementedError` in the abstract `Action.execute()` stub, same accepted pattern as Package 012) |
| `argus/dispatcher/dispatcher.py` | 74 | 0 | 100% |
| `argus/dispatcher/exceptions.py` | 5 | 0 | 100% |
| `argus/dispatcher/interfaces.py` | 10 | 0 | 100% |
| `argus/dispatcher/mapping.py` | 4 | 0 | 100% |

Package 013 total (`argus/capability/*` + touched `argus/dispatcher/*`): 289 statements, 99% covered (288/289). Full `argus/*` coverage: 99% (measured across the entire repository).

## 9. Engineering Decisions / Deviations from the Work Order

- **`IntentDispatcher` constructor signature changed**: `(event_bus, capability_registry, action_factory)`, not `(event_bus, workflow_engine)` or `(event_bus)` with post-construction `register_mapping()` calls. See Section 3, Decision 1.
- **`ICapabilityRegistry` does not inherit `IService`** — a deliberate, ADR-0002-driven choice, not an oversight. See Section 4.
- **A local string constant, not an import of `WorkflowAction`, guards `CapabilityRegistry.register()`'s `"workflow"`-kind validation** — avoids a circular import; see Section 3, Decision 2, and `argus/capability/registry.py`'s own comment at `_WORKFLOW_ACTION_KIND`.
- **`register_mapping`/`remove_mapping`/`list_mappings` removed from `IIntentDispatcher`; `resolve()`'s return type changed from `Action` to `Capability`.** A deliberate, explicitly-authorized breaking change to Package 012's public interface. See Section 3, Decision 3.
- **`NoMappingError` renamed to `NoCapabilityError`; `DuplicateMappingError`/`MappingNotFoundError` removed from `argus/dispatcher/exceptions.py`** (their responsibility moved to `argus.capability.exceptions`).
- **`Action` was NOT renamed**, despite this package's explicit rename allowance — considered and rejected as purely cosmetic. See Section 3, Decision 4.
- **No new event for "capability resolved"** — `ActionResolved`'s payload grew a `capability_id` field instead, honoring "do not introduce unnecessary events." See `factory/packages/013_CAPABILITY_REGISTRY.md`'s Events section.
- **`CORE_SERVICES_VERSION` remains `"0.1.2"`, unchanged by this package.** Per the Founder's standing policy and this package's own explicit Version Policy.
- **`argus/tests/test_bootstrap.py` (duplicate tree) synchronized, tuple-only**, per the standing Repository Rule introduced in Package 011.
- **`argus/dispatcher/mapping.py` left completely unchanged** — reused as-is per this package's own "Populate Version 1 using the existing workflow mappings introduced in Package 012" requirement.

## 10. Known Limitations

- The five Version 1 Capabilities reference `workflow_id`s with no real Workflow registered against them anywhere in the repository — dispatching any of them raises `ActionExecutionError` until some future package registers real workflows under those ids. Unchanged from Package 012.
- `find_by_intent_type()` returns disabled capabilities too (a pure filter, by design); callers other than `IntentDispatcher.resolve()` must apply their own enabled-filtering if needed.
- Capabilities are held only in memory; nothing persists across process restarts.
- Only `action_kind == "workflow"` is supported by `build_action_from_capability()` in Version 1.
- The repository's stray `argus/` duplicate tree (beyond the one explicitly-required `test_bootstrap.py` sync) and legacy pre-Factory files remain unresolved, out of scope per the Founder's explicit repository rules.

## 11. Repository-Derived Package Metrics (measured, not estimated)

Measured via `git diff --stat` against the working tree's unmodified base commit `a440c77` (no commit was made — see Section 2):

- Files Created: 8 (5 `argus/capability/*.py`, `factory/packages/013_CAPABILITY_REGISTRY.md`, 2 new test files)
- Files Modified: 16 (`argus/bootstrap.py`, 5 `argus/dispatcher/*.py` files, `argus/events/event_types.py`, `design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`, `factory/ROADMAP.md`, `tests/test_bootstrap.py`, `argus/tests/test_bootstrap.py`, `tests/test_dispatcher.py`, `tests/test_intent_dispatcher.py`, `CHANGELOG.md`, `DEVLOG.md`, `IMPLEMENTATION_REPORT.md`)
- Lines Added: 2,130 / Lines Removed: 554
- Unit Tests: 605 passing in canonical `tests/` (net +52 vs. Package 012's 553: +16 `test_capability.py`, +37 `test_capability_registry.py`, +4 `test_dispatcher.py` [19->23], -7 `test_intent_dispatcher.py` [45->38, rewritten for the new IntentDispatcher interface], +2 `test_bootstrap.py` [15->17])
- Coverage: 99% (Package 013 modules), 99% (full `argus/*`)
- Public Classes: 2 (`Capability`, `CapabilityRegistry`)
- Public Interfaces: 1 (`ICapabilityRegistry`)
- New Dependencies: 0
- External Libraries: 0 (standard library only)
- Architecture Deviations: 0 (see Section 9 for documented, non-architectural deviations)

## 12. Pre-Completion Checklist (per the Founder's explicit checklist)

- ✓ **Bootstrap registration** — `CapabilityRegistry(...)` and revised `IntentDispatcher(...)` both constructed in `bootstrap.py`, registered in the Container as `"capability_registry"`/`"intent_dispatcher"`. Confirmed via `test_bootstrap_registers_capability_registry_in_container`.
- ✓ **Service registration** — both recorded as `ServiceDescriptor`s (version `"0.1.2"`) alongside all eleven prior core services.
- ✓ **Lifecycle integration** — both registered in the Lifecycle Manager as `LifecycleState.REGISTERED`.
- ✓ **Conversation Manager integration** — verified via `ConversationManagerIntegrationTests`: source-inspection proof `argus/dispatcher/` never imports `argus.conversation`, plus an end-to-end composition test.
- ✓ **Workflow Engine delegation** — verified via `WorkflowEngineDelegationTests`, including that a real `IWorkflowEngine.execute()` call occurs via the injected `action_factory`, and that `dispatcher.py` itself never imports `argus.workflow` or the concrete `CapabilityRegistry`.
- ✓ **Event Bus integration** — all six dispatch events and both new capability events verified published at the correct points, in order, via `tests/test_intent_dispatcher.py` and `tests/test_capability_registry.py`.
- ✓ **Naming consistency** — `"capability_registry"` verified against the repository's own `CORE_SERVICE_NAMES` convention before implementation.
- ✓ **Regression suite passes** — `python -m unittest discover -s tests` reports `Ran 605 tests ... OK`; `python -m pytest` reports `693 passed, 38 subtests passed`.
- ✓ **`python main.py` starts cleanly** — exit code 0.
- ✓ **No unintended repository modifications** — confirmed via `git status`/`git diff --stat`; only the files listed in Section 5 were touched.
- ✓ **`CORE_SERVICES_VERSION` not modified** — confirmed still `"0.1.2"`.
- ✓ **No commit created** — confirmed via `git log` (HEAD unchanged at `a440c77`).
- ✓ **No tag created** — confirmed via `git tag -l` (unchanged).
- ✓ **Repository ready for integration and release** — all regression, smoke, and pyflakes checks pass locally; final integration, version bump, commit, and tag remain the Founder's responsibility.

## 13. Concise Implementation Summary

Package 013 adds `argus/capability/`: an immutable `Capability` value object, `ICapabilityRegistry` (a plain ABC, deliberately not an `IService`), and `CapabilityRegistry`, a pure metadata store with field validation at `register()` time and `CapabilityRegistered`/`CapabilityUnregistered` event publication. `argus/dispatcher/` is revised so `IntentDispatcher` holds no capability knowledge of its own: `resolve()` now queries the injected `ICapabilityRegistry` live and returns a `Capability` (applying a documented first-enabled-match selection policy); `dispatch()` obtains an `Action` via an injected `action_factory` built from the new `build_action_from_capability()` function, preserving `dispatcher.py`'s zero-`argus.workflow`-dependency property from Package 012. `register_mapping`/`remove_mapping`/`list_mappings` were removed from `IIntentDispatcher` as a deliberate, authorized breaking change. `CapabilityRegistry` is registered as ArgusOS's 13th core service (a new non-`IService`-adopter data point for ADR-0002); `IntentDispatcher` is now the 14th. 605 tests pass in `tests/` (`python -m pytest` also passes: 693 passed, 38 subtests), 99% coverage across all Package 013 modules. Built and verified entirely within the Founder-supplied repository; no commit, tag, push, or git-history change was made, and `CORE_SERVICES_VERSION` was not advanced, per instruction.

## 14. Architectural Observations

- This package is the first to demonstrate a three-package refactor chain within this codebase's history: Package 011 established the "delegate through the target service's own public interface" pattern, Package 012 established the "opaque injected factory to avoid a hard backend dependency" pattern, and Package 013 combines both simultaneously (`IntentDispatcher` depends on `ICapabilityRegistry`'s interface directly, per Package 011's pattern, while obtaining `Action`s via an opaque `action_factory`, per Package 012's pattern) to insert a new layer without weakening either prior package's own decoupling guarantees. Worth flagging as evidence that these two patterns compose cleanly, not just individually.
- `CapabilityRegistry` is architecturally closer to Knowledge/Memory Service (006/007) than to any of the five `IService` adopters (008-012) that immediately preceded it in package order - a useful reminder, recorded explicitly in ADR-0002's own newly appended finding, that adjacency in package numbering does not imply architectural similarity, and that ADR-0002's criterion needs to be re-applied fresh for every new service rather than pattern-matched against whatever the most recent few packages happened to do.
- The "currently-unowned architectural gap" flagged in both Package 011's and Package 012's own reports - nothing yet takes a raw user message all the way through classification, capability resolution, and execution automatically - remains open after this package. `ConversationManager` still is not wired to call `IntentDispatcher`; both can now be composed manually (proven by `ConversationManagerIntegrationTests`), but no core service owns that composition. This continues to be worth flagging for whichever future package is expected to close it.
