# Implementation Package 017 - Connector Framework

## Objective

Give ArgusOS a single, isolated layer responsible for all
communication with external systems. Per the Founder's Package 017
work order:

```
... -> Workflow -> Services -> Connector Framework -> External Systems
```

extending the current architecture diagram (which ends at Services)
with a new bottom layer. The Connector Framework owns connectivity
only. It never executes Plans, never creates Plans, never dispatches
Intents, never manages Plugins, and never performs business logic -
"The Connector Framework is the only layer responsible for
communicating with external systems." Version 1 ships no real
integrations: exactly one mock connector, backed by an entirely
in-memory `MockConnector`, with no network, no I/O, and no
authentication of any kind.

---

## Specification Note

No `design/specifications/CONNECTOR_FRAMEWORK.md` exists in the
repository - the same situation as Packages 002, 009-016. This
package is built directly from the Founder's explicit work order.

---

## Connector Lifecycle

```
        register_connector(connector, implementation)
                        |
                        v
              Connector: enabled=True  --publish CONNECTOR_REGISTERED-->
              (held in ConnectorManager alongside the injected
               IConnector implementation, keyed by the same id)
                        |
          +-------------+-------------+
          |             |             |
   disable_connector  enable_connector  invoke(connector_id, op, payload=...)
          |             |             |
          v             v             v
   enabled=False   enabled=True   [ConnectorManager itself must be
   --publish        --publish      RUNNING, or InvalidConnectorStateError]
   CONNECTOR_        CONNECTOR_          |
   DISABLED          ENABLED             v
                                   [connector must be enabled, or
                                    ConnectorDisabledError]
                                          |
                                          v
                              implementation.connect()   (idempotent)
                                          |
                                          v
                              implementation.invoke(op, payload)
                                    |            |
                              succeeds       raises
                                    |            |
                                    v            v
                          --publish        --publish CONNECTOR_FAILED--
                          CONNECTOR_        (re-raised as
                          INVOKED--         ConnectorInvocationError)
                          return result

        unregister_connector(connector_id)
                        |
                        v
              removed from both internal tables
              (no dedicated event - see Architectural Decision 3)
```

`ConnectorManager.invoke()` never calls `disconnect()` automatically -
see Architectural Decision 2 for the full rationale.

---

## Dependency Graph

```
ConnectorManager
    depends on -> IEventBus   (publish connector lifecycle/invocation events)

ConnectorManager does NOT depend on:
    argus.runtime      (AgentRuntime is never referenced)
    argus.planner       (Planner is never referenced)
    argus.dispatcher     (IntentDispatcher is never referenced)
    argus.plugins        (PluginManager is never referenced)
    argus.capability     (CapabilityRegistry is never referenced)
    argus.workflow        (WorkflowEngine is never referenced)
```

Construction order in `bootstrap.py` follows the Bootstrap section's
explicit sequence - Capability Registry -> Intent Dispatcher ->
Planner -> Agent Runtime -> Connector Manager - with Connector
Manager constructed last. Unlike every prior "diagram-position-versus-
construction-order" case this codebase has documented (Capability
Registry/Intent Dispatcher in Package 013, Planner/Intent Dispatcher
in Package 015, AgentRuntime/Planner in Package 016), this one is
**not dependency-driven at all**: the dependency graph above shows
`ConnectorManager` depends on nothing but the Event Bus - it could be
constructed immediately after Package 004's Event Bus step with no
functional change. The work order's construction order is a purely
sequential, positional instruction ("append last"), not a reflection
of any real object dependency, and is followed exactly as given
regardless.

---

## Architectural Decisions

### 1. `Connector` (pure data) and `MockConnector` (behavior) are deliberately kept apart, in different files, to avoid a circular import

This package's explicit file list (`__init__.py, connector.py,
manager.py, interfaces.py, exceptions.py`) has no separate file for a
concrete connector implementation, yet Version 1 must ship one (per
"No real integrations yet. Use mock connectors only"). Placing
`MockConnector` in `connector.py` would force `connector.py` to import
`IConnector` from `interfaces.py`, while `interfaces.py` already
imports `Connector` from `connector.py` for typing
`IConnectorManager`'s methods - a circular import. `manager.py`
already depends on both `connector.py` and `interfaces.py`, and
nothing in the package depends on `manager.py`, so `MockConnector`
lives there instead - keeping `connector.py` a pure, dependency-free
leaf, matching the precedent set by `argus.capability.capability`,
`argus.plugins.plugin`, `argus.planner.plan`, and
`argus.runtime.execution`.

`ConnectorManager` holds `Connector` metadata and the live
`IConnector` implementation that backs it in two separate internal
dictionaries, keyed by the same `connector.id`, kept in sync on every
`register_connector()`/`unregister_connector()` call - `Connector`
itself never holds a live, callable reference to its own
implementation, exactly mirroring how `Capability`/`Plugin`/`Plan`/
`Execution` hold no live service references of their own.

### 2. `invoke()` always calls `connect()` first; it never calls `disconnect()` afterward

The work order lists `connect()`/`disconnect()`/`invoke()`/
`health_check()` as `IConnector`'s suggested methods, but
`ConnectorManager`'s own method list names only `invoke()` - no
manager-level `connect()`/`disconnect()` at all. Since
`ConnectorManager.invoke()` is therefore the *only* way a caller using
just the manager's public API can ever cause a connector to connect,
`invoke()` calls the underlying implementation's `connect()`
immediately before calling `invoke()` on it. `IConnector.connect()` is
required by its own contract to be idempotent, so this is safe
regardless of whether the connector was already connected.
`disconnect()` is deliberately never called automatically afterward -
"connect once, invoke many times" is the more realistic connection-
pooling model, and Version 1 has no automatic idle-teardown policy. A
future package may add one once real (non-mock) integrations exist
that make idle connections costly to hold open.

### 3. `IConnectorManager.health_check()` is not exposed at the manager level

`IConnector.health_check()` is part of every connector
implementation's own contract, but `ConnectorManager`'s explicit
method list (`register_connector`/`unregister_connector`/
`get_connector`/`list_connectors`/`enable_connector`/
`disable_connector`/`invoke`) does not include it. Rather than
inventing a manager-level wrapper the work order does not ask for,
`health_check()` is tested directly against `MockConnector` instances
in `tests/test_connector.py` - satisfying this package's explicit
"Test: ... health checks" requirement without adding to
`ConnectorManager`'s closed public surface. A caller invoking through
`ConnectorManager.invoke()` observes connectivity problems indirectly,
as a `CONNECTOR_FAILED` event and a raised `ConnectorInvocationError`,
if the underlying implementation's `connect()` fails.

### 4. `register_connector()` does not `isinstance`-check its `implementation` argument

`connector: Connector` is validated (type, non-empty `id`/`name`/
`version`) because `Connector` is a concrete dataclass this same
package defines - cheap and idiomatic to check, mirroring
`Capability.register()`'s own validation of its `Capability` argument
(Package 013). `implementation: IConnector`, by contrast, is an
injected, foreign, behavioral dependency - and no constructor-injected
interface anywhere in this codebase (`IEventBus`, `IIntentDispatcher`,
`IPlanner`, `IWorkflowEngine`, ...) is ever `isinstance`-checked at
the point of injection. `register_connector()` follows that same
established convention: `implementation` is trusted by type hint only,
checked solely for not being `None`.

### 5. No `IConnectorManager.get_connector()` lookup "by name"

The work order's Responsibilities section says the framework shall
"resolve connectors by name," while its Connector Manager method list
gives `get_connector()` no explicit parameter name, and its Connector
Model lists `connector_id` first among suggested fields. Every prior
registry in this codebase (`Capability`, `Plugin`, `Plan`,
`Execution`) is looked up by a generated `id`, not by its
human-readable `name` (which is never enforced unique). This package
follows that same established convention: `get_connector(connector_id)`
resolves by `id`. `name` remains a plain, non-unique descriptive
field, consistent with every other value object in this codebase.

### 6. `Connector.id`, not `connector_id`, for the model's own self-identifier

The work order's suggested `Connector` fields list `connector_id`, but
every other value object in this codebase (`Capability`, `Plugin`,
`Plan`, `PlanStep`, `Execution`) uses a plain `id` field for its own
identity. This package follows that same convention - `Connector.id`
- exactly mirroring `Execution.id`'s identical deviation from the
Package 016 work order's own `execution_id` suggestion.
`connector_id` remains the parameter name used throughout
`ConnectorManager`'s public API (`get_connector(connector_id)`,
`invoke(connector_id, ...)`, event payload keys) - only the model's
own field name differs from the work order's literal suggestion.

### 7. `Connector.capabilities` is a plain tuple of strings, unrelated to `argus.capability.Capability`

"Capabilities" in this package's Connector Model means the operation
names a connector exposes to `invoke()` (for example,
`"send_email"`) - a connector-local, descriptive concept with no
relationship to `argus.capability.capability.Capability`, which is a
Dispatcher-facing concept tied to `IntentType`/`action_kind`/
`workflow_id`. Modeling `Connector.capabilities` as a plain
`Sequence[str]` keeps `argus.connectors` free of any dependency on
`argus.capability`, preserving "the framework owns connectivity only."
`ConnectorManager.invoke()` does not check that `operation` is a
member of `capabilities` - the field is purely descriptive/informational
in Version 1.

---

## Events

Exactly the five event types this package's own Events section names:
`CONNECTOR_REGISTERED`, `CONNECTOR_ENABLED`, `CONNECTOR_DISABLED`,
`CONNECTOR_INVOKED`, `CONNECTOR_FAILED`. `CONNECTOR_ENABLED`/
`CONNECTOR_DISABLED` fire every time `enable_connector()`/
`disable_connector()` succeeds, even if the connector was already in
that state - matching `PLUGIN_ENABLED`/`PLUGIN_DISABLED`'s (Package
014) identical "fires regardless of prior state" precedent.
`CONNECTOR_INVOKED`/`CONNECTOR_FAILED` are mutually exclusive outcomes
for a single `invoke()` call, matching `EXECUTION_COMPLETED`/
`EXECUTION_FAILED` (Package 016), `WORKFLOW_COMPLETED`/
`WORKFLOW_FAILED` (Package 010), and `DISPATCH_COMPLETED`/
`DISPATCH_FAILED` (Package 012). See Architectural Decision 3 for why
no `CONNECTOR_UNREGISTERED` event was added.

---

## IService Adoption

`IConnectorManager` DOES inherit `IService` - continuing the pattern
`AgentRuntime` set in Package 016 rather than the three-consecutive-
non-adopter streak that preceded it (Capability Registry - 013,
Plugin Manager - 014, Planner - 015). `invoke()` - the only method
that actually reaches an external system's connector implementation -
is genuinely gated on the manager's own `RUNNING` state, architecturally
identical to `IntentDispatcher.dispatch()` (012) and
`AgentRuntime.start_execution()` (016) - if anything a stronger case
for gating, since `invoke()` is the literal boundary between ArgusOS
and the outside world. `register_connector()`/`unregister_connector()`/
`get_connector()`/`list_connectors()`/`enable_connector()`/
`disable_connector()` remain ungated, matching `AgentRuntime`'s own
pause/cancel/get/list precedent. See
`argus/connectors/interfaces.py`'s Architectural Note and
`design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`'s newly
appended Empirical Finding, which records `ConnectorManager` as the
seventh `IService` adopter and the sixth genuinely-gated one.

---

## Repository Verification Note

The uploaded repository ("ArgusOS (16).zip") was verified against this
package's own general "verify repository state, verify version
consistency, run smoke validation" pre-flight instruction (this work
order did not specify a fixed pre-flight checklist the way Packages
013-015's did). Findings: HEAD (`fc6225a`, "Synchronize repository
version with v0.1.6 release") is a clean, single-commit descendant of
tag `v0.1.6` (which points to `2f40211`, "Implement Package 016 Agent
Runtime"); `git diff v0.1.6..HEAD --stat` shows exactly 1 file changed
(`argus/bootstrap.py`, 1 insertion/1 deletion) - a minimal, standard
version-only sync, no anomaly this time (unlike Package 016's own
pre-flight, which found an uncommitted-but-correct version bump).
`git status --short` showed a completely clean working tree.
`argus/runtime/` (Package 016) present with all 5 expected files;
`python -m pytest` passing (919 passed, 38 subtests); `python -m
unittest discover -s tests` passing (831); `python main.py` starting
and shutting down cleanly (exit 0); `CORE_SERVICES_VERSION == "0.1.6"`
matching tag `v0.1.6`. All confirmed before any Package 017 code was
written.

---

## Files Created

```
argus/
    connectors/
        __init__.py
        connector.py
        manager.py
        interfaces.py
        exceptions.py
tests/
    test_connector.py
    test_connector_manager.py
```

## Files Modified

```
argus/bootstrap.py            (construct + register Connector Manager
                                as 17th core service, immediately
                                after the Agent Runtime, per the
                                Bootstrap section's explicit,
                                purely-sequential construction order;
                                registers one built-in mock connector,
                                "Mock External System"; CORE_SERVICES_
                                VERSION left at "0.1.6" - not advanced
                                by this package)
argus/events/event_types.py   (5 new event types)
argus/tests/test_bootstrap.py (CORE_SERVICE_NAMES tuple only, per the
                                standing Package 011 rule)
tests/test_bootstrap.py       (CORE_SERVICE_NAMES tuple + 3 new tests)
design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md (Empirical Finding
                                appended; Status remains Proposed)
CHANGELOG.md, DEVLOG.md, IMPLEMENTATION_REPORT.md, factory/ROADMAP.md
```

`argus/runtime/`, `argus/planner/`, `argus/dispatcher/`,
`argus/capability/`, `argus/workflow/`, and `argus/plugins/` are
unchanged - the Connector Framework has no dependency on, and no
touchpoint with, any of them; its only dependency is `IEventBus`.

---

## Test Totals

894 tests passing via `python -m unittest discover -s tests` (831 from
Packages 002-016, plus 16 new in `test_connector.py`, plus 44 new in
`test_connector_manager.py`, plus 3 new in `test_bootstrap.py`
[26->29]). `python -m unittest discover -s argus/tests` remains at 64
(duplicate tree unaffected beyond the standing `CORE_SERVICE_NAMES`
sync). `python -m pytest` also passes: 982 passed, 38 subtests
passed.

---

## Coverage

100% line coverage on every new/modified module measured for this
package: `argus/connectors/__init__.py`, `argus/connectors/connector.py`,
`argus/connectors/manager.py`, `argus/connectors/interfaces.py`,
`argus/connectors/exceptions.py`, `argus/bootstrap.py`, and
`argus/events/event_types.py` - all 100%, no accepted gaps. Overall
repository coverage: 99% (measured with `coverage run -m pytest`
followed by `coverage report`), unchanged from Package 016.

---

## Known Limitations

- **No real integrations** - `MockConnector` is the only `IConnector`
  implementation Version 1 ships; there is no network I/O,
  authentication, or persistence of any kind, per this package's
  explicit Constraints.
- **`invoke()` does not automatically disconnect** - see Architectural
  Decision 2. A connector that has been invoked once stays "connected"
  (from `MockConnector`'s own point of view) for the lifetime of the
  process, or until something explicitly calls `disconnect()` on the
  raw implementation directly (not exposed through
  `ConnectorManager`'s own API in Version 1).
- **`health_check()` is not reachable through `ConnectorManager`** -
  see Architectural Decision 3. Only a caller holding a direct
  reference to an `IConnector` implementation can call it; the
  Connector Framework's own public surface has no wrapper.
- **`Connector.capabilities` is not enforced** - `invoke()` does not
  check that the requested `operation` is a member of the connector's
  own `capabilities` tuple; the field is purely descriptive in Version
  1.
- No persistence - Connectors are held only in memory; nothing
  survives a process restart.
- No concurrency, no retries, no rollback for `invoke()` - matching
  every other Version 1 package's identical constraints.
- The repository's stray `argus/` duplicate tree (beyond the one
  explicitly-required `test_bootstrap.py` sync) and legacy pre-Factory
  files remain unresolved, out of scope per the Founder's explicit
  repository rules.

---

## Future Expansion

- Replace `MockConnector` with real connector implementations (HTTP,
  database, message-queue, etc.) once a future package's Constraints
  permit real external I/O and authentication.
- Add an automatic idle-disconnect policy to `ConnectorManager.invoke()`
  once real (non-mock) connections make holding them open indefinitely
  costly (Architectural Decision 2).
- Expose `health_check()` at the `ConnectorManager` level, if a future
  package's Responsibilities call for it (Architectural Decision 3).
- Wire `AgentRuntime`/`Dispatcher` to `ConnectorManager.invoke()`, so a
  `PlanStep`/`Capability` can eventually reach an external system as
  part of a real execution - out of bounds for this package, whose
  Objective is connectivity infrastructure only, not execution
  integration.
- Enforce `Connector.capabilities` against `invoke()`'s `operation`
  argument, once Version 1's deliberately permissive behavior is
  revisited.

---

## Release Rules

Per the Founder's explicit instruction: no commit, tag, or push was
performed. `CORE_SERVICES_VERSION` was not changed by this package -
it remains `"0.1.6"`. This package is not reported as complete or
released - implementation ends after successful local verification;
final validation, integration, release, version update, commit, and
tag are the Founder's responsibility against the live repository.
