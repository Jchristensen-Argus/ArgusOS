# Dev Log

## v0.0.9 – Intent Detection

Today Argus made its first architectural decision.

The Brain now routes requests instead of blindly sending everything to the AI.

Testing revealed a major architectural insight:

Memory stores information.
Knowledge understands information.

This changed the roadmap and led to the design of the Knowledge Engine.
---

## Package 002 – Bootstrap

Argus Factory reconciled two conflicting implementation packages (001_FOUNDATION and 002_BOOTSTRAP, which both targeted the same files with diverging scope). The Architect retired 001 as historical documentation and confirmed 002 as authoritative.

Built the foundational application framework: a dependency injection Container, a minimal Configuration loader, a Logging Service wrapping the standard library, and an Application lifecycle (start/shutdown), wired together by a single `bootstrap()` function. `python main.py` now runs this sequence instead of launching the legacy Shell.

Two things came up worth carrying forward:

Order of initialization matters. LOGGING.md states Logging depends on Configuration, so Configuration loads first and Logging initializes from it — not the other way around.

Configuration Service's own specification lists Event Bus as a required dependency, but Event Bus is out of scope for this package. Resolved by scoping this package's Configuration to a one-time startup load with no change notification; wiring to the Event Bus is deferred until that package exists.

The interactive Shell still exists in the codebase but is no longer started from `main.py`. It predates the Factory architecture and needs to be reintroduced deliberately as an application on top of this foundation, not bypassed around it.

The coding standard was also consolidated: `CODING_STANDARDS.md` and `coding.md` were merged into a single canonical `factory/standards/CODING_STANDARD.md`.

---

## Package 002 – Bootstrap (architecture review correction)

Architecture review caught a real gap: the test suite booted fine in isolation but `python -m unittest` and `python -m unittest discover` found zero tests, and `pytest` wasn't installed in the review environment. Root cause: the tests were written as bare pytest-style functions (`pytest.raises`, the `tmp_path` fixture) with no `unittest.TestCase` classes, and `pytest` was never declared as a project dependency anywhere in the repo. `unittest`'s loader only collects test methods defined on `TestCase` subclasses, so it silently found nothing.

Rewrote all five test files as `unittest.TestCase` classes using only the standard library (`tempfile.TemporaryDirectory` in place of `tmp_path`, `assertRaises` in place of `pytest.raises`), and added `tests/__init__.py`. Verified `python -m unittest`, `python -m unittest discover`, and `python -m unittest discover -s tests` all find and pass the full 21-test suite with no dependencies beyond the standard library, consistent with the coding standard's preference for the standard library over new dependencies.

---

## Package 003 – Event Bus

Built the publish/subscribe communication backbone: an immutable `Event` (frozen dataclass, UUID + UTC timestamp auto-generated, payload/metadata wrapped in `MappingProxyType` so no handler can mutate what it receives), an `IEventBus` contract, and `InMemoryEventBus` — a synchronous, in-process implementation with explicit validation for null events, invalid types, missing sources, non-callable handlers, and duplicate subscriptions.

A few judgment calls, all grounded directly in the spec text rather than invented:

`publish()` validates the event, times the dispatch, and logs type/source/priority/handler-count/duration; `dispatch()` is the separate, unvalidated handler-invocation primitive the interface also requires. Splitting them this way is the only reading that doesn't make one of the two interface methods redundant.

`EventPriority` defaults to `NORMAL` — implied by the acceptance scenario, which constructs an `Event` without a priority.

Registered `InMemoryEventBus` in the Container from `bootstrap.py` only. Left `Application.start()`/`shutdown()` untouched — the work order's objectives call for DI registration, not for lifecycle wiring, and Package 002's lifecycle was explicitly marked "preserve exactly." Flagged as a natural next package rather than folded in here.

All 21 Package 002 tests plus 27 new tests pass under `python -m unittest discover` — 48 total, no pytest anywhere.

---

## Package 004 – Service Registry

Built the operating system's authoritative service directory: an immutable `ServiceDescriptor` (name/instance/interface/version/state/metadata, metadata wrapped in `MappingProxyType` the same way `Event`'s payload/metadata were in Package 003), a `ServiceState` enum, an `IServiceRegistry` contract, and `InMemoryServiceRegistry` — a deterministic, name-keyed registry with explicit exceptions for duplicate registration and unknown-name lookups.

A few decisions worth flagging:

`register()` takes a fully-constructed `ServiceDescriptor` rather than loose parameters — keeps the "no business logic" constraint on `ServiceDescriptor` honest (it's pure data; the registry doesn't build it) and keeps `InMemoryServiceRegistry` focused purely on storage/lookup.

`resolve()` returns the raw service instance (`descriptor.instance`), not the descriptor, matching `Container.resolve()`'s existing behavior; `list_services()` returns the full descriptors so callers can still introspect version/state/metadata/interface when enumerating.

`unregister()` of a name that was never registered raises `ServiceNotFoundError` rather than no-op — same reasoning as `EventBus.unsubscribe()` in Package 003: "never silently fail" plus the established precedent.

`ServiceState` has no separate module: the work order's package structure lists five files with no room for a `service_state.py`, so it lives in `service_descriptor.py` next to the dataclass that uses it, the same way `EventType`/`EventPriority` both live in `event_types.py`.

Registered `InMemoryServiceRegistry` in the Container from `bootstrap.py` only, in the exact position specified (between Event Bus and Application). Did not populate the registry with the existing services (Configuration, Logger, Event Bus) — the spec's Bootstrap Integration section asks for registering the Service Registry itself, not for using it yet.

72 tests total (48 from Packages 002/003 plus 24 new), all passing under `python -m unittest discover`, no pytest anywhere.

---

## Package 005 – Service Lifecycle

Built the common lifecycle contract and state machine every ArgusOS service will eventually implement: `IService` (initialize/start/stop/status), `LifecycleState` (seven states), and `LifecycleManager`, an in-memory, per-name state machine with an explicit legal-transition graph.

The one real gap in the spec: the "Suggested public API" lists five methods (register/initialize/start/stop/status), but the transition rules require a `FAILED` state reachable from "any active state," and none of those five methods can produce it — `initialize`/`start`/`stop` each move forward exactly one step in the happy path, and `status` is read-only. Added a sixth method, `fail(service_name)`, since there's no other way to satisfy an explicit requirement in the same document. Documented prominently rather than silently added, since it's the most consequential judgment call in this package.

The other structural note: `stop()` has to cover two edges (`RUNNING`→`STOPPING`→`STOPPED`) in one call, since there's no separate method for the second edge. It's implemented as one validated transition into `STOPPING` immediately followed by a direct write to `STOPPED` — no timers, no background step, matching "no timers, no background workers."

Registered the five core services (Configuration, Logger, Event Bus, Service Registry, Lifecycle Manager) into both the Service Registry (finally closing the gap Package 004 flagged as a known limitation) and the Lifecycle Manager, all landing on `REGISTERED` and nothing further, exactly as instructed. Used `"0.0.5"` as the version on their `ServiceDescriptor`s, taken from this work order's own version target header.

Flagged one open architecture question rather than resolving it myself: `ServiceDescriptor.state` (Package 004) and `LifecycleManager`'s `LifecycleState` (Package 005) are now two parallel, unsynchronized "state" concepts tracking the same five names. Not this package's job to unify them, but worth the Architect's attention before more services start relying on either one.

99 tests total (72 from Packages 002-004 plus 27 new), all passing under `python -m unittest discover`, no pytest anywhere.

---

## Package 005 – Architectural Revision (duplicate state elimination)

Architecture review caught exactly the thing flagged as a known limitation when Package 005 first shipped: `ServiceDescriptor.state` and the Lifecycle Manager's `LifecycleState` were two independent models of the same concept, set together but never kept in sync. Asked to make the Lifecycle Manager the sole owner and eliminate the duplicate before acceptance.

Removed `state` from `ServiceDescriptor` and deleted `ServiceState` outright — searched the whole tree for it first to make sure nothing else depended on it (nothing did; only `service_descriptor.py`, `services/__init__.py`, and `bootstrap.py`'s construction call ever touched it). `ServiceDescriptor` is now pure identity/descriptive data: name, instance, interface, version, metadata. Runtime state lives in exactly one place now.

This breaks `ServiceDescriptor`'s constructor signature. Didn't try to preserve backward compatibility with a stray optional `state` parameter that goes nowhere — the revision request was explicit that eliminating the duplicate takes priority, and the only callers were `bootstrap.py` and the test suite, both already fixed.

Verified end to end: `python main.py` clean, all 99 tests passing, and a manual bootstrap check confirming no core service's `ServiceDescriptor` carries a `state` attribute while every core service still correctly reports `LifecycleState.REGISTERED` from the Lifecycle Manager.
