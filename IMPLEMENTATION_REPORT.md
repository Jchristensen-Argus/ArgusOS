# ArgusOS Implementation Report — Package 017: Connector Framework

## 1. Package Overview

Package 017 adds `argus/connectors/`, the only layer in ArgusOS responsible for communicating with external systems. `ConnectorManager` registers, enables/disables, looks up, and invokes `Connector`s - immutable metadata records paired one-to-one with a live `IConnector` implementation held internally by the manager. `invoke()` is gated on the manager's own `IService` lifecycle state being `RUNNING`; `register_connector()`/`unregister_connector()`/`get_connector()`/`list_connectors()`/`enable_connector()`/`disable_connector()` remain ungated registry-style operations - continuing, not breaking, the `IService`-adoption pattern `AgentRuntime` established in Package 016. `invoke()` always calls the implementation's `connect()` (required to be idempotent) immediately before calling its `invoke()`, and never calls `disconnect()` automatically. Version 1 ships exactly one concrete `IConnector` implementation, `MockConnector` - fully in-memory, no network, no I/O, no authentication - per this package's explicit "No real integrations yet. Use mock connectors only" constraint. `ConnectorManager` is registered as ArgusOS's 17th core service, constructed immediately after the Agent Runtime; bootstrap.py also registers one built-in mock connector, "Mock External System." All 831 pre-existing canonical tests still pass unchanged; 894 tests total pass under `python -m unittest discover -s tests`, and `python -m pytest` also passes (982 passed, 38 subtests passed). `python main.py` starts and shuts down cleanly.

## 2. Repository Verification Note

Before writing any code, the uploaded repository ("ArgusOS (16).zip") was verified fresh against this package's own general pre-flight instruction ("verify repository state, verify version consistency, run smoke validation") - this work order did not specify the fixed, numbered checklist Packages 013-015's did.

No anomaly was found this time - a return to the standard pattern after Package 016's own uncommitted-version-bump variation. HEAD (`fc6225a`, "Synchronize repository version with v0.1.6 release") is a clean, single-commit descendant of tag `v0.1.6` (which points to `2f40211`, "Implement Package 016 Agent Runtime"), confirmed via `git merge-base --is-ancestor v0.1.6 HEAD`. `git diff v0.1.6..HEAD --stat` shows exactly 1 file changed (`argus/bootstrap.py`, 1 insertion/1 deletion) - a minimal, standard version-only sync commit, now fully committed (the working tree that produced Package 016's own uncommitted anomaly has since been committed by the Founder, as evidenced by the now-present `ca30cfb`, "Synchronize repository version with v0.1.5 release," ancestor commit). `git status --short` showed a completely clean working tree. Every substantive check passed cleanly: Package 016 (`argus/runtime/`) present with all 5 expected files; `python -m pytest` passing (919 passed, 38 subtests); `python -m unittest discover -s tests` passing (831); `python main.py` starting and shutting down cleanly (exit 0); `CORE_SERVICES_VERSION == "0.1.6"` matching tag `v0.1.6`.

Per the Founder's explicit release rules, this implementation was built, tested, and verified entirely within the supplied repository. No `git commit`, `git tag`, push, or git-history modification of any kind was performed, `CORE_SERVICES_VERSION` was not changed by this package, and this package is not being reported as complete — final validation, integration, release, tagging, and git operations are the Founder's responsibility, to be performed against the live repository after independent regression testing.

## 3. Architectural Rationale

No `design/specifications/CONNECTOR_FRAMEWORK.md` exists — the same situation as Packages 002, 009-016. Every structural decision traces to the Founder's explicit work order. The full rationale for each decision below is also recorded in `factory/packages/017_CONNECTOR_FRAMEWORK.md`'s "Architectural Decisions" section, in the source code's own module docstrings, and is only summarized here.

**Decision 1 — `Connector` and `MockConnector` are kept in different files to avoid a circular import.** This package's explicit five-file structure has no dedicated file for a concrete connector implementation, yet Version 1 must ship one. Placing `MockConnector` in `connector.py` would force it to import `IConnector` from `interfaces.py`, which already imports `Connector` from `connector.py` for typing — a cycle. `MockConnector` was placed in `manager.py` instead, keeping `connector.py` a pure, dependency-free leaf, matching the precedent set by `Capability`/`Plugin`/`Plan`/`Execution`.

**Decision 2 — `invoke()` always calls `connect()` first; it never calls `disconnect()` afterward.** `ConnectorManager`'s own method list names only `invoke()`, with no manager-level `connect()`/`disconnect()` — meaning `invoke()` is the only way a caller using the manager's public API can ever cause a connector to connect. `IConnector.connect()` is required by contract to be idempotent, making this safe regardless of prior state. `disconnect()` is never called automatically, on a "connect once, invoke many times" model; no automatic idle-teardown policy exists in Version 1.

**Decision 3 — `IConnectorManager.health_check()` is not exposed at the manager level.** `ConnectorManager`'s explicit method list (register/unregister/get/list/enable/disable/invoke) does not include `health_check()`, even though `IConnector` itself has one. Rather than inventing a manager-level wrapper the work order does not ask for, `health_check()` is tested directly against `MockConnector` instances in `tests/test_connector.py`.

**Decision 4 — `register_connector()` does not `isinstance`-check its `implementation` argument.** `connector: Connector` is validated because it is a concrete dataclass this package defines; `implementation: IConnector` is an injected, foreign, behavioral dependency, and no constructor-injected interface anywhere in this codebase is ever `isinstance`-checked at the point of injection — `register_connector()` follows that same convention, trusting `implementation` by type hint only.

**Decision 5 — lookup is by `id`, not literally "by name."** The work order's Responsibilities section says "resolve connectors by name," but every prior registry in this codebase (`Capability`, `Plugin`, `Plan`, `Execution`) is looked up by a generated `id`, not by a non-unique `name`. `get_connector(connector_id)` follows that same established convention.

**Decision 6 — `Connector.id`, not `connector_id`, for the model's own identity.** Follows the established `id`-for-self-identity / `<noun>_id`-for-references convention already set by `Capability`, `Plugin`, `Plan`, `PlanStep`, and `Execution`.

**Decision 7 — `Connector.capabilities` is a plain tuple of strings, unrelated to `argus.capability.Capability`.** "Capabilities" here means operation names a connector exposes to `invoke()` — a connector-local, descriptive concept with no relationship to the Dispatcher-facing `Capability` class, keeping `argus.connectors` free of any dependency on `argus.capability`.

## 4. IService Adoption — Continuing the Pattern Package 016 Set

`IConnectorManager` DOES inherit `IService` — `invoke()` is genuinely gated on the manager's own `RUNNING` state, architecturally identical to (and arguably a stronger case than) `IntentDispatcher.dispatch()` (012) and `AgentRuntime.start_execution()` (016), since `invoke()` is the literal boundary between ArgusOS and every external system. `register_connector()`/`unregister_connector()`/`get_connector()`/`list_connectors()`/`enable_connector()`/`disable_connector()` remain ungated, matching `AgentRuntime`'s own pause/cancel/get/list precedent. This is the seventh `IService` adopter overall and the sixth genuinely gated one — appended to `design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md` as further evidence the criterion discriminates correctly. Its Status remains `Proposed`, per standing instruction.

## 5. Directory Tree (files touched)

```
argus/
    connectors/
        __init__.py                        (new)
        connector.py                       (new)
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
        017_CONNECTOR_FRAMEWORK.md          (new)
    ROADMAP.md                              (modified)
tests/
    test_bootstrap.py                       (modified)
    test_connector.py                       (new)
    test_connector_manager.py               (new)
argus/tests/test_bootstrap.py               (modified — CORE_SERVICE_NAMES tuple only, per explicit instruction)
CHANGELOG.md                                (modified)
DEVLOG.md                                   (modified)
IMPLEMENTATION_REPORT.md                    (replaced — this file)
```

No file outside this list was created, deleted, moved, or modified. `argus/runtime/`, `argus/planner/`, `argus/dispatcher/`, `argus/capability/`, `argus/workflow/`, `argus/plugins/`, `argus/CHANGELOG.md`, `argus/DEVLOG.md`, `argus/IMPLEMENTATION_REPORT.md`, `argus/factory/`, and every legacy pre-Factory file were left completely untouched.

## 6. Integration Notes

- `ConnectorManager(event_bus)` — constructed in `bootstrap.py` immediately after the Agent Runtime, depending only on the Event Bus.
- This is now the 17th core service constructed in the bootstrap sequence; bootstrap.py also registers one built-in `Connector` ("Mock External System") backed by a `MockConnector`.
- Registered in the Container (`"connector_manager"`), in the Service Registry as a `ServiceDescriptor` (version `"0.1.6"`, the repository's currently released version — see Section 2), and in the Lifecycle Manager as `LifecycleState.REGISTERED` — matching the treatment of all sixteen prior core services. `ConnectorManager`'s own `initialize()`/`start()` are NOT called by bootstrap, for the same divergence-avoidance reasoning already applied to every other `IService` adopter.
- `argus/events/event_types.py` extended with five new members: `CONNECTOR_REGISTERED`, `CONNECTOR_ENABLED`, `CONNECTOR_DISABLED`, `CONNECTOR_INVOKED`, `CONNECTOR_FAILED`.
- Naming (`"connector_manager"`) verified against the repository's own `tests/test_bootstrap.py::CORE_SERVICE_NAMES` convention before implementation.
- The repository's pre-existing, known stray duplicate `argus/tests/test_bootstrap.py` had its `CORE_SERVICE_NAMES` tuple synchronized with `"connector_manager"` added, per the standing Repository Rule introduced in Package 011 — and only that tuple.
- Source-inspection confirms `argus/connectors/manager.py` contains no `import argus.runtime`, `argus.planner`, `argus.dispatcher`, `argus.plugins`, `argus.capability`, or `argus.workflow` statement anywhere — its only cross-package import beyond `argus.connectors` itself and the standard library is `argus.events` and `argus.lifecycle.lifecycle.LifecycleState`.

## 7. Test Results

Canonical suite (`tests/`):
```
python -m unittest discover -s tests
Ran 894 tests in 0.079s
OK
```

Per this package's explicit testing instruction:
```
python -m pytest
982 passed, 38 subtests passed in 0.93s
```

The synchronized duplicate `argus/tests/` also verified passing standalone (unaffected by the one-line sync):
```
python -m unittest discover -s argus/tests -p "test_*.py"
Ran 64 tests in 0.016s
OK
```

`pyflakes` on every new/modified module: clean, no warnings.

`python main.py`:
```
[INFO] argus: ArgusOS application started.
[INFO] argus: ArgusOS application shutting down.
```
Exit code 0.

## 8. Coverage Summary

Measured with `coverage.py`, `python -m coverage run -m pytest`:

| Module | Stmts | Miss | Cover |
|---|---|---|---|
| `argus/bootstrap.py` | 72 | 0 | 100% |
| `argus/events/event_types.py` | 68 | 0 | 100% |
| `argus/connectors/__init__.py` | 5 | 0 | 100% |
| `argus/connectors/connector.py` | 16 | 0 | 100% |
| `argus/connectors/exceptions.py` | 7 | 0 | 100% |
| `argus/connectors/interfaces.py` | 28 | 0 | 100% |
| `argus/connectors/manager.py` | 109 | 0 | 100% |

Package 017 total (all `argus/connectors/*` plus touched `argus/bootstrap.py`/`argus/events/event_types.py`): 305 statements, 100% covered — no accepted gaps. Full `argus/*` coverage: 99% (unchanged from Package 016; remaining gaps are pre-existing and out of scope).

## 9. Engineering Decisions / Deviations from the Work Order

- **`MockConnector` lives in `manager.py`, not `connector.py`**, to avoid a circular import while staying within the package's explicit five-file structure. See Section 3, Decision 1.
- **`invoke()` auto-connects but never auto-disconnects** — the only way a caller using solely `ConnectorManager`'s public API can reach `connect()`, given the manager's own method list has no separate connect/disconnect entry points. See Section 3, Decision 2.
- **No manager-level `health_check()` wrapper was added** — `ConnectorManager`'s method list is treated as closed, matching prior packages' identical treatment of closed event/method lists. See Section 3, Decision 3.
- **`implementation` is not `isinstance`-checked in `register_connector()`** — consistent with how every other injected interface dependency is trusted in this codebase. See Section 3, Decision 4.
- **Lookup is `id`-based, not literally "by name"** — following established registry convention over the work order's Responsibilities-section wording. See Section 3, Decision 5.
- **`Connector.id` (not `connector_id`) is the model's own field name** — following established repository convention over the work order's literal suggestion. See Section 3, Decision 6.
- **`Connector.capabilities` is a plain tuple of strings**, deliberately unrelated to `argus.capability.Capability`, keeping this package free of any dependency on the Capability Registry. See Section 3, Decision 7.
- **`IConnectorManager` DOES inherit `IService`** — a deliberate, ADR-0002-driven choice, continuing the pattern Package 016 set. See Section 4.
- **`CORE_SERVICES_VERSION` remains `"0.1.6"`, unchanged by this package.** Per the Founder's standing policy and this package's own explicit Constraints.
- **`argus/tests/test_bootstrap.py` (duplicate tree) synchronized, tuple-only**, per the standing Repository Rule introduced in Package 011.

## 10. Known Limitations

- **No real integrations** — `MockConnector` is Version 1's only `IConnector` implementation; no network I/O, authentication, or persistence of any kind, per this package's explicit Constraints.
- `invoke()` does not automatically disconnect — a connector stays "connected" for the process lifetime once first invoked, unless something explicitly disconnects it directly (not exposed through `ConnectorManager`'s own API in Version 1). See Section 3, Decision 2.
- `health_check()` is not reachable through `ConnectorManager` — only directly against a raw `IConnector` implementation. See Section 3, Decision 3.
- `Connector.capabilities` is descriptive only — `invoke()` does not check that the requested operation is a member of it.
- No persistence — Connectors are held only in memory.
- No concurrency, no retries, no rollback for `invoke()` — explicit Version 1 constraints.
- The repository's stray `argus/` duplicate tree (beyond the one explicitly-required `test_bootstrap.py` sync) and legacy pre-Factory files remain unresolved, out of scope per the Founder's explicit repository rules.

## 11. Repository-Derived Package Metrics (measured, not estimated)

Measured via `git diff --stat` against the working tree's unmodified base commit `fc6225a` (no commit was made — see Section 2):

- Files Created: 8 (5 `argus/connectors/*.py`, `factory/packages/017_CONNECTOR_FRAMEWORK.md`, 2 new test files)
- Files Modified: 9 (`argus/bootstrap.py`, `argus/events/event_types.py`, `design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`, `factory/ROADMAP.md`, `tests/test_bootstrap.py`, `argus/tests/test_bootstrap.py`, `CHANGELOG.md`, `DEVLOG.md`, `IMPLEMENTATION_REPORT.md`)
- Lines Added: 1,997 / Lines Removed: 96 (measured via `git diff --stat` across all 17 touched files, including this report's own replacement)
- Unit Tests: 894 passing in canonical `tests/` (net +63 vs. Package 016's 831: +16 `test_connector.py`, +44 `test_connector_manager.py`, +3 `test_bootstrap.py` [26->29])
- Coverage: 100% (Package 017 modules), 99% (full `argus/*`)
- Public Classes: 2 (`Connector`, `ConnectorManager`) plus 1 built-in implementation (`MockConnector`)
- Public Interfaces: 2 (`IConnector`, `IConnectorManager`)
- New Dependencies: 0
- External Libraries: 0 (standard library only)
- Architecture Deviations: 0 (see Section 9 for documented, non-architectural deviations)

## 12. Pre-Completion Checklist (per the Founder's explicit checklist)

- ✓ **Bootstrap registration** — `ConnectorManager(...)` constructed in `bootstrap.py`, registered in the Container as `"connector_manager"`. Confirmed via `test_bootstrap_registers_connector_manager_in_container`.
- ✓ **Service registration** — recorded as a `ServiceDescriptor` (version `"0.1.6"`) alongside all sixteen prior core services.
- ✓ **Lifecycle integration** — registered in the Lifecycle Manager as `LifecycleState.REGISTERED`, not started. Confirmed via `test_bootstrap_connector_manager_is_not_started`.
- ✓ **Built-in connector integration** — confirmed via `test_bootstrap_registers_one_built_in_mock_connector`, invoking the built-in "Mock External System" connector end-to-end once the manager is explicitly started.
- ✓ **No execution/dispatch/plugin/business-logic responsibilities taken on** — confirmed via source inspection: `argus/connectors/manager.py` contains no import of `argus.runtime`, `argus.planner`, `argus.dispatcher`, `argus.plugins`, `argus.capability`, or `argus.workflow` anywhere.
- ✓ **Event Bus integration** — all five new connector events verified published at the correct points via `tests/test_connector_manager.py`.
- ✓ **Naming consistency** — `"connector_manager"` verified against the repository's own `CORE_SERVICE_NAMES` convention before implementation.
- ✓ **Regression suite passes** — `python -m unittest discover -s tests` reports `Ran 894 tests ... OK`; `python -m pytest` reports `982 passed, 38 subtests passed`.
- ✓ **`python main.py` starts cleanly** — exit code 0.
- ✓ **`pyflakes` clean** — no warnings on any new/modified module.
- ✓ **No unintended repository modifications** — confirmed via `git status`/`git diff --stat`; only the files listed in Section 5 were touched.
- ✓ **`CORE_SERVICES_VERSION` not modified** — confirmed still `"0.1.6"`.
- ✓ **No commit created** — confirmed via `git log` (HEAD unchanged at `fc6225a`).
- ✓ **No tag created** — confirmed via `git tag -l` (unchanged: `v0.1.1`-`v0.1.6`).
- ✓ **Repository ready for architectural review** — all regression, smoke, and pyflakes checks pass locally; final integration, version bump, commit, and tag remain the Founder's responsibility.

## 13. Concise Implementation Summary

Package 017 adds `argus/connectors/`: `Connector` (an immutable metadata record), `IConnector`/`IConnectorManager(IService)`, and `ConnectorManager`, the sole component permitted to communicate with external systems - Version 1 exclusively via `MockConnector`, a fully in-memory implementation with no network, I/O, or authentication of any kind. `invoke()` is gated on the manager's own `RUNNING` state - the seventh `IService` adopter and sixth genuinely gated one, continuing rather than breaking Package 016's pattern. `invoke()` auto-connects (idempotently) but never auto-disconnects. `register_connector()`/`unregister_connector()`/`get_connector()`/`list_connectors()`/`enable_connector()`/`disable_connector()` remain ungated. `argus/runtime/`, `argus/planner/`, `argus/dispatcher/`, `argus/capability/`, `argus/workflow/`, and `argus/plugins/` are all untouched - the Connector Framework's only dependency is the Event Bus. 894 tests pass in `tests/` (`python -m pytest` also passes: 982 passed, 38 subtests), 100% coverage across all Package 017 modules. Built and verified entirely within the Founder-supplied repository; no commit, tag, push, or git-history change was made, and `CORE_SERVICES_VERSION` was not advanced, per instruction.

## 14. Architectural Observations

- This package's construction order (Capability Registry -> Intent Dispatcher -> Planner -> Agent Runtime -> Connector Manager) is the first one in this project's history that is purely positional rather than dependency-driven — `ConnectorManager` depends only on the Event Bus and could have been constructed as early as Package 004 with no functional difference. Every prior "diagram position versus construction order" case (013, 015, 016) involved a package with a genuine functional dependency justifying its specific placement; this is the first where the work order's construction order has no dependency-based justification at all, worth naming explicitly for whoever next revisits bootstrap's sequencing.
- `ConnectorManager` is the second consecutive `IService` adopter after `AgentRuntime` (016), giving ADR-0002 its first back-to-back-adoption data point rather than a single "the streak breaks" instance — useful evidence that adoption isn't a one-off exception but a real, repeatable outcome whenever a package's own core method is genuinely effectful.
- The Connector Framework currently has no consumer anywhere in ArgusOS — nothing in `AgentRuntime`, `IntentDispatcher`, or any Workflow calls `ConnectorManager.invoke()`. This mirrors the same "infrastructure exists, integration is a future package's job" pattern already seen for `PluginManager` (014) and, to a lesser extent, `Planner`/`AgentRuntime`'s own synthetic-Intent limitation (015/016) — worth flagging explicitly so a future package's scope is not assumed to already include wiring the Connector Framework into the execution path.
- The "currently-unowned architectural gap" flagged in Packages 011 through 016's own reports — nothing yet takes a raw user message all the way through classification, planning, execution, and external communication automatically — remains open after this package, now with one more seam built (external connectivity) but still not wired into the chain that would make it reachable end-to-end.
