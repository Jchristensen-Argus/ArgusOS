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

---

## Package 006 – Knowledge Service

Built ArgusOS's first persistent knowledge subsystem: `KnowledgeRecord` (immutable, category + globally-unique key + value + timestamps + version), `IKnowledgeStorage`/`JSONKnowledgeStorage` (one JSON array file per category, every write atomic via temp-file + `os.replace`), and `KnowledgeService` (the CRUD orchestrator, eager in-memory key index, write-locked, event-publishing).

The one real design decision the work order left open: how to satisfy "Publish events on the existing Event Bus. Examples: KnowledgeCreated, KnowledgeUpdated, KnowledgeDeleted" given `InMemoryEventBus._validate_event` strictly requires `isinstance(event.type, EventType)`. Extended `EventType` with `KNOWLEDGE_CREATED`/`KNOWLEDGE_UPDATED`/`KNOWLEDGE_DELETED` rather than inventing a side channel — `event_types.py`'s own docstring says outright that this module is "the single place new event types are added," and a repo-wide search turned up no test that asserts `EventType`'s membership is closed. Naming follows the exact convention already in use (`SYSTEM_STARTED`, `SERVICE_STARTED`, ...).

Kept the in-memory index as a single flat `Dict[key, KnowledgeRecord]` rather than nesting it by category, since keys are specified as globally unique — a flat map is the simplest structure that satisfies that constraint, at the cost of `_persist_category` doing an O(n) scan over the whole index on every write to rebuild just one category's file. Documented as a known limitation rather than over-engineered away, per the package's "intentionally simple" v1 scope.

Published events after releasing the write lock, not while holding it. `threading.Lock` isn't reentrant, and a future subscriber calling back into `KnowledgeService` (e.g. `get()`, or another `put()`) from inside a handler would deadlock if the lock were still held during dispatch. Reads (`get`/`exists`/`list`) stay unlocked throughout, exactly as the work order specifies ("Reads may remain unlocked for v1").

Registered `KnowledgeService` as ArgusOS's sixth core service, immediately after the Lifecycle Manager and before the core-service registration loop, since it depends on the Event Bus (already constructed) and needs to exist before anything can query it. Like the other five, it's registered in both the Service Registry and the Lifecycle Manager (`LifecycleState.REGISTERED`) but never initialized or started — `KnowledgeService` doesn't implement `IService` in this package, matching the treatment of Configuration, the Logger, the Event Bus, the Service Registry, and the Lifecycle Manager itself to date. Bumped `CORE_SERVICES_VERSION` to `"0.0.6"`, this work order's version target.

One process note worth flagging: the work order's Founder Verification Checklist says "Only expected new files should appear" in `git status`, but the Registration requirement explicitly calls for wiring `KnowledgeService` into `bootstrap.py` as a core service — that can only be done by modifying the existing `argus/bootstrap.py`, and satisfying the Events requirement can only be done by modifying the existing `argus/events/event_types.py` (plus `tests/test_bootstrap.py`, to keep its six-core-service assertions accurate). Treated the Registration and Events sections as the more deliberate, specific instructions and proceeded with those three modifications, since leaving `KnowledgeService` unregistered or unable to publish events to satisfy a terser checklist line seemed like the wrong tradeoff — flagging it here rather than resolving it unilaterally.

140 tests total (99 from Packages 002-005 plus 41 new: 8 for `KnowledgeRecord`, 12 for `JSONKnowledgeStorage`, 20 for `KnowledgeService` (including two covering empty-key/empty-category validation), and 1 extending `test_bootstrap.py`), all passing under `python -m unittest discover`, no pytest anywhere. Coverage on every new module is 100% except `storage.py` at 91% (two untested OS-failure branches in the atomic-write path).

---

## Package 007 – Memory Service

First package where I was asked to pick the target, not just implement a handed-down work order. Before writing anything, audited every unimplemented engine in `design/specifications/` (Atlas, Cortex, Hermes, Navigator, Scheduler, Sentinel, Memory) against their own stated Required Dependencies. Only two have every dependency already satisfied by what's actually built: Memory (Logging, Configuration, Event Bus) and Sentinel (Event Bus, Logging, Configuration). Everything else is blocked — Scheduler needs Navigator, Hermes needs Cortex, Navigator needs Cortex+Hermes+Scheduler, Atlas needs Memory, and Cortex has no specification file in the repository at all, so building it would mean inventing architecture rather than implementing it.

Between the two unblocked options, picked Memory over Sentinel because Memory sits on the critical path — Atlas's spec explicitly lists Memory Service as a Required Dependency, so building Memory is the next concrete step toward every reasoning-capable engine. Sentinel has nothing to govern yet: no engine that executes autonomous actions (Navigator, Hermes) exists, so a security/governance layer would be built ahead of anything it protects. Also noticed `EventType.MEMORY_UPDATED` has sat reserved and unused in `event_types.py` since Package 003 — the same kind of signal that correctly anticipated `KNOWLEDGE_*` before Package 006. Wrote the full audit into `factory/packages/007_MEMORY_SERVICE.md` so the reasoning is part of the repository, not just this log entry.

The one real design question: how does Memory Service differ from Package 006's Knowledge Service, given both are JSON-backed, versioned, event-publishing CRUD stores? Landed on expiry as the defining, non-overlapping feature. `MemoryRecord` carries an `expires_at` that `KnowledgeRecord` doesn't; Memory Service is for short-term, working-context data (the kind Atlas/Cortex will eventually read and discard), while Knowledge Service stays scoped to durable, human-curated facts with no concept of expiry at all. Implemented expiry lazily rather than with a background sweep thread: `get`/`exists`/`list`/`search` all treat an expired record as absent without touching storage, and only the new `purge_expired()` method physically removes anything, taking the write lock like every other mutation. This keeps Memory Service consistent with "no timers, no background workers" — a principle that's now shown up in the Event Bus's, the Lifecycle Manager's, and now Memory Service's Non-Goals — and sidesteps having to reason about a thread's lifecycle at all.

Considered making `MemoryService` implement `IService` — its natural `start()` would be a good place for a background expiry sweep, which the `MEMORY.md` spec's "Retention Manager" component gestures at. Decided against it. Every `IService` implementer has to track its own internal `LifecycleState` (the interface's `status()` method demands it), which sits alongside whatever the Lifecycle Manager tracks by name for that same service — structurally the same two-sources-of-truth shape that the Package 005 revision spent real effort eliminating for `ServiceDescriptor`. Adopting `IService` for the first time is a genuine architectural decision, not a detail to fold into a data-service package's scope. Left it explicitly out of scope, `MemoryService` registers with the Lifecycle Manager as `REGISTERED` only, exactly like all six other core services to date.

Reused `EventType.MEMORY_UPDATED` as-is rather than adding `MEMORY_CREATED`/`MEMORY_DELETED` the way Package 006 added three new `KNOWLEDGE_*` members. `MEMORY_UPDATED` was clearly reserved for exactly this purpose, and a single event type with an `operation` field in the payload (`created`/`updated`/`deleted`/`purged`) covers every mutation without touching `event_types.py` at all — a smaller footprint than Package 006's approach, and a deliberate response to the "only expected new files should appear" tension flagged in that package's report.

Registered Memory Service as ArgusOS's seventh core service, immediately after the Knowledge Service, since it depends only on the Event Bus (already constructed). `CORE_SERVICES_VERSION` bumped to `"0.0.7"`.

196 tests total (140 from Packages 002-006 plus 56 new: 13 for `MemoryRecord`, 12 for `JSONMemoryStorage`, 30 for `MemoryService`, and 1 extending `test_bootstrap.py`), all passing under `python -m unittest discover`, no pytest anywhere. Coverage on every new module is 100% except `storage.py` at 90% (two untested OS-failure branches in the atomic-write path, same shape as Package 006's).

---

## Package 008 – Scheduler Service

Built ArgusOS's time orchestration layer: `ScheduledTask` (immutable, priority-ordered), three `Trigger` implementations (`OneShotTrigger`, `IntervalTrigger`, `DailyTrigger`, all using a uniform strict-`>` `next_fire_time(after)` contract so no trigger ever refires on the tick immediately after it fires), and `Scheduler`, which executes due tasks only when `tick()` is called — no background thread, no timer, fully deterministic under an explicit `now`.

Hit a real bug early: `schedule()` originally called `datetime.now(timezone.utc)` internally with no override, the same way every prior package's mutation methods do. But Scheduler is different — its own tests need to control *two* points in time (when a task is scheduled, and when it's ticked), not just one. Discovered this the hard way: a batch of tests scheduling `OneShotTrigger(run_at=NOW)` and ticking later all failed, because the sandbox's real clock is mid-2026 while the test fixture's `NOW` constant is January 2026 — `schedule()` was computing `next_run` against the wrong "now" entirely. Fixed by adding an optional `now` parameter to both `schedule()` and `resume()`, mirroring `tick()`'s existing pattern. Once fixed, a second, more interesting bug surfaced: several tests scheduled a `OneShotTrigger` for exactly the same instant as the schedule-time `now`, which correctly returns `None` under strict-`>` semantics (a one-shot due "now" is treated as already elapsed, not still pending) — so the tests themselves were wrong, not the trigger logic. Fixed by scheduling one second after the reference time throughout, which is also a more realistic pattern than "due literally the instant it's created."

`IScheduler` inherits `IService`, as instructed — and as `IService`'s own Package 005 docstring anticipated four packages ago. Gave `start()`/`stop()` real, non-decorative meaning despite the "no background thread" constraint: `tick()` raises `SchedulerError` unless the Scheduler's own state is `RUNNING`, so start/stop genuinely gate execution rather than being bookkeeping for its own sake. Registry operations (`schedule`/`cancel`/`pause`/`resume`/`get_task`/`list_tasks`) are deliberately unaffected by lifecycle state — you can queue up work before the scheduler is started, which matches how real schedulers behave.

Per the Founder's explicit standing instruction from the ADR-0002 discussion — leave `IService` unchanged, use Scheduler as the proving ground, revisit only if the concern is confirmed — implemented Scheduler's `status()` exactly as the interface demands: a self-tracked internal `LifecycleState`, with no connection to whatever a `LifecycleManager` tracks for the same registered name. Then wrote a dedicated test (`IServiceLifecycleDivergenceTests`) that registers a `Scheduler` with a real `LifecycleManager` the way `bootstrap.py` does, calls `scheduler.initialize()`/`start()` directly without telling the `LifecycleManager`, and asserts the two now disagree. They do: `LifecycleManager` still reports `REGISTERED` while the object itself reports `RUNNING`. This is exactly the failure mode ADR-0002 predicted, now demonstrated with a passing, permanent regression test rather than just an argument. `bootstrap.py` itself avoids the problem by construction — it registers Scheduler with the `LifecycleManager` but never calls `scheduler.initialize()`/`start()` — but that's a discipline the framework doesn't enforce; nothing stops a future caller from doing what the test does.

Extended `EventType` with seven new `TASK_*` members for the seven required events, and finally put the long-reserved `SCHEDULER_TICK` (sitting unused since Package 003, the same vintage as `MEMORY_UPDATED`) to work as a per-`tick()` heartbeat, separate from the per-task events. Deliberately did not wire Scheduler's own `initialize()`/`start()` into `bootstrap.py`: nothing in this package ever calls `tick()` automatically, so starting it during bootstrap would have no behavioral effect beyond flipping an internal flag, while also being the first bootstrap-time exercise of the exact `IService`/`LifecycleManager` pairing this ADR is watching for trouble in. Kept bootstrap registration uniform with all seven prior core services (`REGISTERED` only) and proved the `IService` contract works correctly through direct unit tests instead.

281 tests total (196 from Packages 002-007 plus 85 new: 18 for triggers, 10 for `ScheduledTask`/`TaskPriority`, 56 for `Scheduler` (including the divergence test and a test added during coverage cleanup for a task that cancels itself mid-execution), and 1 extending `test_bootstrap.py`), all passing under `python -m unittest discover`, no pytest anywhere. Coverage is 100% on every new module except the abstract `Trigger.next_fire_time` stub (98% on `triggers.py`, same shape as every other ABC in this codebase — the stub body is never reachable since every concrete trigger overrides it).

---

## Package 009 – Intent Router

Built ArgusOS's first text-classification layer, with a hard constraint running through the whole design: deterministic, rule-based parsing only — no AI, no ML, no external libraries, no regex-heavy heuristics. `parser.py`'s `parse_text()` is a pure function over fixed keyword tuples and a fixed precedence order (question mark/word, then command verb, then memory keyword, then schedule keyword, then unknown), using a simple `_starts_with_word` word-boundary check (`normalized == word or normalized.startswith(word + " ")`) rather than anything regex-based. Verified all four of the work order's given examples classify correctly via a direct smoke test before writing a single formal test.

The real design tension in this package was reconciling two requirements that read as being in conflict: `register_handler(intent_name, handler)` must exist as a first-class method, and routing must go through "Intent → Event Bus → Interested services respond" with no direct service invocation. Resolved it by making `register_handler` pure sugar over the Event Bus: it builds a small adapter closure that subscribes to `EventType.INTENT_ROUTED`, filters by `event.payload["name"] == intent_name.value`, reconstructs an `Intent` from the payload, and calls the handler — catching any exception the handler raises and publishing `IntentFailed` instead of letting it propagate, mirroring Scheduler's per-task failure isolation from Package 008. This means `route()` has exactly one invocation mechanism, a single `self._event_bus.publish(...)` call — nothing in `IntentRouter` ever calls a registered handler directly. Proved this structurally, not just by convention: one test (`test_route_only_invokes_handlers_via_the_event_bus_publish_call`) registers a handler *after* `route()` has already published and confirms it never fires, and another (`test_handler_is_not_invoked_directly_by_route_without_event_bus`) registers a handler on a second `IntentRouter` sharing no Event Bus with the first and confirms it's never called — if `route()` had any hidden direct-dispatch path, either test would catch it.

`IIntentRouter` inherits `IService`, per the work order, and `IntentRouter` tracks its own `LifecycleState` the same way `Scheduler` does — `CREATED → INITIALIZING → RUNNING → STOPPED`, raising `IntentError` on illegal transitions. But unlike `Scheduler`, there is nothing here for `start()`/`stop()` to genuinely gate: `parse()`, `route()`, and `register_handler()` all behave identically no matter what lifecycle state the router is in. Rather than paper over this, wrote it into the module docstring explicitly and added a dedicated test (`test_parse_route_and_register_handler_are_not_gated_by_lifecycle_state`) asserting the current, honest behavior — so if a future package adds real gating, that test forces the change to be a deliberate, visible decision rather than an accidental regression. This is a meaningfully different shape than Scheduler's `IService` adoption: Scheduler proved the ADR-0002 duplicate-state risk is real *and* that `IService` can carry genuine behavior; IntentRouter shows `IService` can also be adopted with zero behavioral gate, purely to satisfy an interface contract. Appended this as a second data point to ADR-0002 rather than opening a new ADR — it's additional evidence for the same open question, not a distinct decision.

Extended `EventType` with three new members: `INTENT_PARSED` (fires on every `parse()` call, including `UNKNOWN` results — the router never treats "no match" as a failure), `INTENT_ROUTED` (fires on every successful `route()` call, and is what `register_handler()`'s adapters filter from), and `INTENT_FAILED` (fires for router-level input failures — non-string `parse()` input, non-`Intent` `route()` input — and, separately, for isolated per-handler failures during `register_handler()`'s dispatch). Registered `IntentRouter` as ArgusOS's ninth core service, immediately after Scheduler, following the exact same `REGISTERED`-only bootstrap treatment already established for all eight prior core services — including Scheduler, despite it being the second consecutive package to genuinely implement `IService`.

Caught one design bug of my own while writing the parser test suite: a memory-keyword test used `"note: buy milk"`, expecting `subject="buy milk"` to be extracted. It wasn't — `_starts_with_word` requires the keyword to be followed by a space or end-of-string, so `"note:"` (colon immediately after, no space) doesn't match the leading-keyword check at all and falls through to the weak-confidence substring path instead, with no subject extracted. This is a real, if narrow, limitation of the simple rule-based matcher (no punctuation normalization) — not a bug worth fixing under the "simple rule-based parsing only" constraint, so it's documented as a Known Limitation and the test now asserts the actual, correct-per-spec behavior instead of the behavior I'd initially assumed.

This package was regenerated once. The first attempt was built against a reconstructed workspace whose Package 008 baseline (281 tests) turned out not to match the Founder's live repository's reported count (369). Investigation of the Founder's actual repository (supplied as a zip export) found the discrepancy had nothing to do with any tests being removed: the live repo carries a stray, stale duplicate of parts of itself nested inside `argus/` (`argus/tests/`, `argus/lifecycle/test_lifecycle.py`, `argus/CHANGELOG.md`, `argus/DEVLOG.md`, `argus/factory/`), left over from an earlier merge, plus a `.pytest_cache/` whose cached node-id list — 369 entries — proved the exact arithmetic: 281 canonical + 24 duplicated from `argus/lifecycle/test_lifecycle.py` + 64 duplicated from `argus/tests/*`. Every canonical file this package actually touches (`argus/bootstrap.py`, `argus/events/event_types.py`, `tests/test_bootstrap.py`, `CHANGELOG.md`, `DEVLOG.md`, `factory/ROADMAP.md`, ADR-0002) was verified byte-identical to the reconstructed workspace's version by direct diff before regenerating, so the actual Package 009 implementation carried over unchanged. Per the Founder's explicit instruction, the stray duplicate and legacy pre-Factory files (`argus/brain.py`, `argus/conversation.py`, etc.) were left untouched as out of scope, reserved for a dedicated future cleanup package.

353 tests total in the canonical `tests/` directory (281 from Packages 002–008 plus 71 new: 10 for `Intent`/`IntentType`, 28 for `parse_text`, 33 for `IntentRouter`), all passing under `python -m unittest discover -s tests`, no pytest anywhere in this package's own test suite. A bare `python -m unittest discover` from the repository root reports 377 (353 canonical plus the pre-existing, out-of-scope 24-test duplicate at `argus/lifecycle/test_lifecycle.py`) — expected, not a regression. Coverage is 100% on every new module in `argus/intent/`.

---

## Package 010 – Workflow Engine

Built ArgusOS's first multi-step orchestration layer. The central design tension, stated almost verbatim in the work order, was "coordinates multiple Argus services" versus "the engine must never directly invoke unrelated services outside its defined interfaces." Resolved it the same way Package 009 resolved the Intent Router's analogous tension: `WorkflowEngine` never imports or references `argus.knowledge`, `argus.memory`, `argus.scheduler`, or `argus.intent` anywhere (verified by a test that inspects `engine.py`'s own source for those import strings). A `WorkflowStep`'s `action` is an opaque callable — `Callable[[Mapping], Mapping]` — that the engine invokes without any idea what it does. Coordinating "multiple Argus services" happens *inside* a step's action, constructed by whoever builds the `WorkflowStep` (resolving whatever service it needs from the Container) — never inside the engine itself. This keeps `WorkflowEngine` exactly as decoupled as `IntentRouter`, just via plain callables instead of Event Bus subscriptions, since a workflow step is a synchronous unit of work rather than a fire-and-forget reaction to an event.

`Workflow` is a frozen dataclass, same shape as `ScheduledTask` and `Intent` before it: `steps` gets wrapped in a tuple and `metadata` in `MappingProxyType` in `__post_init__`, so `WorkflowEngine` never mutates a `Workflow` in place — every state transition (`register_workflow`'s initial `PENDING`, `execute()`'s `RUNNING`→`COMPLETED`/`FAILED`, `cancel()`'s `CANCELLED`) goes through `dataclasses.replace()` and a fresh dict entry, exactly like `Scheduler`'s task registry.

`execute()` threads context sequentially: each step's action receives the accumulated context dict and returns the next one, which becomes the input to the following step. A step's exception is caught, wrapped in `WorkflowExecutionError` (constructed but never raised past `execute()` — it exists for symmetry with `TaskExecutionError` and to give the caught error a documented type), and turned into a `WorkflowFailed` event plus a `FAILED` state transition; remaining steps never run. This is a direct copy of Scheduler's per-task failure isolation philosophy from Package 008, applied to *steps within one workflow* instead of *tasks within one tick()*.

The one real architectural decision this package makes on its own initiative: `IWorkflowEngine` needed a `get_workflow()` lookup method beyond the four literally-named "Required Methods" (`register_workflow`/`execute`/`cancel`/`status`), because the work order's own testing requirements list "Status reporting" as an expected coverage area, and `IService.status()` only reports the *engine's* lifecycle state — there is no way to ask "what state is workflow X in?" without a per-workflow lookup. Added `get_workflow(workflow_id) -> Workflow`, documented explicitly as an addition (not a silent scope expansion) in both `interfaces.py`'s docstring and `IMPLEMENTATION_REPORT.md`'s Deviations section — the same treatment given to Scheduler's added `now` parameter in Package 008 and to `get_task()`/`list_tasks()` themselves, which the Scheduler work order *did* name explicitly (Workflow's did not, making this package's addition slightly more of a judgment call, flagged accordingly).

The second real decision: whether `execute()` should be gated on the engine's own `IService` lifecycle state, the way `Scheduler.tick()` is, or left ungated, the way `IntentRouter`'s methods are. Went with genuine gating. `IService`'s own docstring frames `start()`/`stop()` as bracketing "the service's active work," and running a workflow's steps is unambiguously that — a much closer match to Scheduler's `tick()` than to IntentRouter's stateless `parse()`/`route()`. `register_workflow()`, `cancel()`, and `get_workflow()` stay ungated, mirroring Scheduler's registry operations being unaffected by lifecycle state. This makes WorkflowEngine the second of three `IService` adopters (after Scheduler, unlike IntentRouter) where the interface does genuine work, and I appended that finding to ADR-0002 as reinforcing evidence rather than a new complication — three data points now, two showing a real gate, one showing none, all consistent with the original proposed criterion ("adopt `IService` only when `start()`/`stop()` would do real, distinct work").

This package was implemented and verified entirely within a repository provided by the Founder, per an explicit instruction not to commit, tag, push, or declare the package complete — those steps are reserved for the Founder against the live repository. Before writing any code, the supplied repository was verified fresh (not reused from any prior working copy) to confirm it actually contained Package 009's merge (commit `6b2e298`, `argus/intent/` present, 353 canonical tests, `CORE_SERVICES_VERSION == "0.0.9"`) — an earlier upload in this same request had turned out to still be at Package 008, which was caught and reported before any Package 010 code was written, per the Founder's own explicit "stop and ask rather than guessing" instruction.

416 tests total in the canonical `tests/` directory (353 from Packages 002–009 plus 63 new: 14 for `Workflow`/`WorkflowStep`/`WorkflowState`, 48 for `WorkflowEngine`, 1 extending `test_bootstrap.py`), all passing under `python -m unittest discover -s tests`, no pytest anywhere in this package's own test suite. Coverage is 100% on every new module in `argus/workflow/` except the abstract `IWorkflowEngine` method stubs (76% on `interfaces.py` - unreachable, same shape as every other ABC in this codebase).
