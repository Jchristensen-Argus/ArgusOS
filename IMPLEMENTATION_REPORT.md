# ArgusOS Implementation Report — Package 009: Intent Router

## 1. Package Overview

Package 009 adds `argus/intent/`, ArgusOS's first deterministic text-classification and routing layer. `parse_text()` classifies raw text into one of five `IntentType` values (`QUESTION`/`COMMAND`/`MEMORY`/`SCHEDULE`/`UNKNOWN`) using fixed keyword lists and a fixed precedence order — no AI, no machine learning, no external libraries, no regex. `IntentRouter` wraps every classification in an immutable `Intent` value object, publishes `IntentParsed` on every `parse()` call (including `UNKNOWN` results), and publishes `IntentRouted` on every `route()` call as its *only* invocation mechanism — no service is ever called directly. `register_handler()` is implemented as filtered subscription sugar over the Event Bus, with per-handler failure isolation (a failing handler publishes `IntentFailed` rather than propagating or blocking other handlers). `IntentRouter` is registered as ArgusOS's ninth core service. All 281 pre-existing canonical tests still pass; 72 new tests were added (353 total in `tests/`), all passing under `python -m unittest discover -s tests`. No pytest anywhere in this package. `python main.py` starts and shuts down cleanly.

## 2. Regeneration Note

This package was implemented twice. The first attempt was built against a reconstructed development workspace, not the Founder's live repository. When the Founder reported their live repository finished Package 008 with 369 passing tests against my reported 353 (281 baseline + 72 new), I stopped, requested the live repository directly, and compared every canonical file this package touches against it before writing anything further.

The comparison found the discrepancy was not caused by any tests being removed. The Founder's live repository contains a stray, stale duplicate of parts of itself nested inside `argus/` — `argus/tests/` (4 files, 64 tests, frozen at a pre-Package-008 snapshot), `argus/lifecycle/test_lifecycle.py` (24 tests, an exact duplicate of `tests/test_lifecycle.py`), plus duplicate `argus/CHANGELOG.md`, `argus/DEVLOG.md`, `argus/IMPLEMENTATION_REPORT.md`, and `argus/factory/` — left over from an earlier merge. A `.pytest_cache/` present in the repository confirmed the mechanism directly: its cached node-id list contains exactly 369 entries, matching 281 canonical + 24 + 64 duplicated. Every canonical file this package actually modifies (`argus/bootstrap.py`, `argus/events/event_types.py`, `tests/test_bootstrap.py`, `CHANGELOG.md`, `DEVLOG.md`, `factory/ROADMAP.md`, `design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`) was verified byte-identical between the reconstructed workspace and the live repository by direct diff, so this package's actual implementation is unchanged between the two attempts — only this report and the delivery process reflect the correction.

Per the Founder's explicit instruction, the stray duplicate and legacy pre-Factory files were left untouched as out of scope for this package, reserved for a dedicated future cleanup package. This package modifies only: `argus/` (adding `argus/intent/`, modifying `argus/bootstrap.py` and `argus/events/event_types.py`), `tests/`, `design/`, `factory/`, `CHANGELOG.md`, `DEVLOG.md`, and this file.

## 3. Architectural Rationale

Unlike Packages 007 and 008, Package 009's scope was fully specified by the Founder's own work order rather than derived from a `design/specifications/` dependency audit — no `design/specifications/INTENT_ROUTER.md` exists in the repository (the same situation Package 002/Bootstrap was in). Every structural decision below therefore traces to an explicit line in that work order, not an invented architecture.

The one genuine design problem the work order raised implicitly rather than explicitly: `register_handler(intent_name, handler)` is required as a first-class method, and separately, routing must go through "Intent → Event Bus → Interested services respond," with no direct service invocation. Read literally, these look like they could conflict — does `register_handler` provide a second, direct dispatch path alongside the Event Bus? Resolved by making `register_handler` pure sugar over `IEventBus.subscribe()`: it builds an adapter that subscribes to `IntentRouted`, filters by intent name, reconstructs the `Intent` from the event payload, and invokes the handler. `route()` itself has exactly one invocation mechanism — `self._event_bus.publish(...)` — and never touches a handler directly, at any point. This is verified structurally by two tests, not just asserted in a docstring: one confirms a handler registered *after* a `route()` call never fires (proving there's no lazy secondary dispatch), and another confirms a handler registered on an `IntentRouter` sharing no Event Bus with the router that called `route()` is never invoked (proving there's no direct call hiding behind the Event Bus abstraction).

## 4. IService Adoption — A Second Data Point for ADR-0002

Per the Founder's standing instruction (leave `IService` unchanged, use real adopters as an empirical proving ground, keep ADR-0002 `Proposed`), `IntentRouter` is this package's second real `IService` implementer after Scheduler (Package 008). It confirms a different facet of the same concern.

Scheduler showed two things at once: the duplicate-state risk is real, *and* `IService` can carry genuine behavior (`tick()` is gated on `RUNNING`). `IntentRouter` isolates the first finding from the second — it tracks its own `LifecycleState` the same way Scheduler does, to satisfy `status()`, but none of `parse()`, `route()`, or `register_handler()` are gated by that state at all. Calling `parse()` on a router that was never started behaves identically to calling it on one that has been started and stopped. `IService` is implemented here purely to satisfy the work order's explicit interface requirement, not because `IntentRouter` has any phased behavior for `start()`/`stop()` to enable or disable. This is documented directly in `router.py`'s module docstring and asserted by a dedicated test (`test_parse_route_and_register_handler_are_not_gated_by_lifecycle_state`), so that if a future revision *does* add gating, the change is forced to be deliberate and visible rather than an accidental regression.

This finding has been appended to ADR-0002 (`design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`) as a second empirical entry, not used to revise the ADR's own criterion or its `Proposed` status. See Section 9 (ADR Recommendation) below.

## 5. Directory Tree (files touched)

```
argus/
    intent/
        __init__.py
        exceptions.py
        intent.py
        interfaces.py
        parser.py
        router.py
    bootstrap.py                       (modified)
    events/
        event_types.py                 (modified)
design/
    decisions/
        0002_ISERVICE_ADOPTION_CRITERION.md   (modified — appended finding)
factory/
    packages/
        009_INTENT_ROUTER.md           (new)
    ROADMAP.md                          (modified)
tests/
    test_bootstrap.py                   (modified)
    test_intent.py                      (new)
    test_intent_parser.py               (new)
    test_intent_router.py               (new)
CHANGELOG.md                            (modified)
DEVLOG.md                               (modified)
IMPLEMENTATION_REPORT.md                (replaced — this file)
```

No file outside this list was created, deleted, moved, or modified. In particular, `argus/tests/`, `argus/lifecycle/test_lifecycle.py`, `argus/CHANGELOG.md`, `argus/DEVLOG.md`, `argus/IMPLEMENTATION_REPORT.md`, `argus/factory/`, and every legacy pre-Factory file (`argus/ai.py`, `argus/brain.py`, `argus/commands.py`, `argus/conversation.py`, `argus/identity.py`, `argus/shell.py`, `argus/memory.py`) were left completely untouched, per the Founder's explicit instruction.

## 6. Integration Notes

- `IntentRouter(event_bus: IEventBus)` — constructed in `bootstrap.py` immediately after Scheduler, since it depends only on the Event Bus (already constructed by that point).
- Registered in the Container as `"intent_router"`, in the Service Registry as a `ServiceDescriptor` (version `"0.0.9"`), and in the Lifecycle Manager as `LifecycleState.REGISTERED` — exactly matching the treatment of all eight prior core services, including Scheduler. Not initialized or started (see Section 4).
- `argus/events/event_types.py` extended with `INTENT_PARSED`, `INTENT_ROUTED`, `INTENT_FAILED` — no existing members reused.
- Fully backward compatible: no existing public interface, method signature, or stored data format was changed. `CORE_SERVICES_VERSION` bumped `"0.0.8"` → `"0.0.9"`, matching the version-target convention established in every prior package.
- Deliberately does **not** import or reference `argus.knowledge`, `argus.memory`, or `argus.scheduler` anywhere in `argus/intent/` — loose coupling is structural (verified by `test_router_module_does_not_import_other_core_services`, which inspects `router.py`'s own source), not just a stated intention.

## 7. Test Results

Canonical suite (`tests/` only, the scope this package modifies):
```
python -m unittest discover -s tests
Ran 353 tests in 0.035s
OK
```

A bare `python -m unittest discover` from the repository root additionally picks up the pre-existing, out-of-scope duplicate at `argus/lifecycle/test_lifecycle.py` (24 tests, untouched by this package):
```
python -m unittest discover
Ran 377 tests in 0.033s
OK
```
This is expected, not a regression — see Section 2.

`python main.py`:
```
2026-07-24 12:43:56 [INFO] argus: ArgusOS application started.
2026-07-24 12:43:56 [INFO] argus: ArgusOS application shutting down.
```
Exit code 0.

## 8. Coverage Summary

Measured with `coverage.py`, `python -m coverage run -m unittest discover -s tests`:

| Module | Stmts | Miss | Cover |
|---|---|---|---|
| `argus/bootstrap.py` | 43 | 0 | 100% |
| `argus/intent/__init__.py` | 6 | 0 | 100% |
| `argus/intent/exceptions.py` | 4 | 0 | 100% |
| `argus/intent/intent.py` | 23 | 0 | 100% |
| `argus/intent/interfaces.py` | 11 | 0 | 100% |
| `argus/intent/parser.py` | 53 | 0 | 100% |
| `argus/intent/router.py` | 70 | 0 | 100% |

Package 009 total (`argus/intent/*`): 167 statements, 100% covered. Full `argus/*` coverage: 1,131 statements, 98% covered (24 missed, all pre-existing untested OS-failure branches / unreachable ABC stubs, none introduced by this package).

## 9. Engineering Decisions / ADR Recommendation

- **`register_handler` implemented as Event-Bus-subscription sugar, not a second dispatch path.** See Section 3.
- **`IService` adopted per explicit instruction, honestly documented as ungated.** See Section 4. **ADR Recommendation:** unchanged from Package 008's finding — a dedicated architectural package is still warranted to resolve `IService.status()`'s duplication, and this package's finding additionally suggests that package should decide whether `IService` adoption ought to require a genuine behavioral gate as a precondition, not just a self-tracked state variable satisfying the interface.
- **Exception base named `IntentError`**, matching the `<Subsystem>Error` naming convention already used for `SchedulerError`, `MemoryServiceError`, `KnowledgeError`.
- **No punctuation normalization in `parser.py`.** A keyword immediately followed by punctuation (e.g. `"note: buy milk"`) does not satisfy the word-boundary check and falls through to weak-confidence substring matching with no `subject` entity extracted. Documented as a Known Limitation rather than fixed, since the work order's "simple rule-based parsing only" constraint does not call for punctuation handling.

## 10. Deviations from the Work Order

None in implemented behavior. `argus/bootstrap.py`, `argus/events/event_types.py`, and `tests/test_bootstrap.py` were modified (not just added-to) to satisfy the work order's own explicit Bootstrap Integration and Events requirements — the same procedural pattern flagged in every prior package's report since Package 006. `factory/ROADMAP.md` was also updated to add checklist entries for both Intent Router (this package) and Scheduler (Package 008, whose ROADMAP.md update was confirmed absent from the live repository by direct diff) — a small, pre-existing documentation gap, fixed here rather than left inconsistent.

## 11. Known Limitations

- `IntentRouter`'s `IService` implementation has no genuine behavioral gate (see Section 4): `parse()`/`route()`/`register_handler()` behave identically regardless of lifecycle state.
- No punctuation normalization in classification (see Section 9).
- Confidence is limited to three fixed constants (1.0 strong / 0.6 weak / 0.0 no-match) — no finer-grained scoring.
- `register_handler()`'s duplicate check is exact `(intent_name, handler)` object identity; two distinct callables with identical behavior both register successfully.
- The repository's stray `argus/` duplicate tree and legacy pre-Factory files remain unresolved, out of scope for this package per the Founder's explicit instruction; reserved for a dedicated cleanup package. See Section 2.

## 12. Repository-Derived Package Metrics (measured, not estimated)

- Files Created: 10 (6 `argus/intent/*.py`, `factory/packages/009_INTENT_ROUTER.md`, 3 new test files)
- Files Modified: 7 (`argus/bootstrap.py`, `argus/events/event_types.py`, `design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`, `factory/ROADMAP.md`, `tests/test_bootstrap.py`, `CHANGELOG.md`, `DEVLOG.md`)
- Lines Added: 1,600 / Lines Removed: 32 (measured via `git diff --stat`, staged against the live repository's commit `bd30e29`)
- Unit Tests: 353 passing in canonical `tests/` (72 new: 71 intent-specific + 1 bootstrap)
- Coverage: 100% (Package 009 modules), 98% (full `argus/*`)
- Public Classes: 3 (`Intent`, `ParsedText`, `IntentRouter`) plus 1 Enum (`IntentType`)
- Public Interfaces: 1 (`IIntentRouter`)
- New Dependencies: 0
- External Libraries: 0 (standard library only)
- Architecture Deviations: 0

## 13. Pre-Completion Checklist (per the Founder's explicit 7 points)

1. **Bootstrap registration verified** — `IntentRouter(event_bus=event_bus)` constructed in `bootstrap.py`, registered in the Container as `"intent_router"`. Confirmed via `test_bootstrap_registers_intent_router_in_container`.
2. **Lifecycle registration verified** — registered in both the Service Registry (`ServiceDescriptor`, version `"0.0.9"`) and the Lifecycle Manager (`LifecycleState.REGISTERED`), alongside all eight prior core services. Confirmed via `test_bootstrap_registers_core_services_in_service_registry` and `test_core_services_report_registered_lifecycle_state`.
3. **Service naming consistency verified** — registered as `"intent_router"`, confirmed against the live repository's own `tests/test_bootstrap.py::CORE_SERVICE_NAMES` (`"scheduler"`, `"memory_service"`, `"knowledge_service"`) before implementation, not assumed.
4. **Both test suites addressed** — only `tests/` is canonical; `argus/tests/` is the confirmed stray duplicate described in Section 2 and was left untouched, not extended, per instruction.
5. **All imports verified** — `python3 -m pyflakes` clean across every new and modified file in this live repository.
6. **All regression tests verified passing** — `python -m unittest discover -s tests` reports `Ran 353 tests ... OK`; `python main.py` starts and shuts down cleanly with exit code 0.
7. **Concise implementation summary** — see below.

## 14. Concise Implementation Summary

Package 009 adds `argus/intent/` to the Founder's live ArgusOS repository: a deterministic, keyword-based text classifier (`parse_text`) and an `IntentRouter` that wraps classifications in immutable `Intent` objects, routes exclusively through the Event Bus (`IntentParsed`/`IntentRouted`/`IntentFailed`), and offers `register_handler()` as pure Event-Bus-subscription sugar with per-handler failure isolation. `IIntentRouter` inherits `IService`, making `IntentRouter` a second real adopter alongside Scheduler; unlike Scheduler, none of its methods are gated by lifecycle state, a finding appended to ADR-0002 (kept `Proposed`, unchanged). Registered as ArgusOS's ninth core service, `REGISTERED`-only. This package was regenerated once after a test-count discrepancy was traced to a pre-existing, out-of-scope stray duplicate directory structure in the live repository (Section 2) — not to any defect in the implementation itself, which was verified byte-identical across both attempts for every canonical file touched. 353 tests pass in `tests/` (72 new), 100% coverage on every new module, `python main.py` starts and shuts down cleanly. Only canonical locations (`argus/`, `tests/`, `design/`, `factory/`, `CHANGELOG.md`, `DEVLOG.md`, `IMPLEMENTATION_REPORT.md`) were modified; all duplicate and legacy files were left untouched, per instruction.
