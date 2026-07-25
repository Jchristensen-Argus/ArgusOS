# ArgusOS Implementation Report — Package 014: Plugin Manager

## 1. Package Overview

Package 014 adds `argus/plugins/`, the central mechanism for extending ArgusOS without modifying the core application. `PluginManager` is a pure metadata-and-lifecycle store (`register`/`unregister`/`enable`/`disable`/`get`/`list_plugins`/`list_exported_capabilities`/`contains`) that performs no execution and no intent dispatch — its only non-trivial logic is field validation at `register()` time and the `enabled`-flag replace at `enable()`/`disable()` time. `Plugin` is an immutable value object describing one installable extension: `id`, `name`, `version`, `author`, `description`, `enabled`, `exported_capabilities` (a tuple of `Capability` instances), and `metadata`. `PluginManager` is registered as ArgusOS's 14th core service, constructed immediately after the Capability Registry, and bootstrap registers one built-in "Core Workflows" `Plugin` whose `exported_capabilities` are the same five `Capability` instances Package 013 already registered with the Capability Registry — the identical objects, not copies, so behavior is unchanged and nothing is registered twice. `argus/dispatcher/`, `argus/capability/`, and `argus/workflow/` are untouched by this package; the target architecture diagram's "Action -> Plugin Manager -> Workflow" positioning is treated as directional for a future version, not a Version 1 wiring requirement — see Section 3. All 605 pre-existing canonical tests still pass unchanged; 674 tests total pass under `python -m unittest discover -s tests`, and `python -m pytest` also passes (762 passed, 38 subtests passed). `python main.py` starts and shuts down cleanly.

## 2. Repository Verification Note

Before writing any code, the uploaded repository ("ArgusOS (13).zip") was verified fresh against the Founder's four explicit preconditions. Unlike the two prior packages, all four passed on the first attempt, with no corrected re-upload required:

- Package 013 (Capability Registry) present: `argus/capability/` contains all five expected files.
- HEAD (`6cc70f6`, "Synchronize repository version with v0.1.3 release") confirmed a clean descendant of tag `v0.1.3` via `git merge-base --is-ancestor v0.1.3 HEAD`; `git diff 649ca09..HEAD --stat` (where `649ca09` is the commit `v0.1.3` itself points to, "Implement Package 013 Capability Registry") confirmed the one intervening commit touches only `argus/bootstrap.py`, 1 insertion/1 deletion — a clean version-only sync.
- `python -m pytest` passing (693 passed, 38 subtests) and `python -m unittest discover -s tests` passing (605), before any Package 014 code was written.
- `python main.py` starting and shutting down cleanly (exit 0).
- `CORE_SERVICES_VERSION == "0.1.3"` confirmed at `argus/bootstrap.py`.

One cosmetic, non-blocking observation: the work order's own pre-flight step 1 named "ArgusOS(13)updated.zip," while the actual uploaded filename was "ArgusOS (13).zip" (no "updated" suffix) — almost certainly because the Founder applied the version-sync correction before this upload rather than after a reported mismatch, unlike the previous two packages. Since every substantive verification check passed cleanly, this was not treated as a pre-flight failure.

Per the Founder's explicit release rules, this implementation was built, tested, and verified entirely within the supplied repository. No `git commit`, `git tag`, push, or git-history modification of any kind was performed, `CORE_SERVICES_VERSION` was not changed by this package, and this package is not being reported as complete — final validation, integration, release, tagging, and git operations are the Founder's responsibility, to be performed against the live repository after independent regression testing.

## 3. Architectural Rationale

No `design/specifications/PLUGIN.md` exists — the same situation as Packages 002, 009, 010, 011, 012, and 013. Every structural decision traces to the Founder's explicit work order. The full rationale for each decision below is also recorded in `factory/packages/014_PLUGIN_MANAGER.md`'s "Architectural Decisions" section, in the source code's own module docstrings, and is only summarized here.

**Decision 1 — the dispatch path is untouched.** The work order's target-architecture diagram places Plugin Manager between Action and Workflow, but every substantive section describes it purely in terms of discovery/registration/lifecycle/metadata, and explicitly states "Plugins are NOT required to execute real business logic yet" and "It is NOT responsible for dispatching intents." Read as directional/aspirational, not a Version 1 wiring requirement — confirmed by `git diff --stat` showing no changes to `argus/dispatcher/`, `argus/workflow/`, or `argus/capability/`.

**Decision 2 — `Plugin.exported_capabilities` holds live `Capability` objects.** Required for "expose those capabilities so they can later be registered with the Capability Registry" to be directly actionable by a caller. Since `Capability` is already immutable, holding direct references is safe — a one-way, data-only dependency (`argus/plugins/` -> `argus/capability/capability.py`), never on `argus/capability/registry.py`.

**Decision 3 — bootstrap wraps the same five Capability instances, not copies.** `plugin_manager`'s built-in "Core Workflows" plugin exports `tuple(capability_registry.list_capabilities())` directly, so nothing is registered twice with the Capability Registry and "Behavior should remain unchanged" holds literally.

**Decision 4 — `enable()`/`disable()` are unconditional registry operations, not IService lifecycle methods.** Both always replace-and-publish regardless of prior state, matching `Scheduler.pause()`/`resume()`'s (Package 008) precedent for per-item lifecycle mutation that implies nothing about the owning manager's own runtime state.

**Decision 5 — no plugin-discovery machinery was added.** Version 1 scope is registration-time discovery (a caller constructs and registers a `Plugin`); no filesystem/entry-point scanning or dynamic import machinery, per the work order's explicit "avoid introducing unnecessary abstraction" instruction.

## 4. IService Adoption — A Second Consecutive Non-Adopter Data Point for ADR-0002

`IPluginManager` does NOT inherit `IService` — `PluginManager` is architecturally identical to Knowledge Service (006), Memory Service (007), and Capability Registry (013): fully usable the instant it is constructed, nothing for `start()`/`stop()` to meaningfully gate. `enable()`/`disable()` were explicitly considered and rejected as lifecycle-phase candidates, since they mutate an individual Plugin's flag, not the manager's own runtime state. This is the second consecutive new deliberate non-adopter (following Capability Registry, 013), appended to `design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md` as evidence the proposed criterion continues to work as a design-time filter even against lifecycle-sounding method names. Its Status remains `Proposed`, per standing instruction.

## 5. Directory Tree (files touched)

```
argus/
    plugins/
        __init__.py                        (new)
        plugin.py                          (new)
        manager.py                         (new)
        interfaces.py                      (new)
        exceptions.py                      (new)
    bootstrap.py                           (modified)
    events/
        event_types.py                     (modified)
design/
    decisions/
        0002_ISERVICE_ADOPTION_CRITERION.md   (modified — appended finding)
factory/
    packages/
        014_PLUGIN_MANAGER.md              (new)
    ROADMAP.md                              (modified)
tests/
    test_bootstrap.py                       (modified)
    test_plugin.py                          (new)
    test_plugin_manager.py                  (new)
argus/tests/test_bootstrap.py               (modified — CORE_SERVICE_NAMES tuple only, per explicit instruction)
CHANGELOG.md                                (modified)
DEVLOG.md                                   (modified)
IMPLEMENTATION_REPORT.md                    (replaced — this file)
```

No file outside this list was created, deleted, moved, or modified. `argus/dispatcher/`, `argus/capability/`, `argus/workflow/`, `argus/lifecycle/test_lifecycle.py`, `argus/CHANGELOG.md`, `argus/DEVLOG.md`, `argus/IMPLEMENTATION_REPORT.md`, `argus/factory/`, and every legacy pre-Factory file were left completely untouched.

## 6. Integration Notes

- `PluginManager(event_bus)` — constructed in `bootstrap.py` immediately after the Capability Registry, depending only on the Event Bus. One built-in `Plugin` ("Core Workflows") is registered immediately after construction, whose `exported_capabilities` are `tuple(capability_registry.list_capabilities())` — the identical five `Capability` objects already registered with the Capability Registry, not copies.
- This is now the 14th core service constructed (`CapabilityRegistry` remains 13th, `IntentDispatcher` shifts to 15th, since its own construction is unaffected but now comes one slot later in bootstrap's sequence).
- Registered in the Container (`"plugin_manager"`), in the Service Registry as a `ServiceDescriptor` (version `"0.1.3"`, the repository's currently released version — see Section 2), and in the Lifecycle Manager as `LifecycleState.REGISTERED` — matching the treatment of all thirteen prior core services. `PluginManager` has no gated method (not an `IService` adopter).
- `argus/events/event_types.py` extended with four new members: `PLUGIN_REGISTERED`, `PLUGIN_UNREGISTERED`, `PLUGIN_ENABLED`, `PLUGIN_DISABLED`.
- Naming (`"plugin_manager"`) verified against the repository's own `tests/test_bootstrap.py::CORE_SERVICE_NAMES` convention before implementation.
- The repository's pre-existing, known stray duplicate `argus/tests/test_bootstrap.py` had its `CORE_SERVICE_NAMES` tuple synchronized with `"plugin_manager"` added, per the standing Repository Rule introduced in Package 011 — and only that tuple.

## 7. Test Results

Canonical suite (`tests/`):
```
python -m unittest discover -s tests
Ran 674 tests in 0.065s
OK
```

Per this package's explicit testing instruction:
```
python -m pytest
762 passed, 38 subtests passed in 0.52s
```

The synchronized duplicate `argus/tests/` also verified passing standalone (unaffected by the one-line sync):
```
python -m unittest discover -s argus/tests -p "test_*.py"
Ran 64 tests in 0.018s
OK
```

`pyflakes` on every new/modified module: clean, no warnings.

`python main.py`:
```
2026-07-25 15:41:35 [INFO] argus: ArgusOS application started.
2026-07-25 15:41:35 [INFO] argus: ArgusOS application shutting down.
```
Exit code 0.

## 8. Coverage Summary

Measured with `coverage.py`, `python -m coverage run -m pytest`:

| Module | Stmts | Miss | Cover |
|---|---|---|---|
| `argus/bootstrap.py` | 62 | 0 | 100% |
| `argus/events/event_types.py` | 54 | 0 | 100% |
| `argus/plugins/__init__.py` | 5 | 0 | 100% |
| `argus/plugins/exceptions.py` | 4 | 0 | 100% |
| `argus/plugins/interfaces.py` | 21 | 0 | 100% |
| `argus/plugins/manager.py` | 66 | 0 | 100% |
| `argus/plugins/plugin.py` | 18 | 0 | 100% |

Package 014 total (all `argus/plugins/*` plus touched `argus/bootstrap.py`/`argus/events/event_types.py`): 230 statements, 100% covered — no accepted gaps, unlike `action.py`'s unreachable ABC-stub line in earlier packages, since no new module here defines an abstract method with an unreachable `raise NotImplementedError` body. Full `argus/*` coverage: 99% (unchanged from Package 013; remaining gaps are pre-existing and out of scope).

## 9. Engineering Decisions / Deviations from the Work Order

- **The dispatch path (`argus/dispatcher/`, `argus/workflow/`) was left completely untouched** — the target architecture diagram's Plugin Manager positioning was read as directional, not a Version 1 wiring requirement. See Section 3, Decision 1.
- **`Plugin.exported_capabilities` holds live `Capability` objects, not ids** — a one-way, data-only dependency mirroring `argus/dispatcher/action.py`'s existing dependency shape on `Capability`. See Section 3, Decision 2.
- **Bootstrap's built-in plugin wraps the same five `Capability` instances already in the Capability Registry**, rather than constructing new ones — avoids double-registration risk and keeps "Behavior should remain unchanged" literal. See Section 3, Decision 3.
- **`enable()`/`disable()` are unconditional and idempotent-in-effect**, always replacing and publishing regardless of prior state — a deliberate simplicity choice, not an oversight. See Section 3, Decision 4.
- **`IPluginManager` does not inherit `IService`** — a deliberate, ADR-0002-driven choice, not an oversight. See Section 4.
- **No plugin-discovery machinery (filesystem/entry-point scanning) was added** — out of Version 1 scope per the work order's own "avoid introducing unnecessary abstraction" instruction. See Section 3, Decision 5.
- **`CORE_SERVICES_VERSION` remains `"0.1.3"`, unchanged by this package.** Per the Founder's standing policy and this package's own explicit Version Policy.
- **`argus/tests/test_bootstrap.py` (duplicate tree) synchronized, tuple-only**, per the standing Repository Rule introduced in Package 011.

## 10. Known Limitations

- Plugin discovery is registration-only in Version 1 — no filesystem/entry-point scanning, no dynamic import machinery, no plugin-directory convention. A caller must construct and register every `Plugin` explicitly.
- Plugins do not execute anything — there is no `Plugin.activate()` and no relationship between a `Plugin` and any `Action`/`WorkflowAction` beyond the `exported_capabilities` data link, matching the work order's explicit "Plugins are NOT required to execute real business logic yet."
- `list_exported_capabilities()`'s Capabilities are not automatically registered with the Capability Registry — `PluginManager` only exposes them; a caller decides whether and how to register any of them. In Version 1, the only caller (`bootstrap.py`) already registered these same five Capabilities directly in Package 013's population step.
- The repository's stray `argus/` duplicate tree (beyond the one explicitly-required `test_bootstrap.py` sync) and legacy pre-Factory files remain unresolved, out of scope per the Founder's explicit repository rules.

## 11. Repository-Derived Package Metrics (measured, not estimated)

Measured via `git diff --stat`/`--numstat` against the working tree's unmodified base commit `6cc70f6` (no commit was made — see Section 2):

- Files Created: 8 (5 `argus/plugins/*.py`, `factory/packages/014_PLUGIN_MANAGER.md`, 2 new test files)
- Files Modified: 9 (`argus/bootstrap.py`, `argus/events/event_types.py`, `design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`, `factory/ROADMAP.md`, `tests/test_bootstrap.py`, `argus/tests/test_bootstrap.py`, `CHANGELOG.md`, `DEVLOG.md`, `IMPLEMENTATION_REPORT.md`)
- Lines Added: 1,704 / Lines Removed: 120 (measured via `git diff --stat` across all 17 touched files, including this report's own replacement)
- Unit Tests: 674 passing in canonical `tests/` (net +69 vs. Package 013's 605: +19 `test_plugin.py`, +47 `test_plugin_manager.py`, +3 `test_bootstrap.py`)
- Coverage: 100% (Package 014 modules), 99% (full `argus/*`)
- Public Classes: 2 (`Plugin`, `PluginManager`)
- Public Interfaces: 1 (`IPluginManager`)
- New Dependencies: 0
- External Libraries: 0 (standard library only)
- Architecture Deviations: 0 (see Section 9 for documented, non-architectural deviations)

## 12. Pre-Completion Checklist (per the Founder's explicit checklist)

- ✓ **Bootstrap registration** — `PluginManager(...)` constructed in `bootstrap.py`, registered in the Container as `"plugin_manager"`. Confirmed via `test_bootstrap_registers_plugin_manager_in_container`.
- ✓ **Service registration** — recorded as a `ServiceDescriptor` (version `"0.1.3"`) alongside all thirteen prior core services.
- ✓ **Lifecycle integration** — registered in the Lifecycle Manager as `LifecycleState.REGISTERED`.
- ✓ **Built-in plugin registration** — one "Core Workflows" `Plugin` registered at bootstrap, confirmed via `test_bootstrap_plugin_manager_has_builtin_plugin`.
- ✓ **Capability export integration** — confirmed via `test_bootstrap_plugin_manager_exports_same_capabilities_as_registry`, asserting `assertIs` identity between `PluginManager.list_exported_capabilities()` and `CapabilityRegistry.list_capabilities()` entries.
- ✓ **Event Bus integration** — all four new plugin lifecycle events verified published at the correct points, in order, only on success, via `tests/test_plugin_manager.py`.
- ✓ **Naming consistency** — `"plugin_manager"` verified against the repository's own `CORE_SERVICE_NAMES` convention before implementation.
- ✓ **Regression suite passes** — `python -m unittest discover -s tests` reports `Ran 674 tests ... OK`; `python -m pytest` reports `762 passed, 38 subtests passed`.
- ✓ **`python main.py` starts cleanly** — exit code 0.
- ✓ **`pyflakes` clean** — no warnings on any new/modified module.
- ✓ **No unintended repository modifications** — confirmed via `git status`/`git diff --stat`; only the files listed in Section 5 were touched.
- ✓ **`CORE_SERVICES_VERSION` not modified** — confirmed still `"0.1.3"`.
- ✓ **No commit created** — confirmed via `git log` (HEAD unchanged at `6cc70f6`).
- ✓ **No tag created** — confirmed via `git tag -l` (unchanged: `v0.1.1`, `v0.1.2`, `v0.1.3`).
- ✓ **Repository ready for integration and release** — all regression, smoke, and pyflakes checks pass locally; final integration, version bump, commit, and tag remain the Founder's responsibility.

## 13. Concise Implementation Summary

Package 014 adds `argus/plugins/`: an immutable `Plugin` value object (with `exported_capabilities` holding live `Capability` references), `IPluginManager` (a plain ABC, deliberately not an `IService`), and `PluginManager`, a pure metadata-and-lifecycle store with field validation at `register()` time, unconditional `enable()`/`disable()` flag-replacement, and `PluginRegistered`/`PluginUnregistered`/`PluginEnabled`/`PluginDisabled` event publication. `bootstrap.py` registers `PluginManager` as ArgusOS's 14th core service, immediately after the Capability Registry, and populates one built-in "Core Workflows" `Plugin` whose exported capabilities are the same five `Capability` objects Package 013 already registered — no double registration, no behavior change. The target architecture's "Action -> Plugin Manager -> Workflow" diagram positioning was deliberately not wired into the dispatch path in Version 1: `argus/dispatcher/`, `argus/capability/`, and `argus/workflow/` are all untouched. `PluginManager` is the second consecutive new non-`IService`-adopter data point for ADR-0002. 674 tests pass in `tests/` (`python -m pytest` also passes: 762 passed, 38 subtests), 100% coverage across all Package 014 modules. Built and verified entirely within the Founder-supplied repository; no commit, tag, push, or git-history change was made, and `CORE_SERVICES_VERSION` was not advanced, per instruction.

## 14. Architectural Observations

- This package is the first since Package 010 (Workflow Engine, introducing `StepAction` as an opaque callable) to add a new value object holding references to another package's own value object (`Plugin.exported_capabilities: Sequence[Capability]`) without that dependency ever becoming bidirectional or needing an opaque-factory indirection — `Capability`'s own immutability (established in Package 013) is what makes this safe; a mutable `Capability` would have forced a defensive-copy or factory-injection pattern here instead.
- `PluginManager` is now the second consecutive core service (after Capability Registry, 013) that is architecturally closer to Knowledge/Memory Service (006/007) than to any `IService` adopter — worth flagging again, as Package 013's own report did, that adjacency in package numbering continues to say nothing about architectural similarity, and each new service still needs ADR-0002's criterion re-applied fresh rather than pattern-matched against recent packages.
- The work order's own target-architecture diagram outpaced this package's actual Version 1 scope by design ("Plugins are NOT required to execute real business logic yet") — this is the first package in this codebase's history where the target architecture diagram and the actual wired dispatch path diverge on purpose, rather than the diagram simply describing what was just built. Worth flagging explicitly for whichever future package is expected to actually route dispatch through the Plugin Manager, since at that point `IntentDispatcher`/`Action`/`build_action_from_capability` will need deliberate reconsideration, not just an incremental extension.
- The "currently-unowned architectural gap" flagged in Packages 011, 012, and 013's own reports - nothing yet takes a raw user message all the way through classification, capability resolution, plugin-aware execution, and response generation automatically - remains open after this package, unchanged in shape.
