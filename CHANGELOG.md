# Changelog

All notable changes to ArgusOS will be documented in this file.

---

# ArgusOS Changelog

---
### Added

- Added `factory/contracts/engineer.md`.
- Established the Engineer Contract governing all human and AI implementations.
### Added

- Added `factory/standards/coding.md`.
- Established coding standards for all ArgusOS implementations.

### Added

- Added `factory/templates/subsystem.md`.
- Standardized the structure for all future subsystem specifications.

### Added

- Added `factory/README.md`.
- Established the onboarding guide for all future contributors.
- Defined the recommended reading order and contribution workflow.

### Added

- Added `factory/workflow.md`.
- Defined the standard engineering workflow for Argus Factory.
- Established the lifecycle from vision through release.

- Added `design/FACTORY.md`.
- Defined the Argus Factory engineering organization.
- Established the standard development workflow.
- Defined engineering roles and responsibilities.

## Argus Factory v0.1

### Added


- Introduced the Argus Factory engineering methodology.
- Added the project charter (`design/ARGUS.md`).
- Added engineering principles (`design/PRINCIPLES.md`).
- Established the foundation for specification-driven development.

## v0.0.1 - The Spark

### Added
- Initial ArgusOS project structure
- Main application entry point
- Interactive command shell
- Git repository initialized
- README, ROADMAP, MISSION, CHARTER, DECISIONS, TODO, and CHANGELOG documents created

---

## v0.0.2 - First AI Conversation

### Added
- Conversation mode
- Local Ollama integration
- AI class
- Conversation class
- Chat command
- Llama 3.1 8B support

### Changed
- Shell can enter and exit conversation mode

---

## v0.0.3 - Identity & System Prompt

### Added
- Identity class
- Dynamic system prompt
- Argus personality
- Version command
- Status command

### Changed
- AI now introduces itself as Argus instead of a generic language model
- Centralized system prompt management

---

## v0.0.4 - Memory Foundation

### Added
- Memory class
- Persistent JSON memory storage
- memories.json
- Memory loading
- Memory saving
- remember() method
- recall() method

### Changed
- Memory subsystem separated from AI and Conversation
- Foundation for long-term persistent memory

---

## v0.0.5 - Interactive Memory

### Added
- remember command
- memories command
- Help menu updated
- Interactive memory storage
- Memory recall from shell

### Changed
- Memory survives application restarts
- CommandManager now manages memory interactions

---

## v0.0.6 - AI Memory Integration

### Added
- AI integration with Memory Manager
- Memory context builder
- Stored memories automatically included in AI system prompt

### Changed
- AI can answer questions using previously stored memories
- Memory became part of every AI conversation
- Architecture updated so AI consumes Identity and Memory together

### Notes
- Established the foundation for ArgusOS.
- Defined the long-term architecture and vision.

---

ArgusOS v0.0.7

Files Changed
--------------
✓ brain.py (new)
✓ conversation.py

Architecture
-------------
Conversation now routes every request through the Brain before AI.

Purpose
--------
Create a decision layer that will eventually route requests to memory, projects, agents, email, packaging tools, and more.

Test Checklist
--------------
☐ Start Argus
☐ Enter conversation mode
☐ Normal conversation works
☐ Memory recall still works
☐ Exit conversation mode

Git Commit
----------
git add .
git commit -m "Argus v0.0.7 - Brain Foundation"
git push
pythion

## v0.0.7 - Brain Foundation

### Added
- Brain class
- Initial decision routing layer
- Conversation now routes all user input through the Brain

### Changed
- Separated decision making from conversation management
- Established architecture for future intent detection
- Created foundation for routing requests to memory, projects, agents, and tools

## v0.0.9 - Intent Detection

### Added
- Brain routes user requests by intent.
- Natural language "remember" command.
- Natural language memory listing.
- Conversation is no longer AI-centric.

### Known Limitations
- Memory retrieval is list-based.
- Argus cannot yet answer questions directly from stored memories.
- Knowledge Engine planned for v0.1.0.

# Design Philosophy

Argus is being built as a modular local AI operating system.

Every subsystem has one responsibility.

Shell
- User interaction

Commands
- Executes user requests

Conversation
- Coordinates dialogue

AI
- Generates responses

Identity
- Defines personality and purpose

Memory
- Stores persistent knowledge

Future systems:
- Brain
- Agents
- Projects
- Voice
- Vision
- Documents
- Packaging Intelligence
---

### Added

- Added `argus/container.py` — minimal dependency injection Container (register/resolve/has).
- Added `argus/configuration.py` — Configuration loader (JSON file with built-in defaults, no Event Bus wiring yet).
- Added `argus/logging_service.py` — stdlib-backed Logging Service initialization, replacing `print()` per the coding standard.
- Added `argus/application.py` — Application lifecycle (start/shutdown) over the Container.
- Added `argus/bootstrap.py` — startup sequence: Container → Configuration → Logging → service registration → Application start.
- Added `config/default.json` — default configuration values consumed by `Configuration.load()`.
- Added unit tests for Container, Configuration, Logging Service, Application, and bootstrap under `tests/`, built entirely on the standard library `unittest` module (no external test runner required). Run with `python -m unittest discover` from the repository root.
- Added `factory/standards/CODING_STANDARD.md` as the single canonical coding standard, consolidating the prior `CODING_STANDARDS.md` and `coding.md`.

### Changed

- `main.py` now runs the Package 002 Bootstrap sequence instead of launching the legacy interactive Shell directly.

### Fixed

- Rewrote `tests/` from pytest-style bare functions to standard library `unittest.TestCase` classes. Architecture review found the original tests undiscoverable by `python -m unittest` / `python -m unittest discover` (unittest's loader only collects `TestCase` subclasses) and dependent on an undeclared `pytest` package. All 21 tests now run with zero external dependencies via `python -m unittest discover`.
- Added `tests/__init__.py` so the test package discovers reliably.

### Removed

- Removed `factory/standards/CODING_STANDARDS.md` and `factory/standards/coding.md`, superseded by `factory/standards/CODING_STANDARD.md`.

### Deprecated

- `factory/packages/001_FOUNDATION.md` is retired as an implementation package; retained as historical planning documentation only. `factory/packages/002_BOOTSTRAP.md` is the authoritative Bootstrap package.

### Known Limitations

- Configuration and Logging implementations are minimal (Bootstrap-stage only). Full CONFIGURATION.md / LOGGING.md compliance (validation, feature flags, hot reload, Event Bus change notification, retention, audit, log querying) is deferred to future implementation packages.
- Event Bus is not initialized in this package; out of scope for Package 002 - Bootstrap.
- The legacy interactive Shell (`argus/shell.py` and related modules) is not invoked from `main.py` pending a future package that reintegrates it on top of this foundation.
- `design/specifications/CORTEX.md` does not yet exist, though Cortex is referenced as one of the five core engines in `INTERFACES.md` and `IMPLEMENTATION_PLAN.md`. Logged as an architectural backlog item; not required for Bootstrap.

---

### Added

- Added `argus/events/` package (Package 003 - Event Bus):
  - `event_types.py` — `EventPriority` and `EventType` enumerations.
  - `event.py` — immutable `Event` dataclass (auto-generated `id`/UTC `timestamp`, empty-mapping `payload`/`metadata` defaults, `payload`/`metadata` wrapped in `MappingProxyType` so handlers cannot mutate them).
  - `interfaces.py` — `IEventBus` abstract contract (`publish`, `subscribe`, `unsubscribe`, `dispatch`) and the `EventHandler` type alias.
  - `exceptions.py` — `EventValidationError`, `SubscriptionError`.
  - `event_bus.py` — `InMemoryEventBus`, a synchronous publish/subscribe implementation preserving handler registration order and rejecting invalid events/handlers/duplicate subscriptions explicitly.
  - `__init__.py` — re-exports the package's public API.
- Added `tests/test_event.py` and `tests/test_event_bus.py` (27 new tests).
- Extended `tests/test_bootstrap.py` with a test confirming the Event Bus resolves from the Container as both `IEventBus` and `InMemoryEventBus`.

### Changed

- `argus/bootstrap.py` now constructs `InMemoryEventBus` (injected with a namespaced logger) and registers it in the Container as `"event_bus"`, immediately after logging initializes. No other part of the startup sequence changed.

### Known Limitations

- The Event Bus is synchronous and in-process only, per Package 003's explicit non-goals (no asyncio, threads, queues, external brokers, persistence, replay, distributed messaging, priority scheduling, middleware, filtering, or network transport).
- `Application.start()` / `Application.shutdown()` do not publish `SYSTEM_STARTED` / `SYSTEM_STOPPING` / `SYSTEM_STOPPED` events. Package 003's objectives call for registering the Event Bus in the DI container, not for wiring it into the existing lifecycle, and Package 002's lifecycle was explicitly preserved as-is. Recommended as a follow-up package.
- `EventType` and `EventPriority` are both defined in `event_types.py` (the module list in the work order named one file for "types"); `event.py` imports both from there.

---

### Added

- Added `argus/services/` package (Package 004 - Service Registry):
  - `service_descriptor.py` — `ServiceState` enum (`REGISTERED`, `ACTIVE`, `STOPPED`) and the immutable `ServiceDescriptor` dataclass (`name`, `instance`, `interface`, `version`, `state`, `metadata`), with `metadata` defaulting to and always wrapped in an immutable `MappingProxyType`.
  - `interfaces.py` — `IServiceRegistry` abstract contract (`register`, `unregister`, `resolve`, `contains`, `list_services`).
  - `exceptions.py` — `ServiceRegistrationError`, `ServiceNotFoundError`.
  - `service_registry.py` — `InMemoryServiceRegistry`, a deterministic, in-memory registry keyed by service name, preserving registration order and rejecting invalid/duplicate registrations and unknown-name lookups explicitly.
  - `__init__.py` — re-exports the package's public API.
- Added `tests/test_service_descriptor.py` and `tests/test_service_registry.py` (24 new tests).
- Extended `tests/test_bootstrap.py` with a test confirming the Service Registry resolves from the Container as both `IServiceRegistry` and `InMemoryServiceRegistry`.

### Changed

- `argus/bootstrap.py` now constructs `InMemoryServiceRegistry` and registers it in the Container as `"service_registry"`, immediately after the Event Bus registers and before the Application is constructed. Bootstrap order is now Container → Configuration → Logging → Event Bus → Service Registry → Application. No other part of the startup sequence changed.

### Known Limitations

- The Service Registry does not auto-populate: Configuration, the Logger, the Event Bus, and the Service Registry itself are registered in the DI Container as before, but none of them are also registered as entries *inside* the Service Registry by this package. Bootstrap Integration in Package 004's spec calls for registering the Service Registry itself using the existing Container pattern, not for populating it; populating it is a natural follow-up once real service-oriented subsystems (Memory, Scheduler, Cortex, Atlas, Hermes) exist to register.
- `ServiceDescriptor.state` has no default value (unlike `metadata`, which the spec explicitly defaults). Every caller must pass a `ServiceState` explicitly; the registry does not infer or transition it, per this package's non-goals (no automatic startup, no health monitoring, no event-driven lifecycle).
- `InMemoryServiceRegistry` takes no logger and publishes no events. Unlike the Event Bus (Package 003), Package 004's specification does not include a Logging section, so no logging dependency was added.

---

### Added

- Added `argus/lifecycle/` package (Package 005 - Service Lifecycle):
  - `lifecycle.py` — `LifecycleState` enum (`CREATED`, `REGISTERED`, `INITIALIZING`, `RUNNING`, `STOPPING`, `STOPPED`, `FAILED`) and `LifecycleManager`, an in-memory, name-keyed state machine that validates every transition and rejects illegal ones explicitly. `stop()` carries a service through `STOPPING` to `STOPPED` in a single call; a `fail()` method (see Engineering Decisions in the Package 005 report) carries any active state to `FAILED`.
  - `interfaces.py` — `IService` abstract contract (`initialize`, `start`, `stop`, `status`), the common lifecycle interface future services (Memory, Scheduler, Cortex, Atlas, Hermes) will implement.
  - `exceptions.py` — `LifecycleError`, `InvalidStateTransitionError` (subclass of `LifecycleError`).
  - `__init__.py` — re-exports the package's public API.
- Added `tests/test_lifecycle.py` (27 new tests).
- Extended `tests/test_bootstrap.py` with tests confirming the Lifecycle Manager resolves from the Container, all five core services are registered in the Service Registry, and all five report `LifecycleState.REGISTERED`.

### Changed

- `argus/bootstrap.py` now constructs `LifecycleManager` and registers it in the Container as `"lifecycle_manager"`, immediately after the Service Registry. It then registers Configuration, the Logger, the Event Bus, the Service Registry, and the Lifecycle Manager itself as `ServiceDescriptor` entries (version `"0.0.5"`, `ServiceState.REGISTERED`) in the Service Registry, and by name in the Lifecycle Manager (`LifecycleState.REGISTERED`). None of them are initialized or started. Bootstrap order is now Container → Configuration → Logging → Event Bus → Service Registry → Lifecycle Manager → Register Core Services → Application. No other part of the startup sequence changed.

### Known Limitations

- No existing class (`Configuration`, the stdlib `Logger`, `InMemoryEventBus`, `InMemoryServiceRegistry`, `LifecycleManager`) implements `IService`. Package 005 defines the contract; retrofitting Packages 002-004's services onto it is future work.
- Core services are registered but never initialized or started in this package, per the work order's explicit instruction. They remain in `REGISTERED` until a future package calls `lifecycle_manager.initialize(...)` / `.start(...)` for them.
- `LifecycleManager` and `InMemoryServiceRegistry` now both track a notion of "state" for the same five service names — `ServiceDescriptor.state` (Package 004's coarse `ServiceState`: `REGISTERED`/`ACTIVE`/`STOPPED`) and `LifecycleManager`'s fine-grained `LifecycleState`. They are set together in `_register_core_services` but are otherwise two independent mechanisms with no synchronization; reconciling them (or deciding they should stay separate) is an open architectural question, not addressed by this package.

---

### Changed (Package 005 — Architectural Revision)

Architecture review found that Package 005 introduced a duplicate, unsynchronized runtime state model: `ServiceDescriptor.state` (`ServiceState`, from Package 004) and the Lifecycle Manager's `LifecycleState` (Package 005) both tracked "state" for the same five core services, set together in `bootstrap.py` but never reconciled — flagged as a known limitation in the original Package 005 delivery. This revision eliminates the duplicate:

- Removed the `state: ServiceState` field from `ServiceDescriptor` (`argus/services/service_descriptor.py`). `ServiceDescriptor` is now purely identity and descriptive data: `name`, `instance`, `interface`, `version`, `metadata`.
- Removed the `ServiceState` enum entirely (`REGISTERED`/`ACTIVE`/`STOPPED`) — nothing else referenced it.
- Removed `ServiceState` from `argus/services/__init__.py`'s exports.
- `argus/bootstrap.py`'s `_register_core_services` no longer passes `state=` when constructing each core service's `ServiceDescriptor`; it still calls `lifecycle_manager.register(name)` for each, which remains the sole place runtime lifecycle state is recorded.
- Updated `tests/test_service_descriptor.py` (removed the `ServiceState` membership test, added a test asserting `ServiceDescriptor` has no `state` attribute at all) and `tests/test_service_registry.py`'s descriptor-building helper (no longer passes `state=`).

The Lifecycle Manager (`argus.lifecycle.LifecycleManager`) is now the sole owner of runtime lifecycle state for every service ArgusOS tracks. The Service Registry answers "what services exist and what do they look like"; the Lifecycle Manager answers "what state is this service in right now." This is a breaking change to `ServiceDescriptor`'s constructor (the `state` argument no longer exists); per the revision request, backward compatibility was not preserved here since eliminating the duplicate source of truth took priority, and the only callers were within this repository (`bootstrap.py` and the test suite), both updated.

Test count is unchanged at 99 (one `ServiceState`-specific test removed, one state-absence test added).

---

### Added

- Added `argus/knowledge/` package (Package 006 - Knowledge Service):
  - `knowledge_record.py` — `KnowledgeRecord`, an immutable dataclass (`id`, `category`, `key`, `value`, `created_at`, `updated_at`, `version`) representing one fact in ArgusOS's persistent knowledge store. `id`/`created_at`/`updated_at` auto-generate; `version` defaults to `1`.
  - `interfaces.py` — `IKnowledgeStorage` (`list_categories`, `load`, `save`) and `IKnowledgeService` (`put`, `get`, `exists`, `delete`, `list`, `update`).
  - `storage.py` — `JSONKnowledgeStorage`, storing each category as `knowledge/<category>.json` (a JSON array), with every write performed atomically (temp file + `os.replace`).
  - `knowledge_service.py` — `KnowledgeService`, the CRUD orchestrator: loads every category into a single key-indexed in-memory map at construction, guards all writes (`put`/`update`/`delete`) with a `threading.Lock` (reads remain unlocked, per this package's v1 scope), and publishes a Knowledge event on the Event Bus after each successful write, once the lock is released.
  - `exceptions.py` — `KnowledgeError`, `KnowledgeNotFoundError`, `DuplicateKnowledgeError`.
  - `__init__.py` — re-exports the package's public API.
- Added six seed category files: `knowledge/founder.json`, `knowledge/businesses.json`, `knowledge/architecture.json`, `knowledge/projects.json`, `knowledge/tasks.json`, `knowledge/conversations.json`, each initialized to `[]`.
- Extended `argus/events/event_types.py`'s `EventType` enum with `KNOWLEDGE_CREATED`, `KNOWLEDGE_UPDATED`, `KNOWLEDGE_DELETED`, per that module's own "this module is the single place new event types are added" scope note (Package 003).
- Added `tests/test_knowledge_record.py` (8 new tests), `tests/test_storage.py` (12 new tests), `tests/test_knowledge_service.py` (20 new tests, including two covering empty-key/empty-category validation).
- Extended `tests/test_bootstrap.py` with a test confirming the Knowledge Service resolves from the Container, and updated the six-service assertions already covered by the existing registry/lifecycle tests (1 new test).

### Changed

- `argus/bootstrap.py` now constructs `JSONKnowledgeStorage` and `KnowledgeService` (depends on the Event Bus) immediately after the Lifecycle Manager, and registers `KnowledgeService` in the Container as `"knowledge_service"`. Bootstrap order is now Container → Configuration → Logging → Event Bus → Service Registry → Lifecycle Manager → Knowledge Service → Register Core Services → Application. `_register_core_services` now registers six core services (added Knowledge Service) as `ServiceDescriptor` entries in the Service Registry and by name in the Lifecycle Manager (`LifecycleState.REGISTERED`); `CORE_SERVICES_VERSION` was bumped to `"0.0.6"`, this work order's version target.

### Known Limitations

- `KnowledgeService` does not implement `IService` and is not initialized or started by the Lifecycle Manager in this package — it is registered only, matching the treatment of all other core services to date.
- `JSONKnowledgeStorage._persist_category` rebuilds and rewrites a category's entire JSON file on every write (`put`/`update`/`delete`), scanning the full in-memory index each time. O(n) in the number of records in that category; acceptable for this package's intentionally simple v1 scope, but will not scale to large per-category record counts without a future revision.
- `KnowledgeRecord.value` is not deep-frozen: only the dataclass's own fields are immutable. If a caller stores a mutable object (e.g. a `dict`) as `value` and keeps a reference to it, mutating that object in place bypasses `KnowledgeService`'s write path entirely (no lock, no persistence, no event). Documented, not fixed, per this package's "intentionally simple" scope.
- Two OS-level failure branches in `JSONKnowledgeStorage.save` (the `os.replace` failure path and the leftover-temp-file cleanup path) are not covered by unit tests, since triggering them requires mocking filesystem failures. Coverage for `argus/knowledge/storage.py` is 91%; every other new module is 100%.

---

### Added

- Added `argus/memory/` package (Package 007 - Memory Service):
  - `memory_record.py` — `MemoryRecord`, an immutable dataclass (`id`, `key`, `value`, `created_at`, `updated_at`, `expires_at`, `version`) representing one item of short-term working memory. `expires_at` defaults to `None` (never expires); `is_expired(now=...)` reports whether a record is past its expiry.
  - `interfaces.py` — `IMemoryStorage` (`load`, `save`) and `IMemoryService` (`put`, `get`, `exists`, `delete`, `update`, `list`, `search`, `purge_expired`).
  - `storage.py` — `JSONMemoryStorage`, a single-file JSON store (`memory/memory_store.json`, no categories — unlike Package 006's per-category files, since Memory has no category concept), with every write performed atomically (temp file + `os.replace`).
  - `memory_service.py` — `MemoryService`, the CRUD-plus-expiry orchestrator: loads every record into a key-indexed in-memory map at construction, guards all writes (`put`/`update`/`delete`/`purge_expired`) with a `threading.Lock` (reads remain unlocked), treats any record whose `expires_at` has passed as invisible to `get`/`exists`/`list`/`search` without physically deleting it, and publishes `EventType.MEMORY_UPDATED` after each successful write with an `operation` field (`created`/`updated`/`deleted`/`purged`) distinguishing the mutation.
  - `exceptions.py` — `MemoryServiceError` (base; named to avoid shadowing the built-in `MemoryError`), `MemoryNotFoundError`, `DuplicateMemoryError`.
  - `__init__.py` — re-exports the package's public API.
- Added `memory/memory_store.json`, seeded to `[]`.
- Added `factory/packages/007_MEMORY_SERVICE.md`, the formal work order for this package, including a dependency-graph audit of every unimplemented engine in `design/specifications/` and the rationale for choosing Memory Service over the alternatives (see that file's "Why Package 007, Not an Alternative" section).
- Added `tests/test_memory_record.py` (13 new tests), `tests/test_memory_storage.py` (12 new tests), `tests/test_memory_service.py` (30 new tests).
- Extended `tests/test_bootstrap.py` with a test confirming the Memory Service resolves from the Container (1 new test).

### Changed

- `argus/bootstrap.py` now constructs `JSONMemoryStorage` and `MemoryService` (depends on the Event Bus) immediately after the Knowledge Service, and registers `MemoryService` in the Container as `"memory_service"`. Bootstrap order is now Container → Configuration → Logging → Event Bus → Service Registry → Lifecycle Manager → Knowledge Service → Memory Service → Register Core Services → Application. `_register_core_services` now registers seven core services (added Memory Service) as `ServiceDescriptor` entries in the Service Registry and by name in the Lifecycle Manager (`LifecycleState.REGISTERED`); `CORE_SERVICES_VERSION` was bumped to `"0.0.7"`.
- No changes to `argus/events/event_types.py` this package: `EventType.MEMORY_UPDATED` has been present since Package 003 and was reused as-is, distinguishing the four mutation kinds via a payload `operation` field rather than adding new enum members.

### Known Limitations

- `MemoryService` does not implement `IService` — this was deliberately deferred rather than adopted opportunistically; see `factory/packages/007_MEMORY_SERVICE.md`'s Out of Scope section for the reasoning (adopting `IService` anywhere risks reintroducing the class of duplicate-state problem the Package 005 revision eliminated, and deserves its own dedicated decision).
- Expired records are only removed from storage when `purge_expired()` is called explicitly; there is no background sweep. Until `purge_expired()` runs, expired-but-unpurged records still occupy space in `memory/memory_store.json` (though they are invisible to every read path).
- `search()` is a simple case-insensitive substring match on `key`, not semantic search. Semantic search is explicitly listed as a Future Enhancement for Atlas, not Memory, in `design/specifications/ATLAS.md`.
- Two OS-level failure branches in `JSONMemoryStorage.save` are not covered by unit tests, for the same reason noted for `JSONKnowledgeStorage` in the Package 006 entry above. Coverage for `argus/memory/storage.py` is 90%; every other new module is 100%.

---

### Added

- Added `argus/scheduler/` package (Package 008 - Scheduler Service):
  - `task.py` — `ScheduledTask`, an immutable dataclass (`id`, `name`, `callback`, `trigger`, `priority`, `enabled`, `created_at`, `next_run`, `last_run`), and `TaskPriority` (`LOW`/`NORMAL`/`HIGH`/`CRITICAL`, independent of `argus.events.EventPriority`).
  - `triggers.py` — `Trigger` (the common contract: `next_fire_time(after) -> Optional[datetime]`, strict `>` semantics throughout), `OneShotTrigger`, `IntervalTrigger` (fixed-delay, not fixed-rate), `DailyTrigger`. No cron support, no time-zone conversion, no missed-schedule recovery — all explicitly deferred.
  - `interfaces.py` — `IScheduler`, inheriting `IService` (`schedule`, `cancel`, `pause`, `resume`, `get_task`, `list_tasks`, `tick`, plus the inherited `initialize`/`start`/`stop`/`status`).
  - `scheduler.py` — `Scheduler`: in-memory task registry, deterministic `tick()`-driven execution (no background thread), write-locked mutations, priority-then-next_run execution ordering, lazy one-shot exhaustion, and publishes a task lifecycle event for every operation plus `EventType.SCHEDULER_TICK` once per `tick()` call.
  - `exceptions.py` — `SchedulerError`, `TaskAlreadyExists`, `TaskNotFound`, `InvalidTrigger`, `TaskExecutionError`.
  - `__init__.py` — re-exports the package's public API.
- Added `factory/packages/008_SCHEDULER_SERVICE.md`, including the scope reduction relative to `design/specifications/SCHEDULER.md` (no Navigator dependency; `callback` is a plain Python callable in v1) and the IService adoption rationale.
- Extended `argus/events/event_types.py`'s `EventType` with seven new members: `TASK_SCHEDULED`, `TASK_STARTED`, `TASK_COMPLETED`, `TASK_FAILED`, `TASK_CANCELLED`, `TASK_PAUSED`, `TASK_RESUMED`. The existing `SCHEDULER_TICK` (reserved, unused since Package 003) is now used as a per-`tick()` heartbeat.
- Added `tests/test_triggers.py` (18 new tests), `tests/test_scheduler_task.py` (10 new tests), `tests/test_scheduler.py` (55 new tests, including an empirical test proving the ADR-0002 duplicate-state concern is real, not just theoretical).
- Extended `tests/test_bootstrap.py` with a test confirming the Scheduler resolves from the Container (1 new test).

### Changed

- `argus/bootstrap.py` now constructs `Scheduler` (depends on the Event Bus) immediately after the Memory Service, and registers it in the Container as `"scheduler"`. Bootstrap order is now ... → Memory Service → Scheduler → Register Core Services → Application. `_register_core_services` now registers eight core services; `CORE_SERVICES_VERSION` bumped to `"0.0.8"`. Scheduler's own `initialize()`/`start()` are deliberately **not** called during bootstrap — see Engineering Decisions.

### ADR Update

- ADR-0002 (`design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`) remains `Proposed`, per standing instruction. Scheduler is its proving ground, per that ADR's own recommendation. Finding: **the predicted duplicate-state risk is confirmed empirically**, not just theoretical — see `IMPLEMENTATION_REPORT.md`'s ADR Recommendation section and `tests/test_scheduler.py::IServiceLifecycleDivergenceTests` for the reproducing test.

### Known Limitations

- Scheduler has no background thread; nothing calls `tick()` automatically. A future package (or a direct caller) must drive `tick()` on its own schedule.
- `ScheduledTask.callback` is a plain Python callable, not dispatched through Navigator (which does not exist yet).
- No retry/backoff for failing callbacks: a failure publishes `TaskFailed` and, for recurring triggers, is simply rescheduled for its normal next occurrence.
- `IntervalTrigger` is fixed-delay, not fixed-rate: a late `tick()` call causes subsequent fires to drift later rather than catching up to a grid.
- Confirmed: Scheduler's own `IService` state and a `LifecycleManager`'s per-name tracking of the same registered name can diverge if one is updated without the other, exactly as ADR-0002 predicted.

## Package 009 - Intent Router

### Added

- Added `argus/intent/` package (Package 009 - Intent Router):
  - `intent.py` - `IntentType` (`QUESTION`/`COMMAND`/`MEMORY`/`SCHEDULE`/`UNKNOWN`) and `Intent`, an immutable dataclass (`id`, `name`, `confidence`, `entities`, `parameters`, `timestamp`).
  - `parser.py` - `parse_text(text) -> ParsedText`: pure, dependency-free, rule-based classification (fixed keyword lists, fixed precedence order: question mark/word, then command verb, then memory keyword, then schedule keyword, then unknown). No AI, no machine learning, no regex.
  - `interfaces.py` - `IIntentRouter`, inheriting `IService` (`parse`, `route`, `register_handler`, plus the inherited `initialize`/`start`/`stop`/`status`).
  - `router.py` - `IntentRouter`: `parse()` classifies text and publishes `IntentParsed`; `route()` publishes `IntentRouted` as its *only* invocation mechanism (no direct service calls); `register_handler()` is sugar over `IEventBus.subscribe()` that filters by intent name, reconstructs the routed `Intent`, and isolates handler failures (publishing `IntentFailed` instead of propagating).
  - `exceptions.py` - `IntentError`, `IntentParseError`, `InvalidIntentError`, `DuplicateHandlerError`.
  - `__init__.py` - re-exports the package's public API.
- Added `factory/packages/009_INTENT_ROUTER.md`, including a note that no `design/specifications/INTENT_ROUTER.md` exists (this package implements the Founder's explicit work order directly, the same situation as Package 002).
- Extended `argus/events/event_types.py`'s `EventType` with three new members: `INTENT_PARSED`, `INTENT_ROUTED`, `INTENT_FAILED`.
- Added `tests/test_intent.py` (10 new tests), `tests/test_intent_parser.py` (28 new tests), `tests/test_intent_router.py` (33 new tests).
- Extended `tests/test_bootstrap.py` with a test confirming the Intent Router resolves from the Container (1 new test).

### Changed

- `argus/bootstrap.py` now constructs `IntentRouter` (depends on the Event Bus) immediately after Scheduler, and registers it in the Container as `"intent_router"`. Bootstrap order is now ... -> Scheduler -> Intent Router -> Register Core Services -> Application. `_register_core_services` now registers nine core services; `CORE_SERVICES_VERSION` bumped to `"0.0.9"`. IntentRouter's own `initialize()`/`start()` are deliberately **not** called during bootstrap, for the same reasoning already applied to Scheduler in Package 008.

### ADR Update

- ADR-0002 (`design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`) remains `Proposed`, per standing instruction. IntentRouter is a second `IService` adopter, appended as a further empirical data point: unlike Scheduler's `tick()`, none of IntentRouter's `parse()`/`route()`/`register_handler()` are gated by lifecycle state at all - `IService` is satisfied here purely to meet an explicit interface requirement, with no genuine behavioral gate. See `IMPLEMENTATION_REPORT.md`'s ADR Recommendation section.

### Known Limitations

- `IntentRouter`'s `IService` implementation has no genuine behavioral gate: `parse()`/`route()`/`register_handler()` behave identically regardless of lifecycle state.
- Classification is a fixed keyword/precedence scheme with no punctuation normalization: a keyword immediately followed by punctuation (e.g. `"note: buy milk"`) does not satisfy the word-boundary check and falls through to weak-confidence substring matching with no `subject` entity extracted.
- No confidence levels beyond the three fixed constants (1.0 strong / 0.6 weak / 0.0 no-match).
- `register_handler()`'s duplicate check is exact `(intent_name, handler)` identity; two distinct handler objects with identical behavior are not considered duplicates.

## Package 010 - Workflow Engine

### Added

- Added `argus/workflow/` package (Package 010 - Workflow Engine):
  - `state.py` - `WorkflowState` (`PENDING`/`RUNNING`/`COMPLETED`/`FAILED`/`CANCELLED`).
  - `workflow.py` - `WorkflowStep` (a name paired with a deterministic `StepAction` callable) and `Workflow`, an immutable dataclass (`id`, `name`, `state`, `steps`, `created_at`, `started_at`, `completed_at`, `metadata`).
  - `interfaces.py` - `IWorkflowEngine`, inheriting `IService` (`register_workflow`, `execute`, `cancel`, `get_workflow`, plus the inherited `initialize`/`start`/`stop`/`status`).
  - `engine.py` - `WorkflowEngine`: in-memory workflow registry; `execute()` runs a `PENDING` workflow's steps strictly in order, threading each step's returned context into the next, gated on the engine's own `IService` state being `RUNNING`; a failing step publishes `WorkflowFailed`, marks the workflow `FAILED`, and stops - the exception never propagates out of `execute()`.
  - `exceptions.py` - `WorkflowError`, `WorkflowNotFoundError`, `DuplicateWorkflowError`, `InvalidWorkflowError`, `WorkflowExecutionError`.
  - `__init__.py` - re-exports the package's public API.
- Added `factory/packages/010_WORKFLOW_ENGINE.md`, including a note that no `design/specifications/WORKFLOW.md` exists (this package implements the Founder's explicit work order directly, the same situation as Packages 002 and 009).
- Extended `argus/events/event_types.py`'s `EventType` with six new members: `WORKFLOW_STARTED`, `WORKFLOW_STEP_STARTED`, `WORKFLOW_STEP_COMPLETED`, `WORKFLOW_COMPLETED`, `WORKFLOW_FAILED`, `WORKFLOW_CANCELLED`.
- Added `tests/test_workflow.py` (14 new tests), `tests/test_workflow_engine.py` (48 new tests).
- Extended `tests/test_bootstrap.py` with a test confirming the Workflow Engine resolves from the Container (1 new test).

### Changed

- `argus/bootstrap.py` now constructs `WorkflowEngine` (depends on the Event Bus) immediately after the Intent Router, and registers it in the Container as `"workflow_engine"`. Bootstrap order is now ... -> Intent Router -> Workflow Engine -> Register Core Services -> Application. `_register_core_services` now registers ten core services; `CORE_SERVICES_VERSION` bumped to `"0.0.10"`. WorkflowEngine's own `initialize()`/`start()` are deliberately **not** called during bootstrap, for the same reasoning already applied to Scheduler and IntentRouter - with the added consequence that `execute()` will raise until a caller starts the engine directly, since (unlike IntentRouter) `execute()` is genuinely gated on the engine's own `RUNNING` state.

### ADR Update

- ADR-0002 (`design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`) remains `Proposed`, per standing instruction. WorkflowEngine is a third `IService` adopter, appended as a further empirical data point: its `execute()` is genuinely gated on lifecycle state, reinforcing Scheduler's finding rather than IntentRouter's - two of three real adopters to date use `IService` for a genuine behavioral gate. See `IMPLEMENTATION_REPORT.md`'s ADR Recommendation section.

### Known Limitations

- Steps execute strictly sequentially with no parallelism, branching, or conditional logic.
- No retry/backoff for a failing step; a failure stops the entire workflow.
- Workflows are held only in memory; nothing persists across process restarts.
- A step's action is an opaque callable with no declared input/output schema beyond "receives a context mapping, returns a context mapping" - the engine cannot validate a step's contract beyond checking it is callable.
- `cancel()` only succeeds against a `PENDING` workflow; since `execute()` is fully synchronous, a workflow is never observably `RUNNING` to an external caller, making mid-execution cancellation structurally impossible in this version (by design, per the work order's "no threading, no background execution").

## Package 011 - Conversation Manager

### Added

- Added `argus/conversation/` package (Package 011 - Conversation Manager):
  - `state.py` - `ConversationState` (`NEW`/`ACTIVE`/`WAITING`/`CLOSED`).
  - `message.py` - `ConversationRole` (`USER`/`ASSISTANT`/`SYSTEM`) and `ConversationMessage`, an immutable dataclass (`id`, `timestamp`, `role`, `content`, `metadata`).
  - `session.py` - `ConversationSession`, an immutable dataclass (`id`, `created_at`, `updated_at`, `state`, `metadata`, `messages`).
  - `interfaces.py` - `IConversationManager`, inheriting `IService` (`start_session`, `end_session`, `receive`, `history`, `active_session`, plus the inherited `initialize`/`start`/`stop`/`status`).
  - `manager.py` - `ConversationManager`: in-memory session registry (one active session at a time in v1); `receive()` appends the user message, delegates classification to `IIntentRouter.parse()`, optionally delegates execution to `IWorkflowEngine.execute()` when a `workflow_id` is supplied and registered, generates a deterministic templated response keyed on the resolved intent, and appends the assistant message - never performs AI reasoning, never parses intents itself, never executes workflow steps itself.
  - `exceptions.py` - `ConversationError`, `NoActiveSessionError`, `SessionNotFoundError`, `ActiveSessionExistsError`, `InvalidMessageError`.
  - `__init__.py` - re-exports the package's public API.
- Added `factory/packages/011_CONVERSATION_MANAGER.md`, including a note that no `design/specifications/CONVERSATION.md` exists (this package implements the Founder's explicit work order directly, the same situation as Packages 002, 009, and 010).
- Extended `argus/events/event_types.py`'s `EventType` with six new members: `CONVERSATION_STARTED`, `MESSAGE_RECEIVED`, `INTENT_RESOLVED`, `WORKFLOW_EXECUTED`, `RESPONSE_GENERATED`, `CONVERSATION_ENDED`.
- Added `tests/test_conversation.py` (21 new tests), `tests/test_conversation_manager.py` (49 new tests).
- Extended `tests/test_bootstrap.py` with a test confirming the Conversation Manager resolves from the Container (1 new test).
- Synchronized the repository's pre-existing stray duplicate `argus/tests/test_bootstrap.py`: added `"conversation_manager"` to its `CORE_SERVICE_NAMES` tuple only, per the Founder's explicit instruction to keep both bootstrap registration tests synchronized whenever a new core service is added. No other line in that file, and no other duplicate-tree file, was touched.

### Changed

- `argus/bootstrap.py` now constructs `ConversationManager` (depends on the Event Bus, the Intent Router, and the Workflow Engine) immediately after the Workflow Engine, and registers it in the Container as `"conversation_manager"`. Bootstrap order is now ... -> Workflow Engine -> Conversation Manager -> Register Core Services -> Application. `_register_core_services` now registers eleven core services. `CORE_SERVICES_VERSION` remains `"0.1.0"` - per the Founder's standing policy, this constant always reflects the repository's last actual release (git tag + committed history), not the package currently being implemented; it advances only after Package 011 is integrated, validated, committed, and tagged, which has not yet happened. An initial delivery of this package mistakenly bumped it to `"0.1.1"` during implementation; corrected back to `"0.1.0"` per the Founder's explicit instruction - see `IMPLEMENTATION_REPORT.md`. ConversationManager's own `initialize()`/`start()` are deliberately **not** called during bootstrap, for the same reasoning already applied to Scheduler, IntentRouter, and WorkflowEngine.

### ADR Update

- ADR-0002 (`design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`) remains `Proposed`, per standing instruction. ConversationManager is a fourth `IService` adopter, appended as a further empirical data point: its `receive()` is genuinely gated on lifecycle state, reinforcing the pattern set by Scheduler and WorkflowEngine - three of four real adopters to date use `IService` for a genuine behavioral gate. See `IMPLEMENTATION_REPORT.md`'s ADR Recommendation section.

### Known Limitations

- Response generation is a small, fixed set of deterministic templates keyed on the resolved Intent's name - not natural language generation.
- No automatic mapping from a resolved Intent to a workflow_id; the caller of `receive()` must supply `workflow_id` explicitly for execution to be delegated.
- Exactly one active session at a time (Version 1 constraint); starting a second session while one is active raises `ActiveSessionExistsError`.
- Sessions and messages are held only in memory; nothing persists across process restarts.
- `receive()` does not call `IIntentRouter.route()` or `register_handler()` - only `parse()`'s direct return value is used, so other Event Bus subscribers to `IntentRouted` are not triggered by a conversation turn.

## Package 012 - Intent Dispatcher

### Added

- Added `argus/dispatcher/` package (Package 012 - Intent Dispatcher):
  - `action.py` - `Action`, an abstract base class declaring one method (`execute()`) plus a `kind` label, and `WorkflowAction`, Version 1's only concrete Action, which delegates `execute()` to an injected `IWorkflowEngine.execute()` call for a given `workflow_id`.
  - `mapping.py` - `DEFAULT_WORKFLOW_IDS`: a pure-data table pairing each `IntentType` with the conventional Version 1 workflow_id `bootstrap.py` registers a `WorkflowAction` against for it (`answer_workflow`, `command_workflow`, `memory_workflow`, `reminder_workflow`, `unknown_handler_workflow`). Contains no service dependency and constructs no Action itself.
  - `interfaces.py` - `IIntentDispatcher`, inheriting `IService` (`register_mapping`, `remove_mapping`, `resolve`, `dispatch`, `list_mappings`, plus the inherited `initialize`/`start`/`stop`/`status`).
  - `dispatcher.py` - `IntentDispatcher`: an in-memory `IntentType -> Action` registry (`register_mapping`/`remove_mapping`/`list_mappings`, all ungated) plus `resolve()` (a pure lookup) and `dispatch()` (resolves an Intent to its Action and calls `action.execute()`, publishing `IntentDispatched`, `ActionResolved`, `WorkflowSelected` (WorkflowAction only), `DispatchStarted`, and then `DispatchCompleted` or `DispatchFailed`). Never imports `argus.workflow`, `argus.intent.router`, `argus.intent.parser`, or `argus.conversation` - verified structurally by test.
  - `exceptions.py` - `DispatcherError`, `InvalidIntentError`, `InvalidActionError`, `NoMappingError`, `DuplicateMappingError`, `MappingNotFoundError`, `ActionExecutionError`.
  - `__init__.py` - re-exports the package's public API.
- Added `factory/packages/012_INTENT_DISPATCHER.md`, including a note that no `design/specifications/DISPATCHER.md` exists (this package implements the Founder's explicit work order directly, the same situation as Packages 002, 009, 010, and 011).
- Extended `argus/events/event_types.py`'s `EventType` with six new members: `INTENT_DISPATCHED`, `ACTION_RESOLVED`, `WORKFLOW_SELECTED`, `DISPATCH_STARTED`, `DISPATCH_COMPLETED`, `DISPATCH_FAILED`.
- Added `tests/test_dispatcher.py` (19 new tests: `Action`/`WorkflowAction`/`DEFAULT_WORKFLOW_IDS`), `tests/test_intent_dispatcher.py` (45 new tests: `IntentDispatcher` itself).
- Extended `tests/test_bootstrap.py` with two new tests confirming the Intent Dispatcher resolves from the Container and has all five initial mappings registered.
- Synchronized the repository's pre-existing stray duplicate `argus/tests/test_bootstrap.py`: added `"intent_dispatcher"` to its `CORE_SERVICE_NAMES` tuple only, per the standing instruction (introduced in Package 011) to keep both bootstrap registration tests synchronized whenever a new core service is added. No other line in that file, and no other duplicate-tree file, was touched.

### Changed

- `argus/bootstrap.py` now constructs `IntentDispatcher` (depends on the Event Bus only) immediately after the Conversation Manager, and registers it in the Container as `"intent_dispatcher"`. Bootstrap also constructs five `WorkflowAction` instances - one per `argus.dispatcher.mapping.DEFAULT_WORKFLOW_IDS` entry, each wrapping the already-constructed `WorkflowEngine` - and registers them as the dispatcher's five Version 1 "Initial mappings" via `register_mapping()`. Bootstrap order is now ... -> Conversation Manager -> Intent Dispatcher -> Register Core Services -> Application. `_register_core_services` now registers twelve core services. `CORE_SERVICES_VERSION` remains `"0.1.1"` - unchanged by this package, per its own explicit Version Policy (the constant already matched the repository's actual release, `v0.1.1`, before this package began - see `IMPLEMENTATION_REPORT.md`'s Repository Verification Note for the correction that preceded this package). IntentDispatcher's own `initialize()`/`start()` are deliberately **not** called during bootstrap, for the same reasoning already applied to Scheduler, IntentRouter, WorkflowEngine, and ConversationManager.

### ADR Update

- ADR-0002 (`design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`) remains `Proposed`, per standing instruction. IntentDispatcher is a fifth `IService` adopter, appended as a further empirical data point: its `dispatch()` is genuinely gated on lifecycle state, reinforcing the pattern set by Scheduler, WorkflowEngine, and ConversationManager - four of five real adopters to date use `IService` for a genuine behavioral gate. See `IMPLEMENTATION_REPORT.md`'s ADR Recommendation section.

### Known Limitations

- The five Version 1 "Initial mappings" reference `workflow_id`s (`answer_workflow`, etc.) that no other package has registered an actual Workflow against - dispatching any of them raises `ActionExecutionError` (wrapping `WorkflowNotFoundError`) until some future package registers real workflows under those ids. This is expected, by-design Version 1 behavior, not a defect - see `factory/packages/012_INTENT_DISPATCHER.md`.
- `IntentDispatcher` is not wired into `ConversationManager` - the two compose only if some future caller explicitly feeds a resolved Intent from one into the other; `manager.py` was not modified by this package.
- Mappings are held only in memory; nothing persists across process restarts.
- `IntentDispatcher` does not import `IWorkflowEngine` directly (see the Architectural Note in `factory/packages/012_INTENT_DISPATCHER.md`) - this is a deliberate design choice for extensibility, not a limitation, but is called out here since it differs from ConversationManager's (Package 011) direct-dependency pattern.

## Package 013 - Capability Registry

### Added

- Added `argus/capability/` package (Package 013 - Capability Registry):
  - `capability.py` - `Capability`, an immutable dataclass describing one thing ArgusOS knows how to do: `name`, `description`, `intent_types`, `action_kind`, `id` (auto-generated), `workflow_id` (Version 1), `enabled` (default `True`), `metadata`. Pure data - holds no live service reference and does not validate its own fields.
  - `interfaces.py` - `ICapabilityRegistry`, a plain `ABC` (deliberately NOT inheriting `IService` - see the ADR Update below): `register`, `unregister`, `get`, `find_by_intent_type`, `list_capabilities`, `contains`.
  - `registry.py` - `CapabilityRegistry`: an in-memory registry of `Capability` objects keyed by id. `register()` validates a Capability's fields (non-empty id/name/intent_types/action_kind, and a `workflow_id` when `action_kind` is `"workflow"`) before accepting it - the one piece of business logic this module contains, and it is validation, not execution. Publishes `CapabilityRegistered`/`CapabilityUnregistered` on success only.
  - `exceptions.py` - `CapabilityError`, `InvalidCapabilityError`, `DuplicateCapabilityError`, `CapabilityNotFoundError`.
  - `__init__.py` - re-exports the package's public API.
- Added `factory/packages/013_CAPABILITY_REGISTRY.md`, including a note that no `design/specifications/CAPABILITY.md` exists (this package implements the Founder's explicit work order directly, the same situation as Packages 002, 009, 010, 011, and 012).
- Extended `argus/events/event_types.py`'s `EventType` with two new members: `CAPABILITY_REGISTERED`, `CAPABILITY_UNREGISTERED`.
- Added `argus/dispatcher/action.py::build_action_from_capability(capability, *, workflow_engine)`: translates a Capability's metadata into a constructed `Action`. Version 1 supports only `action_kind == "workflow"` (raises `InvalidActionError` otherwise). This is the only place in `argus/dispatcher/` that imports `argus.capability`.
- Added `tests/test_capability.py` (16 new tests: the `Capability` model), `tests/test_capability_registry.py` (37 new tests: `CapabilityRegistry`).
- Extended `tests/test_bootstrap.py` with three new tests confirming the Capability Registry resolves from the Container, has an initial enabled capability for every `IntentType`, and that the Intent Dispatcher can resolve every `IntentType` end-to-end.
- Synchronized the repository's pre-existing stray duplicate `argus/tests/test_bootstrap.py`: added `"capability_registry"` to its `CORE_SERVICE_NAMES` tuple only, per the standing instruction (introduced in Package 011) to keep both bootstrap registration tests synchronized whenever a new core service is added.

### Changed

- **`argus/dispatcher/` revised to remove all hardcoded capability knowledge**, per this package's target architecture (`Intent -> Capability Registry -> Intent Dispatcher -> Action -> Workflow`):
  - `IIntentDispatcher`/`IntentDispatcher`: `register_mapping()`, `remove_mapping()`, and `list_mappings()` **removed** - that responsibility now belongs entirely to `ICapabilityRegistry`. `IntentDispatcher.__init__` now takes `(event_bus, capability_registry, action_factory)`, not `(event_bus)` with mappings registered after construction. `resolve(intent)` now returns a `Capability` (queried live from the injected registry, picking the first *enabled* match in registration order), not an `Action`. `dispatch()`'s behavior and its six published events are otherwise unchanged, except `ActionResolved`'s payload now also carries `capability_id`, and `DispatchFailed`'s `stage` payload gained a new possible value, `"build"` (an `action_factory` failure), alongside the existing `"resolve"`/`"execute"`.
  - `argus/dispatcher/exceptions.py`: `NoMappingError` renamed to `NoCapabilityError`; `DuplicateMappingError`/`MappingNotFoundError` removed (their responsibility moved to `argus.capability.exceptions.DuplicateCapabilityError`/`CapabilityNotFoundError`).
  - `argus/dispatcher/action.py`: `Action`/`WorkflowAction` unchanged (considered renaming `Action`, per this package's explicit allowance, and decided against it - see `IMPLEMENTATION_REPORT.md`'s Engineering Decisions).
  - `argus/dispatcher/mapping.py` (`DEFAULT_WORKFLOW_IDS`): unchanged - reused by `bootstrap.py` to populate this package's five Version 1 Capabilities.
- `argus/bootstrap.py` now constructs `CapabilityRegistry` (depends on the Event Bus only) immediately after the Conversation Manager, registers it in the Container as `"capability_registry"`, and populates five `Capability` instances from `DEFAULT_WORKFLOW_IDS` via `register()`. `IntentDispatcher` is now constructed after `CapabilityRegistry` (its 14th-core-service slot, one later than Package 012's 12th), with an `action_factory` built via `functools.partial(build_action_from_capability, workflow_engine=workflow_engine)`. Bootstrap order is now ... -> Conversation Manager -> Capability Registry -> Intent Dispatcher -> Register Core Services -> Application. `_register_core_services` now registers thirteen core services. `CORE_SERVICES_VERSION` remains `"0.1.2"` - unchanged by this package, per its own explicit Version Policy.

### ADR Update

- ADR-0002 (`design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`) remains `Proposed`, per standing instruction. `CapabilityRegistry` is the first new *non*-adopter of `IService` since Memory Service (Package 007) - a different kind of data point than the five gated/ungated adopters recorded so far, confirming the criterion correctly rules out adoption at design time, not just in hindsight. See `IMPLEMENTATION_REPORT.md`'s ADR Recommendation section.

### Known Limitations

- The five Version 1 Capabilities reference `workflow_id`s (`answer_workflow`, etc.) that no other package has registered an actual Workflow against - dispatching any of them still raises `ActionExecutionError` (wrapping `WorkflowNotFoundError`) until some future package registers real workflows under those ids. Unchanged from Package 012's own Known Limitations.
- `find_by_intent_type()` returns disabled capabilities too (a pure filter, by design) - callers other than `IntentDispatcher.resolve()` that query the registry directly must apply their own enabled-filtering if they need it.
- Capabilities are held only in memory; nothing persists across process restarts.
- Only `action_kind == "workflow"` is supported by `build_action_from_capability()` in Version 1; a capability with any other `action_kind` will fail at dispatch time with `ActionExecutionError` (`stage="build"`).

## Package 014 - Plugin Manager

### Added

- Added `argus/plugins/` package (Package 014 - Plugin Manager):
  - `plugin.py` - `Plugin`, an immutable dataclass describing one installable unit of extension: `name`, `version`, `author`, `description`, `id` (auto-generated), `enabled` (default `True`), `exported_capabilities` (a tuple of `Capability` instances), `metadata`. Pure data - holds no live service reference and does not validate its own fields.
  - `interfaces.py` - `IPluginManager`, a plain `ABC` (deliberately NOT inheriting `IService` - see the ADR Update below): `register`, `unregister`, `enable`, `disable`, `get`, `list_plugins`, `list_exported_capabilities`, `contains`.
  - `manager.py` - `PluginManager`: an in-memory registry of `Plugin` objects keyed by id. `register()` validates a Plugin's fields (non-empty id/name/version/author, and that every `exported_capabilities` entry is a `Capability`) before accepting it - the one piece of business logic this module contains besides the `enable()`/`disable()` flag-replace, and it is validation, not execution. Publishes `PluginRegistered`/`PluginUnregistered`/`PluginEnabled`/`PluginDisabled` on success only. `list_exported_capabilities()` aggregates every registered Plugin's `exported_capabilities` in registration order - a pure, no-policy read; never calls into the Capability Registry itself.
  - `exceptions.py` - `PluginError`, `InvalidPluginError`, `DuplicatePluginError`, `PluginNotFoundError`.
  - `__init__.py` - re-exports the package's public API.
- Added `factory/packages/014_PLUGIN_MANAGER.md`, including a note that no `design/specifications/PLUGIN.md` exists (this package implements the Founder's explicit work order directly, the same situation as Packages 002, 009, 010, 011, 012, and 013).
- Extended `argus/events/event_types.py`'s `EventType` with four new members: `PLUGIN_REGISTERED`, `PLUGIN_UNREGISTERED`, `PLUGIN_ENABLED`, `PLUGIN_DISABLED`.
- Added `tests/test_plugin.py` (19 new tests: the `Plugin` model), `tests/test_plugin_manager.py` (47 new tests: `PluginManager`).
- Extended `tests/test_bootstrap.py` with three new tests confirming the Plugin Manager resolves from the Container, has one enabled built-in Plugin with non-empty exported capabilities, and that its exported capabilities are the identical objects (`assertIs`) already registered with the Capability Registry.
- Synchronized the repository's pre-existing stray duplicate `argus/tests/test_bootstrap.py`: added `"plugin_manager"` to its `CORE_SERVICE_NAMES` tuple only, per the standing instruction (introduced in Package 011) to keep both bootstrap registration tests synchronized whenever a new core service is added.

### Changed

- `argus/bootstrap.py` now constructs `PluginManager` (depends on the Event Bus only) immediately after the Capability Registry, registers it in the Container as `"plugin_manager"`, and registers one built-in `Plugin` ("Core Workflows") whose `exported_capabilities` are the same five `Capability` instances already registered with the Capability Registry in the preceding step - the identical objects, not copies, so nothing is registered twice and dispatch behavior is unaffected. Bootstrap order is now ... -> Conversation Manager -> Capability Registry -> Plugin Manager -> Intent Dispatcher -> Register Core Services -> Application. `_register_core_services` now registers fourteen core services. `CORE_SERVICES_VERSION` remains `"0.1.3"` - unchanged by this package, per its own explicit Version Policy.
- `argus/dispatcher/`, `argus/capability/`, and `argus/workflow/` are unchanged - the target architecture's "Action -> Plugin Manager -> Workflow" diagram positioning is not wired into the dispatch path in Version 1 (see `factory/packages/014_PLUGIN_MANAGER.md`'s Architectural Decisions).

### ADR Update

- ADR-0002 (`design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`) remains `Proposed`, per standing instruction. `PluginManager` is the second consecutive new *non*-adopter of `IService`, following Capability Registry (Package 013) - its `enable()`/`disable()` methods were explicitly considered and rejected as lifecycle-phase candidates, since they mutate an individual Plugin's flag rather than the manager's own runtime state. See `IMPLEMENTATION_REPORT.md`'s ADR Recommendation section.

### Known Limitations

- Plugin discovery is registration-only in Version 1: no filesystem/entry-point scanning, no dynamic import machinery. A caller must construct and register every `Plugin` explicitly.
- Plugins do not execute anything - there is no `Plugin.activate()` and no relationship between a `Plugin` and any `Action`/`WorkflowAction` beyond the `exported_capabilities` data link.
- `list_exported_capabilities()`'s Capabilities are not automatically registered with the Capability Registry - `PluginManager` only exposes them; a caller decides whether and how to register any of them.

## Package 015 - Planner

### Added

- Added `argus/planner/` package (Package 015 - Planner):
  - `plan.py` - `PlanStatus` (an enum: `CREATED`, `VALIDATED`, `READY`, `FAILED`, `COMPLETED` - only the first three are ever produced by Version 1) and `Plan`, an immutable dataclass describing one Execution Plan: `originating_intent`, `id` (auto-generated), `status` (default `CREATED`), `created_at` (auto-generated), `steps`, `metadata`. Pure data - holds no live service reference and does not validate its own fields.
  - `step.py` - `PlanStep`, an immutable dataclass describing one ordered unit of work: `description`, `required_capability` (a capability id string), `id` (auto-generated), `order` (maintained exclusively by `Planner`), `optional` (default `False`), `metadata`.
  - `interfaces.py` - `IPlanner`, a plain `ABC` (deliberately NOT inheriting `IService` - see the ADR Update below): `create_plan`, `add_step`, `remove_step`, `reorder_steps`, `validate_plan`, `get_plan`, `list_plans`.
  - `planner.py` - `Planner`: an in-memory registry of `Plan` objects keyed by id. Every mutation constructs a new `Plan` (and, where steps change, new `PlanStep`s with recomputed `order` fields) via `dataclasses.replace`. Any structural mutation (`add_step`/`remove_step`/`reorder_steps`) resets a Plan's status to `CREATED`, since a prior `VALIDATED`/`FAILED` status no longer reflects the current steps. `validate_plan()` checks only that every non-optional `PlanStep`'s `required_capability` is registered with the injected `ICapabilityRegistry` (via `contains()` - never invoking it); on success, publishes `PlanValidated` and sets `status=VALIDATED`; on failure, sets `status=FAILED`, persists it, and raises `PlanValidationError` without publishing anything. Publishes `PlanCreated`/`PlanUpdated` on successful `create_plan()`/step-mutations respectively.
  - `exceptions.py` - `PlannerError`, `InvalidPlanError`, `PlanNotFoundError`, `StepNotFoundError`, `PlanValidationError`.
  - `__init__.py` - re-exports the package's public API.
- Added `factory/packages/015_PLANNER.md`, including a note that no `design/specifications/PLANNER.md` exists (this package implements the Founder's explicit work order directly, the same situation as Packages 002, 009, 010, 011, 012, 013, and 014).
- Extended `argus/events/event_types.py`'s `EventType` with three new members: `PLAN_CREATED`, `PLAN_UPDATED`, `PLAN_VALIDATED`. `PLAN_REMOVED` (a work-order example) was deliberately not added - this package has no "delete an entire Plan" operation for it to correspond to; step-level removal is covered by `PLAN_UPDATED`'s `"change"` payload field instead.
- Added `tests/test_step.py` (13 new tests: the `PlanStep` model), `tests/test_plan.py` (17 new tests: the `Plan`/`PlanStatus` model), `tests/test_planner.py` (52 new tests: `Planner`).
- Extended `tests/test_bootstrap.py` with three new tests confirming the Planner resolves from the Container, has no plans initially, and can validate a Plan against a real capability id already registered with the Capability Registry.
- Synchronized the repository's pre-existing stray duplicate `argus/tests/test_bootstrap.py`: added `"planner"` to its `CORE_SERVICE_NAMES` tuple only, per the standing instruction (introduced in Package 011) to keep both bootstrap registration tests synchronized whenever a new core service is added.

### Changed

- `argus/bootstrap.py` now constructs `Planner` (depends on the Event Bus and the Capability Registry) immediately after the Intent Dispatcher, and registers it in the Container as `"planner"`. Construction order reflects dependency order (Planner needs a live `ICapabilityRegistry`), not the target architecture diagram's own top-to-bottom position (which places Planner above Intent and the Capability Registry) - the same distinction already drawn for Capability Registry/Intent Dispatcher in Package 013. Bootstrap order is now ... -> Capability Registry -> Plugin Manager -> Intent Dispatcher -> Planner -> Register Core Services -> Application. `_register_core_services` now registers fifteen core services. `CORE_SERVICES_VERSION` remains `"0.1.4"` - unchanged by this package, per its own explicit Version Policy.
- `argus/dispatcher/`, `argus/capability/`, `argus/workflow/`, and `argus/plugins/` are unchanged - the Planner's only touchpoint with any of them is a read-only `ICapabilityRegistry.contains()` call inside `validate_plan()`.

### ADR Update

- ADR-0002 (`design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`) remains `Proposed`, per standing instruction. `Planner` is the third consecutive new *non*-adopter of `IService`, following Capability Registry (013) and Plugin Manager (014) - even `validate_plan()`, the closest thing to "real work" any non-adopter has done so far, remains a single synchronous operation with no phase distinct from any other method call. See `IMPLEMENTATION_REPORT.md`'s ADR Recommendation section.

### Known Limitations

- `PlanStatus.READY` and `PlanStatus.COMPLETED` are never produced by any Version 1 Planner method - reserved for a future dispatch-integration and completion-reporting package.
- `validate_plan()` checks capability-id existence only - it does not check a matching Capability's `enabled` flag or whether it actually supports the Plan's originating Intent's `IntentType`.
- The Planner is not wired to the Capability Registry/Dispatcher path in any direction beyond its one read-only check - nothing automatically creates a Plan from a resolved Intent, and nothing consumes a validated Plan to dispatch it.
- Plans are held only in memory; nothing persists across process restarts.

## Package 016 - Agent Runtime

### Added

- Added `argus/runtime/` package (Package 016 - Agent Runtime):
  - `execution.py` - `ExecutionStatus` (an enum: `CREATED`, `RUNNING`, `PAUSED`, `FAILED`, `COMPLETED`, `CANCELLED`) and `Execution`, an immutable dataclass describing one run of one Plan: `plan_id`, `id` (auto-generated), `status` (default `CREATED`), `current_step` (default 0), `results` (keyed by PlanStep id), `started_at`/`completed_at`, `metadata`. Pure data - holds no live service reference and does not validate its own fields.
  - `interfaces.py` - `IAgentRuntime(IService)`: `start_execution`, `pause_execution`, `resume_execution`, `cancel_execution`, `get_execution`, `list_executions`, plus the inherited IService contract. Unlike Capability Registry/Plugin Manager/Planner (three consecutive non-adopters), this package DOES inherit `IService` - see the ADR Update below.
  - `runtime.py` - `AgentRuntime`: an in-memory registry of `Execution` objects keyed by id. `start_execution()`/`resume_execution()` are gated on the Runtime's own `RUNNING` state and dispatch a Plan's `PlanStep`s sequentially through the injected `IIntentDispatcher.dispatch()` - the only way any step is ever executed - stopping immediately on the first failure (no retries, no rollback). `pause_execution()`/`cancel_execution()`/`get_execution()`/`list_executions()` remain ungated registry operations. Constructs a synthetic `Intent` per step (reusing the Plan's own `originating_intent.name`) since `IIntentDispatcher.dispatch()` has no capability-id-specific entry point - see this package's Known Limitations. Publishes `ExecutionCreated`/`ExecutionStarted`/`StepStarted`/`StepCompleted` and exactly one of `ExecutionCompleted`/`ExecutionFailed` per run; `pause_execution()`/`cancel_execution()` publish nothing (no corresponding event was specified).
  - `exceptions.py` - `AgentRuntimeError` (base, deliberately not named `RuntimeError` to avoid shadowing the Python built-in), `InvalidExecutionError`, `ExecutionNotFoundError`, `InvalidExecutionStateError`, `StepExecutionError`.
  - `__init__.py` - re-exports the package's public API.
- Added `factory/packages/016_AGENT_RUNTIME.md`, including a note that no `design/specifications/AGENT_RUNTIME.md` exists (this package implements the Founder's explicit work order directly, the same situation as Packages 002, 009-015).
- Extended `argus/events/event_types.py`'s `EventType` with six new members: `EXECUTION_CREATED`, `EXECUTION_STARTED`, `STEP_STARTED`, `STEP_COMPLETED`, `EXECUTION_COMPLETED`, `EXECUTION_FAILED` - exactly the six this package's work order named, no more.
- Added `tests/test_execution.py` (22 new tests: the `Execution`/`ExecutionStatus` model), `tests/test_runtime.py` (47 new tests: `AgentRuntime`, including reentrant pause/resume/cancel scenarios and a fake-dispatcher-based failure/no-retry suite).
- Extended `tests/test_bootstrap.py` with three new tests confirming the Agent Runtime resolves from the Container, is registered but not started, and can execute a validated Plan end-to-end through the real Planner/Dispatcher stack (failing for the expected, already-documented reason that bootstrap never starts WorkflowEngine - not a wiring bug).
- Synchronized the repository's pre-existing stray duplicate `argus/tests/test_bootstrap.py`: added `"agent_runtime"` to its `CORE_SERVICE_NAMES` tuple only, per the standing instruction (introduced in Package 011) to keep both bootstrap registration tests synchronized whenever a new core service is added.

### Changed

- `argus/bootstrap.py` now constructs `AgentRuntime` (depends on the Event Bus, the Intent Dispatcher, and the Planner) immediately after the Planner, registers it in the Container as `"agent_runtime"`. Bootstrap order is now ... -> Intent Dispatcher -> Planner -> Agent Runtime -> Register Core Services -> Application. `_register_core_services` now registers sixteen core services. `CORE_SERVICES_VERSION` remains `"0.1.5"` - unchanged by this package, per its own explicit Version Policy. AgentRuntime's own `initialize()`/`start()` are deliberately **not** called during bootstrap, for the same divergence-avoidance reasoning already applied to every prior `IService` adopter.
- `argus/dispatcher/`, `argus/capability/`, `argus/workflow/`, `argus/plugins/`, and `argus/planner/` are all unchanged - AgentRuntime's only touchpoints are `IIntentDispatcher.dispatch()` and `IPlanner.get_plan()`, both existing, unmodified public methods.

### ADR Update

- ADR-0002 (`design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`) remains `Proposed`, per standing instruction. `AgentRuntime` breaks the three-consecutive-non-adopter streak (013, 014, 015): `start_execution()`/`resume_execution()` are genuinely gated, architecturally identical to `WorkflowEngine.execute()`/`ConversationManager.receive()`/`IntentDispatcher.dispatch()`. Sixth adopter, fifth genuinely gated. See `IMPLEMENTATION_REPORT.md`'s ADR Recommendation section.

### Known Limitations

- Per-step `required_capability` targeting is not honored by Dispatcher resolution in Version 1 - every step of a Plan resolves to whatever Capability the Dispatcher would select for the Plan's originating `IntentType`, regardless of each step's own `required_capability` id.
- `PlanStep.optional` has no effect on execution - a failed optional step still stops the entire run, per this package's unconditional Failure Rules.
- No persistence, no concurrency, no retries, no rollback.
- `pause_execution()`/`cancel_execution()` are only reachable on a `RUNNING` Execution via a reentrant call from within a dispatched step's own action - there is no out-of-band way to pause an in-progress `start_execution()` call, since Version 1 has no concurrency.

## Package 017 - Connector Framework

### Added

- Added `argus/connectors/` package (Package 017 - Connector Framework):
  - `connector.py` - `Connector`, an immutable dataclass describing one registered connector's metadata: `name`, `description`, `version`, `id` (auto-generated), `enabled` (default `True`), `capabilities` (a plain tuple of operation-name strings, unrelated to `argus.capability.Capability`), `metadata`. Pure data - holds no live implementation reference and has no dependency on any other module in the package, matching the established "pure leaf model" precedent.
  - `interfaces.py` - `IConnector` (a plain ABC: `connect`/`disconnect`/`invoke`/`health_check` - the contract a connector implementation must satisfy) and `IConnectorManager(IService)`: `register_connector`, `unregister_connector`, `get_connector`, `list_connectors`, `enable_connector`, `disable_connector`, `invoke`, plus the inherited IService contract. Like Agent Runtime (016), and unlike Capability Registry/Plugin Manager/Planner (013-015), this package DOES inherit `IService` - see the ADR Update below.
  - `manager.py` - `ConnectorManager`: an in-memory registry pairing `Connector` metadata with the live `IConnector` implementations that back them, keyed by the same id. `invoke()` is gated on the manager's own `RUNNING` state, requires the target connector to be `enabled`, calls the implementation's `connect()` (idempotent) immediately before its `invoke()`, and never calls `disconnect()` automatically. `register_connector`/`unregister_connector`/`get_connector`/`list_connectors`/`enable_connector`/`disable_connector` remain ungated registry operations. Also defines `MockConnector`, the one concrete `IConnector` implementation Version 1 ships - fully in-memory, no network, no I/O - placed here rather than in `connector.py` to avoid a circular import (see this package's own Architectural Decision 1).
  - `exceptions.py` - `ConnectorError` (base), `InvalidConnectorError`, `DuplicateConnectorError`, `ConnectorNotFoundError`, `ConnectorDisabledError`, `InvalidConnectorStateError`, `ConnectorInvocationError`.
  - `__init__.py` - re-exports the package's public API.
- Added `factory/packages/017_CONNECTOR_FRAMEWORK.md`, including a note that no `design/specifications/CONNECTOR_FRAMEWORK.md` exists (this package implements the Founder's explicit work order directly, the same situation as Packages 002, 009-016).
- Extended `argus/events/event_types.py`'s `EventType` with five new members: `CONNECTOR_REGISTERED`, `CONNECTOR_ENABLED`, `CONNECTOR_DISABLED`, `CONNECTOR_INVOKED`, `CONNECTOR_FAILED` - exactly the five this package's work order named, no more.
- Added `tests/test_connector.py` (16 new tests: the `Connector` model and `MockConnector`'s own connect/disconnect/invoke/health_check state machine), `tests/test_connector_manager.py` (44 new tests: `ConnectorManager`, including duplicate registration, unknown-connector handling, enable/disable, gated `invoke()`, connect-failure and invoke-failure wrapping, and event publication).
- Extended `tests/test_bootstrap.py` with three new tests confirming the Connector Manager resolves from the Container, is registered but not started, and that bootstrap's one built-in mock connector ("Mock External System") can be invoked successfully once the manager is explicitly started.
- Synchronized the repository's pre-existing stray duplicate `argus/tests/test_bootstrap.py`: added `"connector_manager"` to its `CORE_SERVICE_NAMES` tuple only, per the standing instruction (introduced in Package 011) to keep both bootstrap registration tests synchronized whenever a new core service is added.

### Changed

- `argus/bootstrap.py` now constructs `ConnectorManager` (depends only on the Event Bus) immediately after the Agent Runtime, registers it in the Container as `"connector_manager"`, and registers one built-in mock connector, "Mock External System," backed by a `MockConnector`. Bootstrap order is now ... -> Planner -> Agent Runtime -> Connector Manager -> Register Core Services -> Application. `_register_core_services` now registers seventeen core services. `CORE_SERVICES_VERSION` remains `"0.1.6"` - unchanged by this package, per its own explicit Constraints. ConnectorManager's own `initialize()`/`start()` are deliberately **not** called during bootstrap, for the same divergence-avoidance reasoning already applied to every prior `IService` adopter.
- `argus/runtime/`, `argus/planner/`, `argus/dispatcher/`, `argus/capability/`, `argus/workflow/`, and `argus/plugins/` are all unchanged - the Connector Framework has no dependency on, and no touchpoint with, any of them.

### ADR Update

- ADR-0002 (`design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`) remains `Proposed`, per standing instruction. `ConnectorManager` continues the pattern `AgentRuntime` set in Package 016: `invoke()` is genuinely gated, architecturally identical to (and arguably a stronger case than) `IntentDispatcher.dispatch()`/`AgentRuntime.start_execution()`, since it is the literal boundary between ArgusOS and external systems. Seventh adopter, sixth genuinely gated. See `IMPLEMENTATION_REPORT.md`'s ADR Recommendation section.

### Known Limitations

- No real integrations - `MockConnector` is Version 1's only `IConnector` implementation; no network I/O, authentication, or persistence of any kind.
- `invoke()` never calls `disconnect()` automatically - a connector stays "connected" for the process lifetime once first invoked, unless something disconnects it directly (not exposed through `ConnectorManager`'s own API in Version 1).
- `health_check()` is not reachable through `ConnectorManager` - only directly against a raw `IConnector` implementation.
- `Connector.capabilities` is descriptive only - `invoke()` does not check that the requested operation is a member of it.
- No persistence, no concurrency, no retries, no rollback for `invoke()`.

## Package 018 - Knowledge Graph

### Added

- Added `argus/knowledge_graph/` package (Package 018 - Knowledge Graph):
  - `entity.py` - `Entity`, an immutable dataclass describing one node: `entity_type` (required, non-empty), `name` (required, non-empty, not enforced unique), `id` (auto-generated), `attributes` (an immutable mapping). Pure data - no dependency on any other module in the package.
  - `relationship.py` - `Relationship`, an immutable dataclass describing one directed edge: `source_entity_id`/`target_entity_id` (required, non-empty; reference `Entity.id` by id only, never a live object; self-loops permitted), `relationship_type` (required, non-empty), `id` (auto-generated), `attributes`. Also a pure, dependency-free leaf.
  - `interfaces.py` - `IKnowledgeGraph(IService)`: `add_entity`, `remove_entity`, `get_entity`, `list_entities`, `add_relationship`, `remove_relationship`, `list_relationships`, `neighbors`, `find_by_type`, plus the inherited IService contract. Per this package's explicit "Extend IService" instruction, `IKnowledgeGraph` DOES inherit `IService` - but unlike every genuinely gated adopter, none of its own methods are lifecycle-gated, exactly mirroring `IntentRouter`'s (Package 009) shape. See the ADR Update below.
  - `graph.py` - `KnowledgeGraph`: an in-memory registry of Entities and Relationships. `remove_entity()` cascades to remove every Relationship referencing the removed Entity, guaranteeing referential integrity by construction; `add_relationship()` rejects references to unknown Entities (`EntityNotFoundError`); `neighbors()` returns every distinct Entity connected to a given Entity by one hop, in either direction; `find_by_type()` filters Entities by `entity_type`.
  - `exceptions.py` - `KnowledgeGraphError` (base), `InvalidEntityError`, `DuplicateEntityError`, `EntityNotFoundError`, `InvalidRelationshipError`, `DuplicateRelationshipError`, `RelationshipNotFoundError`.
  - `__init__.py` - re-exports the package's public API.
- Added `factory/packages/018_KNOWLEDGE_GRAPH.md`, including a note that no `design/specifications/KNOWLEDGE_GRAPH.md` exists (this package implements the Founder's explicit work order directly, the same situation as Packages 002, 009-017).
- Extended `argus/events/event_types.py`'s `EventType` with four new members: `ENTITY_ADDED`, `ENTITY_REMOVED`, `RELATIONSHIP_ADDED`, `RELATIONSHIP_REMOVED` - exactly the four this package's work order named, no more.
- Added `tests/test_entity.py` (6 new tests: the `Entity` model), `tests/test_relationship.py` (7 new tests: the `Relationship` model, including self-loops), `tests/test_knowledge_graph.py` (57 new tests: `KnowledgeGraph`, including cascading removal, invalid-reference rejection, neighbors deduplication, and event publication).
- Extended `tests/test_bootstrap.py` with three new tests confirming the Knowledge Graph resolves from the Container, is registered but not started, and supports registering Entities/Relationships and querying neighbors end-to-end.
- Synchronized the repository's pre-existing stray duplicate `argus/tests/test_bootstrap.py`: added `"knowledge_graph"` to its `CORE_SERVICE_NAMES` tuple only, per the standing instruction (introduced in Package 011) to keep both bootstrap registration tests synchronized whenever a new core service is added.

### Changed

- `argus/bootstrap.py` now constructs `KnowledgeGraph` (depends only on the Event Bus) immediately after the Planner and immediately before the Agent Runtime, registers it in the Container as `"knowledge_graph"`. Bootstrap order is now ... -> Planner -> Knowledge Graph -> Agent Runtime -> Connector Manager -> Register Core Services -> Application - the first insertion in this project's history to land in the *middle* of the existing construction sequence rather than being appended at the end. `_register_core_services` now registers eighteen core services. `CORE_SERVICES_VERSION` remains `"0.1.7"` - unchanged by this package. KnowledgeGraph's own `initialize()`/`start()` are deliberately **not** called during bootstrap, for the same divergence-avoidance reasoning already applied to every prior `IService` adopter.
- `argus/runtime/`, `argus/planner/`, `argus/dispatcher/`, `argus/capability/`, `argus/workflow/`, `argus/plugins/`, and `argus/connectors/` are all unchanged - the Knowledge Graph has no dependency on, and no touchpoint with, any of them.

### ADR Update

- ADR-0002 (`design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`) remains `Proposed`, per standing instruction. `KnowledgeGraph` DOES inherit `IService`, per explicit Founder instruction rather than this Engineer's own application of the criterion - the first such case recorded. Applying the criterion independently would not have suggested adoption (no method involves external calls, dispatch, or a genuine phase distinction); none of `KnowledgeGraph`'s methods are gated, making it the second zero-gated-method adopter after `IntentRouter` (009). Eighth adopter overall, still six genuinely gated. See `IMPLEMENTATION_REPORT.md`'s ADR Recommendation section.

### Known Limitations

- No persistence - Entities/Relationships are held only in memory.
- No graph traversal algorithms (no shortest path, no multi-hop queries) and no inference, per this package's explicit Constraints.
- Not yet consulted by the Planner or any other component - infrastructure only in this package.
- `find_by_type()` filters Entities only; no relationship-type analogue exists.
- No concurrency.

## Package 019 - Memory Integration

### Added

- Added `argus/memory_integration/` package (Package 019 - Memory Integration):
  - `mapper.py` - `MemoryMapper`: pure, side-effect-free translation only, calling neither `IMemoryService` nor `IKnowledgeGraph`. `memory_to_entity(record)` translates a `MemoryRecord` into a fresh `Entity` with a deterministic id (`f"memory:{key}"`, ensuring the same memory key always maps to the same graph Entity - the mechanism behind "prevent duplicate graph entities"). `memory_to_relationship(record)` recognizes one simple convention - a `"related_keys"` entry in a Mapping-shaped `value` - translating each reference into a `Relationship` (`relationship_type="related_to"`); a record without this convention produces no Relationships. `update_entity(existing, record)` produces an Entity's updated form, preserving `existing.id`. `remove_entity(key)` returns the deterministic Entity id for a bare key, with no lookup required.
  - `interfaces.py` - `IMemoryIntegration(IService)`: `synchronize_memory`, `remove_memory`, `synchronize_all`, `synchronization_status`, `reset`, plus the inherited IService contract. Named `synchronization_status()`, not `status()` as the work order literally suggests, to avoid an unavoidable naming collision with `IService.status()` (which every other adopter in this codebase reserves exclusively for `LifecycleState` reporting) - see the Naming Collision note below.
  - `integration.py` - `MemoryIntegration`: coordinates an injected `IMemoryService` and `IKnowledgeGraph` via an injected `MemoryMapper`. Every `synchronize_memory(key)` call is a full reconciliation - if the key was already synchronized, its Entity (and, via `IKnowledgeGraph`'s own cascading removal, every Relationship referencing it) is removed and rebuilt fresh from the record's current state, satisfying both "prevent duplicate graph entities" and "synchronize updates" with one mechanism. Entity-level failures raise `MemoryMappingError`; Relationship-level failures are best-effort, publishing `MEMORY_MAPPING_FAILED` without aborting the surrounding call. `synchronize_all()` synchronizes every record in the Memory Service, one failure never aborting the batch. `synchronize_memory()`/`synchronize_all()`/`remove_memory()` are gated on the service's own `RUNNING` state; `synchronization_status()`/`reset()` remain ungated. `reset()` clears only `MemoryIntegration`'s own internal bookkeeping (which keys are synchronized, and to what Entity id) - it never touches the Memory Service's records or the Knowledge Graph's Entities/Relationships, per this package's explicit "It owns no data itself."
  - `exceptions.py` - `MemoryIntegrationError` (base), `InvalidMemoryRecordError`, `MemoryMappingError`, `MemoryNotSynchronizedError`, `InvalidMemoryIntegrationStateError`.
  - `__init__.py` - re-exports the package's public API.
- Added `factory/packages/019_MEMORY_INTEGRATION.md`, including a note that no `design/specifications/MEMORY_INTEGRATION.md` exists (this package implements the Founder's explicit work order directly, the same situation as Packages 002, 009-018).
- Extended `argus/events/event_types.py`'s `EventType` with three new members: `MEMORY_SYNCHRONIZED`, `MEMORY_DESYNCHRONIZED`, `MEMORY_MAPPING_FAILED` - exactly the three this package's work order named, no more.
- Added `tests/test_memory_mapper.py` (20 new tests: `MemoryMapper`'s pure translation methods, including the `related_keys` convention and its edge cases), `tests/test_memory_integration.py` (41 new tests: `MemoryIntegration`, including duplicate synchronization, update-in-place, removal cascade, best-effort relationship failures, batch synchronization, and lifecycle gating).
- Extended `tests/test_bootstrap.py` with three new tests confirming Memory Integration resolves from the Container, is registered but not started, and can synchronize a real Memory Service record into the Knowledge Graph end-to-end (with explicit cleanup, since `bootstrap()`'s Memory Service is disk-backed).
- Synchronized the repository's pre-existing stray duplicate `argus/tests/test_bootstrap.py`: added `"memory_integration"` to its `CORE_SERVICE_NAMES` tuple only, per the standing instruction (introduced in Package 011) to keep both bootstrap registration tests synchronized whenever a new core service is added.

### Changed

- `argus/bootstrap.py` now constructs `MemoryIntegration` (depends on the Event Bus, the Memory Service, and the Knowledge Graph) immediately after the Knowledge Graph and immediately before the Agent Runtime, registers it in the Container as `"memory_integration"`. Bootstrap order is now ... -> Knowledge Graph -> Memory Integration -> Agent Runtime -> Connector Manager -> Register Core Services -> Application. `_register_core_services` now registers nineteen core services. `CORE_SERVICES_VERSION` remains `"0.1.8"` - unchanged by this package. MemoryIntegration's own `initialize()`/`start()` are deliberately **not** called during bootstrap, for the same divergence-avoidance reasoning already applied to every prior `IService` adopter.
- `argus/memory/`, `argus/knowledge_graph/`, `argus/planner/`, `argus/runtime/`, `argus/dispatcher/`, `argus/capability/`, `argus/workflow/`, `argus/plugins/`, and `argus/connectors/` are all unchanged - Memory Integration consumes only their existing, unmodified public interfaces.

### ADR Update

- ADR-0002 (`design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`) remains `Proposed`, per standing instruction. `MemoryIntegration` DOES inherit `IService`, per explicit Founder instruction - but unlike Package 018's Knowledge Graph, applying the criterion independently to this package's own methods *would also* have suggested adoption: `synchronize_memory()`/`synchronize_all()`/`remove_memory()` are genuinely gated. This is the first case where an explicit adoption instruction and the criterion's own independent conclusion agree, directly contrasting with Package 018's divergent case - together the two packages suggest ADR-0002 could formally separate "adoption" from "gating" as distinct questions. Ninth adopter overall, seventh genuinely gated. See `IMPLEMENTATION_REPORT.md`'s ADR Recommendation section.

### Naming Collision

- This package's work order lists `status()` as a Responsibility, but `IService.status()` is a fixed abstract method (`-> LifecycleState`) used identically by every other adopter in this codebase. Resolved by naming the domain method `synchronization_status()` instead - see `argus/memory_integration/interfaces.py`'s Architectural Note.

### Known Limitations

- Resynchronizing an Entity can silently drop inbound Relationships created by other entities' syncs, since only the resynchronized Entity's own outgoing Relationships are rebuilt.
- No persistence - synchronization bookkeeping is held only in memory.
- No AI reasoning, no graph inference - `related_keys` is the only relationship signal recognized.
- No vector search.
- `synchronize_all()`'s per-record relationship resolution depends on `IMemoryService.list()`'s (unordered) iteration order; a second pass resolves any references that failed on the first.
- No concurrency.

## Package 020 - Reasoning Engine

### Added

- Added `argus/reasoning/` package (Package 020 - Reasoning Engine):
  - `query.py` - `ReasoningQuery`: an immutable request (`entity_type`, `relationship_type`, `entity_id`, `depth`, `filters`). Pure data, no validation of its own - validation lives in `ReasoningEngine`, matching the "pure leaf" precedent set by `Entity`/`Relationship`.
  - `result.py` - `ReasoningResult`: an immutable, descriptive-only outcome (`matched_entities`, `matched_relationships`, `reasoning_steps`, `metadata`). No confidence scores, no AI-generated explanations - `reasoning_steps` is a factual, mechanical execution trace only.
  - `interfaces.py` - `IReasoningEngine(IService)`: `query`, `neighbors`, `find_paths`, `related_entities`, `entity_summary`, `relationship_summary`, plus the inherited IService contract.
  - `engine.py` - `ReasoningEngine`: a deterministic, read-only query layer over an injected `IKnowledgeGraph`. `query()` interprets a `ReasoningQuery` across four branches - traversal from a specific `entity_id` (breadth-first reachability, bounded by `depth`, optionally restricted by `relationship_type`), search by `entity_type` alone, search by `relationship_type` alone, and a combined "simple graph pattern" (relationships of a given type touching an entity of a given type) when both are set together. `neighbors()`/`related_entities()` return an entity's direct connections, the latter optionally restricted by relationship type. `entity_summary()`/`relationship_summary()` return count-based descriptive summaries. `find_paths()` deterministically enumerates every simple path between two entities up to an explicit `max_depth`, via bounded depth-first search - the first package permitted to perform genuine multi-hop graph traversal, since Package 018's "No graph algorithms yet" was an explicit deferral, not a permanent prohibition. Every public method also attaches the injected `IMemoryIntegration`'s own `synchronization_status()` snapshot to its result's metadata, read-only, satisfying the Objective's "consumes information from... Memory Integration" without correlating individual Entities back to memory keys (which would require reaching into `MemoryMapper`'s private id scheme).
  - `exceptions.py` - `ReasoningError` (base, also used for IService lifecycle transition failures), `InvalidReasoningQueryError`, `ReasoningTargetNotFoundError`.
  - `__init__.py` - re-exports the package's public API.
- Added `factory/packages/020_REASONING_ENGINE.md`, including a note that no `design/specifications/REASONING_ENGINE.md` exists (this package implements the Founder's explicit work order directly, the same situation as Packages 002, 009-019).
- Extended `argus/events/event_types.py`'s `EventType` with three new members: `REASONING_QUERY_EXECUTED`, `REASONING_RESULT_CREATED`, `REASONING_QUERY_FAILED` - exactly the three this package's work order named, no more. Every public method publishes `REASONING_QUERY_EXECUTED` then `REASONING_RESULT_CREATED` on success, or `REASONING_QUERY_FAILED` alone on failure - mutually exclusive outcomes for a single call.
- Added `tests/test_reasoning_query.py` (7 new tests), `tests/test_reasoning_result.py` (7 new tests), `tests/test_reasoning_engine.py` (72 new tests covering entity/relationship/pattern queries, neighbor traversal, path discovery including parallel edges and self-loops, summaries, empty-graph behavior, invalid input, lifecycle behavior, and event publication for every public method's success and failure paths).
- Extended `tests/test_bootstrap.py` with three new tests confirming the Reasoning Engine resolves from the Container, is registered but not started, and can query a live Knowledge Graph end-to-end (no disk-backed resource involved, unlike Memory Integration's own end-to-end bootstrap test).
- Synchronized the repository's pre-existing stray duplicate `argus/tests/test_bootstrap.py`: added `"reasoning_engine"` to its `CORE_SERVICE_NAMES` tuple only, per the standing instruction (introduced in Package 011) to keep both bootstrap registration tests synchronized whenever a new core service is added.

### Changed

- `argus/bootstrap.py` now constructs `ReasoningEngine` (depends on the Event Bus, the Knowledge Graph, and Memory Integration) immediately after Memory Integration and immediately before the Agent Runtime, registers it in the Container as `"reasoning_engine"`. Bootstrap order is now ... -> Knowledge Graph -> Memory Integration -> Reasoning Engine -> Agent Runtime -> Connector Manager -> Register Core Services -> Application. `_register_core_services` now registers twenty core services. `CORE_SERVICES_VERSION` remains `"0.1.9"` - unchanged by this package. ReasoningEngine's own `initialize()`/`start()` are deliberately **not** called during bootstrap, for the same divergence-avoidance reasoning already applied to every prior `IService` adopter.
- `argus/knowledge_graph/`, `argus/memory_integration/`, `argus/planner/`, `argus/runtime/`, `argus/dispatcher/`, `argus/capability/`, `argus/workflow/`, `argus/plugins/`, and `argus/connectors/` are all unchanged - the Reasoning Engine consumes only their existing, unmodified public interfaces. Per this package's own explicit instruction, the Planner does not yet consume the Reasoning Engine.

### ADR Update

- ADR-0002 (`design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`) remains `Proposed`, per standing instruction. `ReasoningEngine` DOES inherit `IService`, per explicit Founder instruction - but, like Package 018's Knowledge Graph and unlike Package 019's Memory Integration, applying the criterion independently to this package's own methods would NOT have suggested adoption: all six public methods are read-only, in-memory, and ungated. This is the third IService adopter in this codebase with zero gated methods (after IntentRouter and KnowledgeGraph), and the second case (after Knowledge Graph) where an explicit adoption instruction diverges from the criterion's own independent conclusion. Tenth adopter overall, seventh genuinely gated. See `IMPLEMENTATION_REPORT.md`'s ADR Recommendation section.

### Known Limitations

- No persistence - the Reasoning Engine holds no state of its own; every query re-reads the live Knowledge Graph.
- No graph algorithms beyond bounded, deterministic BFS reachability (`query()`'s entity_id branch) and bounded, deterministic simple-path DFS enumeration (`find_paths()`) - no shortest-path ranking, no weighting, no heuristics.
- No AI reasoning, no probabilistic inference, no LLM invocation - every result is descriptive and mechanically derived.
- `find_paths()`'s exhaustive simple-path enumeration is combinatorially bounded by `max_depth` and the graph's own density; a very dense graph with a large `max_depth` could enumerate a large number of paths. No limit on result size exists in Version 1 beyond `max_depth` itself.
- `ReasoningResult.metadata`'s `memory_synchronization_status` reflects Memory Integration's own bookkeeping only - it does not correlate individual matched Entities back to the specific memory keys that produced them (see `argus/reasoning/engine.py`'s own Architectural Decision).
- No concurrency.

## Package 021 - Decision Engine

### Added

- Added `argus/decision/` package (Package 021 - Decision Engine):
  - `rule.py` - `DecisionRule`: an immutable value object (`name`, `predicate`, `priority`, `id`, `description`). `predicate` is a plain Python callable, `Callable[[Sequence[ReasoningResult]], bool]`, supplied directly by the caller - this module implements no interpreter, scripting language, `eval()`, `exec()`, or dynamic code generation of any kind, satisfying "No scripting. No Python execution. No dynamic code generation" by construction, not by added validation.
  - `decision.py` - `Decision`: an immutable outcome (`decision_type`, `decision_id`, `matched_rules`, `reasoning_results`, `metadata`). "Decision is immutable."
  - `interfaces.py` - `IDecisionEngine(IService)`: `evaluate`, `evaluate_all`, `register_rule`, `remove_rule`, `list_rules`, `decision_summary`, plus the inherited IService contract.
  - `engine.py` - `DecisionEngine`: maintains a rule table and evaluates one or more `ReasoningResult` objects against every registered rule, in priority order (lower first, ties broken by registration order) - no "stop at first match." `matched_rules` reports every rule that matched; `Decision.metadata["rule_evaluations"]` reports a complete matched/not-matched trace for every registered rule. A registered rule's predicate raising an exception aborts the whole evaluation (unlike Memory Integration's best-effort batch philosophy) - `DECISION_FAILED` is published and `RuleEvaluationError` is raised, with no partial Decision returned. `DecisionEngine` holds an injected `IReasoningEngine` (per the explicit Bootstrap dependency instruction) but does not call it in Version 1 - see the ADR Update section below.
  - `exceptions.py` - `DecisionError` (base), `InvalidDecisionRuleError`, `DuplicateRuleError`, `RuleNotFoundError`, `InvalidDecisionInputError`, `RuleEvaluationError`.
  - `__init__.py` - re-exports the package's public API.
- Added `factory/packages/021_DECISION_ENGINE.md`, including a note that no `design/specifications/DECISION_ENGINE.md` exists (this package implements the Founder's explicit work order directly, the same situation as Packages 002, 009-020).
- Extended `argus/events/event_types.py`'s `EventType` with three new members: `DECISION_EVALUATED`, `DECISION_CREATED`, `DECISION_FAILED` - exactly the three this package's work order named, no more. `register_rule()`/`remove_rule()` publish nothing - this package's own Events section names only evaluation-lifecycle events.
- Added `tests/test_decision.py` (7 new tests), `tests/test_decision_rule.py` (7 new tests), `tests/test_decision_engine.py` (44 new tests covering rule registration, duplicate rules, rule ordering, deterministic evaluation, multiple reasoning results, raising predicates, decision summaries, lifecycle behavior, and event publication).
- Extended `tests/test_bootstrap.py` with three new tests confirming the Decision Engine resolves from the Container, is registered but not started, and can evaluate a real Reasoning Engine result end-to-end.
- Synchronized the repository's pre-existing stray duplicate `argus/tests/test_bootstrap.py`: added `"decision_engine"` to its `CORE_SERVICE_NAMES` tuple only, per the standing instruction (introduced in Package 011) to keep both bootstrap registration tests synchronized whenever a new core service is added.

### Changed

- `argus/bootstrap.py` now constructs `DecisionEngine` (depends on the Event Bus and the Reasoning Engine) immediately after the Reasoning Engine and immediately before the Agent Runtime, registers it in the Container as `"decision_engine"`. Bootstrap order is now ... -> Reasoning Engine -> Decision Engine -> Agent Runtime -> Connector Manager -> Register Core Services -> Application. `_register_core_services` now registers twenty-one core services. `CORE_SERVICES_VERSION` remains `"0.2.0"` - unchanged by this package. DecisionEngine's own `initialize()`/`start()` are deliberately **not** called during bootstrap, for the same divergence-avoidance reasoning already applied to every prior `IService` adopter.
- `argus/reasoning/`, `argus/knowledge_graph/`, `argus/memory_integration/`, `argus/planner/`, `argus/runtime/`, `argus/dispatcher/`, `argus/capability/`, `argus/workflow/`, `argus/plugins/`, and `argus/connectors/` are all unchanged - the Decision Engine consumes only `ReasoningResult`, an existing, unmodified type. Per this package's own explicit instruction, the Planner remains unchanged and does not yet consume the Decision Engine.

### ADR Update

- ADR-0002 (`design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`) remains `Proposed`, per standing instruction. `DecisionEngine` DOES inherit `IService`, per explicit Founder instruction - but, like Package 018's Knowledge Graph and Package 020's Reasoning Engine, and unlike Package 019's Memory Integration, applying the criterion independently to this package's own methods would NOT have suggested adoption: all six public methods are in-memory and ungated. This is the fourth IService adopter in this codebase with zero gated methods, and the third of four consecutive directed-adoption packages (018, 020, 021) to diverge from the criterion's own independent conclusion (019 alone converged). Eleventh adopter overall, seven genuinely gated. See `IMPLEMENTATION_REPORT.md`'s ADR Recommendation section.

### Known Limitations

- No persistence - `DecisionEngine` retains no history of past Decisions; `decision_summary()` reflects the currently registered rule set only.
- No AI, no machine learning, no probabilistic reasoning - every Decision is produced by deterministic, caller-supplied Python predicates evaluated in a fixed priority order.
- No rule scripting - predicates are plain Python callables; this package implements no interpreter, DSL, or dynamic code execution of any kind.
- A rule predicate that raises aborts the entire `evaluate()`/`evaluate_all()` call - there is no best-effort, partial-result mode.
- The injected `IReasoningEngine` dependency is not called anywhere in Version 1 - see the ADR Update section and `argus/decision/interfaces.py`'s own Architectural Note.
- The Planner does not yet consume the Decision Engine, per this package's own explicit Version 1 scope limit.
- No concurrency.

## Package 022 - Cognitive Context

### Added

- Added `argus/context/` package (Package 022 - Cognitive Context):
  - `context.py` - `CognitiveContext`: an immutable transport object (`context_id`, `conversation_id`, `memory_references`, `knowledge_references`, `reasoning_results`, `decision_references`, `metadata`). `reasoning_results` holds actual `ReasoningResult` objects, directly reusing `Decision.reasoning_results`' (Package 021) own field name and type; `memory_references`/`knowledge_references`/`decision_references` hold plain identifier strings, not live objects - what makes "shall NOT modify any contained object" and "shall NOT own persistence" true by construction. Pure data, no validation of its own - validation lives in `ContextBuilder`, matching the "pure leaf" precedent set by every prior value object in this codebase.
  - `metadata.py` - `ContextMetadata`: an immutable value object (`created_at`, `version`, `correlation_id`, `extra`) reconciling the work order's "arbitrary metadata" and "creation timestamp, version, correlation identifier" descriptions into a single field - the three named fields are system-assigned, `extra` is the open-ended, caller-supplied mapping.
  - `builder.py` - `ContextBuilder`: a mutable, fluent builder implementing `ICognitiveContextBuilder` - `with_conversation`/`with_memory`/`with_knowledge`/`with_reasoning`/`with_decision`/`with_metadata`/`build`. "The builder is mutable. The resulting context is immutable." `with_memory()`/`with_knowledge()`/`with_reasoning()`/`with_decision()` accumulate across calls; `with_conversation()` and repeated `with_metadata()` calls on the same key overwrite (last call wins). `build()` performs no additional validation and returns a fresh, independent `CognitiveContext` snapshot every time it is called.
  - `interfaces.py` - `ICognitiveContextBuilder(ABC)` - explicitly NOT `IService`: "This is not an IService... This package intentionally introduces no new core service. This is the first infrastructure package since the early foundation that does not expand the service registry." Matches `IConnector`'s (Package 017) own "plain behavior, not a lifecycle-managed service" precedent.
  - `exceptions.py` - `ContextError` (base), `InvalidContextError` - raised only by `ContextBuilder`'s `with_*` methods for malformed input.
  - `__init__.py` - re-exports the package's public API.
- Added `factory/packages/022_COGNITIVE_CONTEXT.md`, including a note that no `design/specifications/COGNITIVE_CONTEXT.md` exists (this package implements the Founder's explicit work order directly, the same situation as Packages 002, 009-021).
- Added `tests/test_context.py` (15 new tests), `tests/test_context_builder.py` (20 new tests), `tests/test_context_metadata.py` (10 new tests) covering immutability, builder chaining, builder validation, metadata creation, empty/populated contexts, invalid construction, equality semantics, and build() independence across multiple calls.

### Not Changed

- **`argus/bootstrap.py` was intentionally left unchanged** - Package 022 registers no new core service, per this package's own explicit "No bootstrap registration. No lifecycle integration. No service registration" Constraint. `CORE_SERVICES_VERSION` remains `"0.2.1"`.
- **`argus/events/event_types.py` was intentionally left unchanged** - no new `EventType` members. "No new EventTypes. This package is intentionally passive."
- **`tests/test_bootstrap.py` and `argus/tests/test_bootstrap.py` were intentionally left unchanged** - no `CORE_SERVICE_NAMES` sync was needed, since this package registers no core service.
- `argus/decision/`, `argus/reasoning/`, `argus/knowledge_graph/`, `argus/memory_integration/`, `argus/planner/`, `argus/runtime/`, `argus/dispatcher/`, `argus/capability/`, `argus/workflow/`, `argus/plugins/`, and `argus/connectors/` are all unchanged - `CognitiveContext` consumes only `ReasoningResult`, an existing, unmodified type. Per this package's own explicit instruction, neither the Planner nor the Decision Engine consume the Cognitive Context yet.

### ADR Update

- Not applicable - this package introduces no `IService` adopter. `design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md` was not modified.

### Known Limitations

- No lifecycle, no service registration - `CognitiveContext`/`ContextBuilder` carry no `IService` contract of any kind.
- No events - this package publishes nothing.
- No persistence, no serialization - a `CognitiveContext` exists only in memory for as long as a caller holds a reference to it.
- The Planner does not yet consume the Cognitive Context, per this package's own explicit Version 1 scope limit.
- The Decision Engine does not yet consume the Cognitive Context, per this package's own explicit Version 1 scope limit.
- `memory_references`/`knowledge_references`/`decision_references` are opaque identifier strings - `CognitiveContext` performs no lookup, dereferencing, or validation that a given identifier corresponds to an existing record.
- No concurrency.

## Package 023 - Planning Session

### Added

- Added `argus/planning/` package (Package 023 - Planning Session):
  - `session.py` - `PlanningSession`: an immutable transport object (`session_id`, `cognitive_context`, `goals`, `constraints`, `metadata`). `cognitive_context` holds the actual, already-immutable `CognitiveContext` (Package 022) itself; `goals`/`constraints` hold the actual `PlanningGoal`/`PlanningConstraint` objects, not reference strings - a deliberate contrast with `CognitiveContext`'s own three "..._references" fields, resolved the same way: by the work order's own field naming. Pure data, no validation of its own - validation lives in `PlanningSessionBuilder`.
  - `goal.py` - `PlanningGoal`: an immutable value object (`goal_id`, `name`, `description`, `priority`). "Priority is descriptive only. No scheduling logic." - never read, compared, or sorted by anything in this package; `PlanningSession.goals` always preserves exact call order.
  - `constraint.py` - `PlanningConstraint`: an immutable value object (`constraint_id`, `name`, `description`, `metadata`). "No validation logic." - carries no evaluable logic of any kind.
  - `metadata.py` - `PlanningMetadata`: an immutable value object (`created_at`, `version`, `correlation_id`, `extra`), directly reusing `ContextMetadata`'s (Package 022) own reconciliation of "arbitrary metadata" and "creation timestamp, version, correlation identifier" into a single field - the second consecutive package to use this exact shape.
  - `builder.py` - `PlanningSessionBuilder`: a mutable, fluent builder implementing `IPlanningSessionBuilder` - `with_context`/`with_goal`/`with_constraint`/`with_metadata`/`build`. "Builder is mutable. PlanningSession is immutable. Each call to build() returns an independent immutable snapshot." `with_goal()`/`with_constraint()` accumulate across calls; `with_context()` and repeated `with_metadata()` calls on the same key overwrite (last call wins). Directly mirrors `ContextBuilder`'s (022) own shape and validation discipline.
  - `interfaces.py` - `IPlanningSessionBuilder(ABC)` - explicitly NOT `IService`: "This is not an IService... No service registration. No lifecycle integration. No EventBus changes." Directly reuses `ICognitiveContextBuilder`'s (022) own resolution for the identical question.
  - `exceptions.py` - `PlanningError` (base), `InvalidPlanningSessionError` - raised only by `PlanningSessionBuilder`'s `with_*` methods for malformed input.
  - `__init__.py` - re-exports the package's public API.
- Added `factory/packages/023_PLANNING_SESSION.md`, including a note that no `design/specifications/PLANNING_SESSION.md` exists (this package implements the Founder's explicit work order directly, the same situation as Packages 002, 009-022).
- Added `tests/test_planning_session.py` (15 new tests), `tests/test_planning_builder.py` (20 new tests), `tests/test_planning_goal.py` (9 new tests), `tests/test_planning_constraint.py` (11 new tests), `tests/test_planning_metadata.py` (10 new tests) covering immutability, builder chaining, builder validation, metadata behavior, empty/populated sessions, multiple goals, multiple constraints, invalid construction, and equality semantics.

### Not Changed

- **`argus/bootstrap.py` was intentionally left unchanged** - Package 023 registers no new core service, per this package's own explicit "No service registration. No lifecycle integration. No EventBus changes" Constraint. `CORE_SERVICES_VERSION` remains `"0.2.2"`.
- **`argus/events/event_types.py` was intentionally left unchanged** - no new `EventType` members. "No EventTypes."
- **`tests/test_bootstrap.py` and `argus/tests/test_bootstrap.py` were intentionally left unchanged** - no `CORE_SERVICE_NAMES` sync was needed, since this package registers no core service.
- `argus/context/`, `argus/decision/`, `argus/reasoning/`, `argus/knowledge_graph/`, `argus/memory_integration/`, `argus/planner/`, `argus/runtime/`, `argus/dispatcher/`, `argus/capability/`, `argus/workflow/`, `argus/plugins/`, and `argus/connectors/` are all unchanged - `PlanningSession` consumes only `CognitiveContext`, an existing, unmodified type. Per this package's own explicit instruction, the Planner does not yet consume the Planning Session.

### ADR Update

- Not applicable - this package introduces no `IService` adopter. `design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md` was not modified.

### Known Limitations

- No lifecycle, no service registration - `PlanningSession`/`PlanningSessionBuilder` carry no `IService` contract of any kind.
- No events - this package publishes nothing.
- No persistence, no serialization - a `PlanningSession` exists only in memory for as long as a caller holds a reference to it.
- No goal validation, no plan optimization, no workflow execution - "It performs no planning. It executes no workflows."
- `PlanningGoal.priority` has no behavior - descriptive only.
- `PlanningConstraint` carries no evaluable logic - purely descriptive data.
- The Planner does not yet consume the Planning Session, per this package's own explicit Version 1 scope limit.
- No concurrency.

## Package 024 - Planner Session Integration

### Added

- Added `Planner.plan_session(planning_session: PlanningSession) -> Plan` to `argus/planner/planner.py`, and declared it on `IPlanner` (`argus/planner/interfaces.py`) - a second, additive entry point that builds a Plan from a `PlanningSession` by internally delegating to the pre-existing `create_plan()`/`add_step()` methods. "No duplicate planning logic": `plan_session()` synthesizes an `Intent(name=IntentType.UNKNOWN, confidence=0.0, ...)` (PlanningSession carries no Intent of its own), calls `self.create_plan()`, then calls `self.add_step()` once per `planning_session.goal` - every `PLAN_CREATED`/`PLAN_UPDATED` event this produces is published by those two pre-existing methods themselves.
- Each `PlanningGoal` becomes one `PlanStep`: `description` is the goal's own description if non-empty, else its `name`; `required_capability` is the goal's `name` (its only other identifying field); `metadata` carries `goal_id`/`priority`. `PlanningConstraint`s are never turned into steps - each is recorded descriptively under the resulting Plan's own `metadata["constraints"]` instead, alongside `metadata["planning_session_id"]` and (when present) `metadata["cognitive_context_id"]`.
- `plan_session()` raises the Planner's own pre-existing `InvalidPlanError` for a non-`PlanningSession` argument - no new exception type was introduced.
- Added `factory/packages/024_PLANNER_SESSION_INTEGRATION.md`, including a note that no `design/specifications/PLANNER_SESSION_INTEGRATION.md` exists (this package implements the Founder's explicit work order directly, the same situation as Packages 002, 009-023).
- Added `tests/test_planner_session_integration.py` (31 new tests) covering planning from a PlanningSession, identical output versus the legacy `create_plan()`/`add_step()` API, empty sessions, populated sessions, multiple goals, multiple constraints, immutable behavior (the session/goal/constraint/context are never mutated), the delegation path (same events fire; the resulting Plan is genuinely registered via `get_plan()`/`list_plans()`/`validate_plan()`), and error handling.

### Changed

- `argus/planner/interfaces.py`: `IPlanner` gained one new abstract method, `plan_session()`, plus two new Architectural Notes explaining why it is additive (not a replacement) and why its only `argus.planning` dependency is `PlanningSession` itself. Every pre-existing abstract method is unchanged.
- `argus/planner/planner.py`: `Planner` gained `plan_session()` plus two private helpers (`_synthesize_intent_for_session()`, `_session_plan_metadata()`). Every pre-existing method's body is byte-for-byte unchanged; all 52 pre-existing tests in `tests/test_planner.py` pass with zero modification to that file.

### Not Changed

- **`argus/bootstrap.py` was intentionally left unchanged** - `Planner`'s constructor signature (`event_bus`, `capability_registry`) is unaffected; no new service, no new registration, no new lifecycle integration. "Bootstrap: No changes."
- **`argus/events/event_types.py` was intentionally left unchanged** - no new `EventType` members; `plan_session()` reuses the pre-existing `PLAN_CREATED`/`PLAN_UPDATED` members via its delegated calls.
- **`tests/test_bootstrap.py` and `argus/tests/test_bootstrap.py` were intentionally left unchanged** - no core service registration changed.
- `argus/context/`, `argus/decision/`, `argus/planning/`, `argus/runtime/`, `argus/planner/plan.py`, `argus/planner/step.py`, `argus/planner/exceptions.py`, and `argus/planner/__init__.py` are all unchanged - per this package's own explicit Constraints ("modify Runtime," "modify Decision Engine," "modify Cognitive Context," "modify Planning Session" all forbidden).

### ADR Update

- Not applicable - this package introduces no `IService` adopter and does not affect `IPlanner`'s existing non-adoption. `design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md` was not modified.

### Known Limitations

- `PlanningGoal.name` doubles as `required_capability` - deterministic and documented, not a guarantee the name corresponds to a registered Capability; `validate_plan()` (called separately, never automatically by `plan_session()`) is what actually checks that.
- `plan_session()` never calls `validate_plan()` - produces a `PlanStatus.CREATED` Plan, exactly like `create_plan()` alone would.
- Goal `priority` still has no behavior beyond being copied into step metadata - steps always appear in the session's own goal call order.
- Only `cognitive_context.context_id` is carried through for traceability - `memory_references`/`knowledge_references`/`reasoning_results`/`decision_references` are not read or reflected anywhere in the resulting Plan.
- The Planner is still not automatically wired into the pipeline - `plan_session()` is available to any caller with a `PlanningSession` in hand, but no future-package-style automatic pipeline stage exists yet.
- No AI, no optimization, no persistence, no concurrency - unchanged from Package 015.

## Package 025 - Cognitive Pipeline

### Added

- Added `argus/pipeline/` (`__init__.py`, `pipeline.py`, `request.py`, `result.py`, `interfaces.py`, `exceptions.py`) - the first-generation Cognitive Pipeline, orchestrating the existing cognitive architecture end-to-end: `User Request -> Cognitive Pipeline -> Conversation -> ... -> Context -> Planning Session -> Planner -> Validated Plan`. "It does not introduce new reasoning. It does not introduce AI. It does not change planner behavior. Its responsibility is orchestration only."
- `PipelineRequest` (`argus/pipeline/request.py`) - immutable, carries the existing `ConversationSession` directly (`conversation`, `request_id`, `metadata`). "The request contains the existing Conversation object. Do not introduce raw text processing here."
- `PipelineResult` (`argus/pipeline/result.py`) - immutable, `conversation`, `cognitive_context`, `planning_session`, `plan`, `pipeline_id`, `metadata`. "No execution results. No runtime state."
- `ICognitivePipeline` (`argus/pipeline/interfaces.py`) - inherits `IService`, per explicit instruction; declares one abstract method, `run(request: PipelineRequest) -> PipelineResult`.
- `CognitivePipeline` (`argus/pipeline/pipeline.py`) - implements `ICognitivePipeline`. `run()` performs exactly six steps: accept the `PipelineRequest`, obtain its `ConversationSession`, build a `CognitiveContext` via `ContextBuilder`, build a `PlanningSession` via `PlanningSessionBuilder` (embedding that same `CognitiveContext`), invoke `Planner.plan_session()`, return the `PipelineResult`. Depends on exactly one injected collaborator, `IPlanner`; holds no `IEventBus` reference at all, since it performs no direct event publication of its own - every event the pipeline's own orchestration produces fires from inside `Planner.plan_session()`'s pre-existing delegated calls.
- `PipelineError`, `InvalidPipelineRequestError`, `PipelineExecutionError` (`argus/pipeline/exceptions.py`) - `InvalidPipelineRequestError` for a non-`PipelineRequest` argument or a `PipelineRequest.conversation` that is not a `ConversationSession`; `PipelineExecutionError` wraps (`raise ... from error`) any exception `Planner.plan_session()` raises, the same "wrap a delegate's own exception" shape `RuleEvaluationError` (Package 021) established; `PipelineError` directly, for an invalid `IService` lifecycle transition or calling `run()` while not `RUNNING`.
- Metadata propagation: every key in `PipelineRequest.metadata`, plus `request_id` itself, is carried into the built `CognitiveContext.metadata.extra`, the built `PlanningSession.metadata.extra`, and `PipelineResult.metadata` directly - three independently observable propagation points.
- Added `factory/packages/025_COGNITIVE_PIPELINE.md`.
- Added `tests/test_pipeline.py` (34 new tests), `tests/test_pipeline_request.py` (11 new tests), `tests/test_pipeline_result.py` (10 new tests) - covering lifecycle gating, empty/populated conversations, orchestration order, planner invocation, immutable results, pipeline output, dependency failures, and metadata propagation.
- Added 3 new tests to `tests/test_bootstrap.py` (`cognitive_pipeline` registered in the container; not started by `bootstrap()` itself; a full end-to-end `initialize()`/`start()`/`run()`/`stop()` call against the real bootstrapped `Planner`).

### Changed

- `argus/bootstrap.py`: registered `CognitivePipeline` as the twenty-second core service and twelfth `IService` adopter - "the first new runtime service since Package 021." Constructed immediately after `connector_manager`, depending on `planner` alone (already constructed earlier in the sequence). Startup Sequence gained a new step 23 ("Construct the Cognitive Pipeline"); the prior steps 23/24 renumbered to 24/25; `_register_core_services()` gained a `cognitive_pipeline: ICognitivePipeline` parameter and the twenty-second entry in its `core_services` tuple.
- `tests/test_bootstrap.py` / `argus/tests/test_bootstrap.py`: `CORE_SERVICE_NAMES` synced to include `"cognitive_pipeline"`, per the standing Package 011 rule for the duplicate tree.

### Not Changed

- **`argus/runtime/`, `argus/decision/`, `argus/reasoning/`, `argus/context/`, `argus/planning/`, and `argus/planner/` are all unchanged** - "Runtime: No changes. Planner: No changes... Decision Engine: No changes. Cognitive Context: No changes. Planning Session: No changes."
- **`argus/events/event_types.py` was intentionally left unchanged** - "No new EventTypes. Reuse existing planner behavior."
- No AI or LLM integration, no persistence, no workflow execution - "The pipeline is an orchestrator only."

### ADR Update

- `design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md` gained an Empirical Finding for Package 025. `ICognitivePipeline` inheriting `IService` was again an explicit instruction, but this time ADR-0002's criterion, applied independently to `run()`'s genuinely effectful multi-step orchestration, would have suggested adoption on its own too - making `CognitivePipeline` the **second** convergent case in this codebase, after Memory Integration (Package 019), and the direct opposite of Packages 018/020/021's divergent pattern. `run()` is the pipeline's sole public method and is genuinely gated on `RUNNING`.

### Known Limitations

- The `PlanningSession` a `CognitivePipeline` builds always has empty `goals`/`constraints` - the pipeline has no dependency on the Reasoning Engine or Decision Engine in Version 1, so it has no source to populate them from; the resulting `Plan` therefore always has zero steps.
- `CognitivePipeline` holds no `IEventBus` reference - by design, since it has nothing of its own to publish.
- No AI, no optimization, no persistence, no concurrency - unchanged from every prior package in this phase.
- The pipeline is not yet invoked automatically by anything - it is available to any caller holding a `PipelineRequest`, but no automatic trigger (a Connector, a Scheduler tick, or similar) exists yet.

## Package 026 - Agent Session

### Added

- Added `argus/agent/` (`__init__.py`, `session.py`, `request.py`, `response.py`, `interfaces.py`, `exceptions.py`, and `service.py` - see "Not Changed"/documentation for the one file-naming deviation from this package's own listed file names) - the first-generation Agent Session, orchestrating the existing Cognitive Pipeline on behalf of a user-facing interaction: `User -> Agent Session -> Pipeline -> Conversation -> ... -> Planner -> Validated Plan`. "An Agent Session represents an ongoing interaction between a user and Argus. It owns conversation continuity. It orchestrates the Cognitive Pipeline. It does not perform reasoning. It does not perform planning. It does not perform execution."
- `AgentSession` (`argus/agent/session.py`) - immutable, owns one `ConversationSession` directly (`conversation`, `session_id`, `metadata`). "The session owns one Conversation instance. The Conversation remains the authoritative conversation model."
- `AgentRequest` (`argus/agent/request.py`) - immutable, references an `AgentSession` and separately carries the `ConversationSession` this particular request concerns (`session`, `conversation`, `request_id`, `metadata`).
- `AgentResponse` (`argus/agent/response.py`) - immutable, `session`, `pipeline_result`, `response_id`, `metadata`. "Do not generate natural-language responses. Do not perform execution. Wrap the PipelineResult only."
- `IAgentService` (`argus/agent/interfaces.py`) - inherits `IService`, per explicit instruction; declares one abstract method, `run(request: AgentRequest) -> AgentResponse`.
- `AgentService` (`argus/agent/service.py`) - implements `IAgentService`. `run()` performs exactly four steps: accept the `AgentRequest`, build a `PipelineRequest` from it, invoke `CognitivePipeline.run()`, return the `AgentResponse`. Depends on exactly one injected collaborator, `ICognitivePipeline`; holds no `IEventBus` reference at all, the same "nothing of its own to publish" shape `CognitivePipeline` (Package 025) already established one layer below.
- `AgentError`, `InvalidAgentRequestError`, `AgentExecutionError` (`argus/agent/exceptions.py`) - `InvalidAgentRequestError` for a non-`AgentRequest` argument, a `session` that is not an `AgentSession`, or a `conversation` that is not a `ConversationSession`; `AgentExecutionError` wraps (`raise ... from error`) any exception `CognitivePipeline.run()` raises, the same "wrap a delegate's own exception" shape `PipelineExecutionError` (Package 025) established one layer below, which itself mirrors `RuleEvaluationError` (Package 021); `AgentError` directly, for an invalid `IService` lifecycle transition or calling `run()` while not `RUNNING`.
- Metadata propagation: every key in `AgentRequest.metadata`, plus `agent_request_id` and `agent_session_id`, is carried into the built `PipelineRequest.metadata` - which the Cognitive Pipeline itself then propagates further into the built `CognitiveContext.metadata.extra`, the built `PlanningSession.metadata.extra`, and `PipelineResult.metadata` - and is also recorded directly in `AgentResponse.metadata`.
- Added `factory/packages/026_AGENT_SESSION.md`.
- Added `tests/test_agent_session.py` (12 new tests), `tests/test_agent_request.py` (12 new tests), `tests/test_agent_response.py` (11 new tests), `tests/test_agent_service.py` (36 new tests) - covering lifecycle gating, empty/populated sessions, pipeline invocation, immutable objects, dependency failures, response wrapping, and metadata propagation.
- Added 3 new tests to `tests/test_bootstrap.py` (`agent_service` registered in the container; not started by `bootstrap()` itself; a full end-to-end `initialize()`/`start()`/`run()`/`stop()` call against the real bootstrapped `CognitivePipeline`).

### Changed

- `argus/bootstrap.py`: registered `AgentService` as the twenty-third core service and thirteenth `IService` adopter - "the second new runtime service since Package 021" (after the Cognitive Pipeline, Package 025). Constructed immediately after `cognitive_pipeline`, depending on `cognitive_pipeline` alone (already constructed earlier in the sequence). Startup Sequence gained a new step 24 ("Construct the Agent Service"); the prior steps 24/25 renumbered to 25/26; `_register_core_services()` gained an `agent_service: IAgentService` parameter and the twenty-third entry in its `core_services` tuple.
- `tests/test_bootstrap.py` / `argus/tests/test_bootstrap.py`: `CORE_SERVICE_NAMES` synced to include `"agent_service"`, per the standing Package 011 rule for the duplicate tree.

### Not Changed

- **`argus/runtime/`, `argus/planner/`, `argus/pipeline/`, `argus/decision/`, `argus/reasoning/`, `argus/context/`, `argus/planning/`, and `argus/conversation/` are all unchanged** - "Runtime: No changes. Planner: No changes. Pipeline: No changes. Conversation: No changes."
- **`argus/events/event_types.py` was intentionally left unchanged** - "No new EventTypes. Reuse existing behavior."
- No AI or LLM integration, no execution, no persistence - "Agent Service is an orchestration layer only."
- **File naming deviates from this package's own listed file names**: the work order's "New Package" section lists six files for `argus/agent/` with no dedicated file for `AgentService`'s own concrete implementation (unlike Package 025's own listing, which named `pipeline.py` explicitly). Resolved by adding one additional file, `service.py`, not named in the work order, rather than placing the concrete `AgentService` inside `interfaces.py` - preserving this codebase's own unbroken "interfaces.py holds an ABC only, never a concrete class" convention. See `factory/packages/026_AGENT_SESSION.md` and `argus/agent/service.py`'s own module docstring for the full reasoning.

### ADR Update

- `design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md` gained an Empirical Finding for Package 026. `IAgentService` inheriting `IService` was again an explicit instruction, but ADR-0002's criterion, applied independently to `run()`'s effectful delegation to a live `CognitivePipeline`, would have suggested adoption on its own too - making `AgentService` the **third** convergent case in this codebase, after Memory Integration (Package 019) and the Cognitive Pipeline (Package 025), and bringing the running tally to an even three divergent, three convergent across six directed-adoption data points - the first point in this ADR's history where the two shapes are exactly balanced.

### Known Limitations

- `AgentResponse` wraps the `PipelineResult` only - no natural-language response is generated anywhere in this package; a caller wanting one must build it from `pipeline_result` themselves, in a future package explicitly scoped to do so.
- `AgentRequest.conversation` is never cross-validated against `request.session.conversation` - the two are independent fields, matching this codebase's own "no validation beyond isinstance checks" restraint elsewhere.
- `AgentService` holds no `IEventBus` reference - by design, since it has nothing of its own to publish.
- No AI, no optimization, no persistence, no concurrency - unchanged from every prior package in this phase.
- The Agent Session is not yet invoked automatically by anything - it is available to any caller holding an `AgentRequest`, but no automatic trigger (a Connector, a Scheduler tick, or similar) exists yet.

## Package 027 - Response Engine

### Added

- Added `argus/response/` (`__init__.py`, `engine.py`, `response.py`, `metadata.py`, `interfaces.py`, `exceptions.py`) - the first-generation Response Engine, converting a validated Plan into a standardized Response: `User -> Agent Service -> Cognitive Pipeline -> ... -> Validated Plan -> Response Engine -> Response`. "The Response Engine converts a validated Plan into a structured response object. It does not generate AI text. It does not execute plans. It does not communicate with the user interface. Its responsibility is to transform cognitive output into a standardized response contract."
- `Response` (`argus/response/response.py`) - immutable, `plan`, `response_id`, `status` (copied from `plan.status`), `metadata` (a `ResponseMetadata`, not a bare mapping). "Do not include natural-language text. Do not include markdown. Do not include rendering. The Response object represents a completed cognitive result only."
- `ResponseMetadata` (`argus/response/metadata.py`) - immutable, mirrors `ContextMetadata`/`PlanningMetadata`'s shape (`version`, `correlation_id`, `extra`), with one explicit field-name deviation the work order itself specifies: `timestamp`, not `created_at`.
- `IResponseEngine` (`argus/response/interfaces.py`) - inherits `IService`, per explicit instruction/Testing-category reading; declares one abstract method, `build_response(plan: Plan) -> Response`.
- `ResponseEngine` (`argus/response/engine.py`) - implements `IResponseEngine`. `build_response()` performs exactly three steps: validate the Plan reference, construct a Response (copying `plan.status` and `plan.metadata`), return it. Takes **no constructor dependency at all** - the first core service in this codebase for which that is true, since "ResponseEngine may depend only on: Plan" and `Plan` is a per-call argument, never injected. `build_response()` is never gated on the engine's own lifecycle state, mirroring `KnowledgeGraph`/`ReasoningEngine`/`DecisionEngine`'s identical "adopts IService, gates nothing" shape.
- `ResponseError`, `InvalidPlanReferenceError` (`argus/response/exceptions.py`) - `InvalidPlanReferenceError` for a non-`Plan` argument to `build_response()`; `ResponseError` directly, for an invalid `IService` lifecycle transition. No "wrap a delegate's own exception" subtype - `ResponseEngine` has no delegate to fail on.
- Metadata propagation: `build_response()` copies `dict(plan.metadata)` into the returned `Response.metadata.extra` unchanged - the only metadata source available to `ResponseEngine`, which never sees the original `AgentRequest`/`PipelineRequest` metadata (that chain terminates at `PipelineResult.metadata`, Package 025).
- Added `factory/packages/027_RESPONSE_ENGINE.md`.
- Added `tests/test_response.py` (12 new tests), `tests/test_response_metadata.py` (10 new tests), `tests/test_response_engine.py` (26 new tests) - covering identity, lifecycle, ungated behavior, valid/invalid plans, immutability, metadata propagation, and the "no dependency to fail on" shape.
- Added 3 new tests to `tests/test_bootstrap.py` (`response_engine` registered in the container; not started by `bootstrap()` itself; `build_response()` works against the real bootstrapped instance even while unstarted, demonstrating the ungated behavior directly).

### Changed

- **`argus/agent/response.py`** - `AgentResponse.pipeline_result: PipelineResult` renamed and retyped to `AgentResponse.response: Response`, per this package's own explicit "Agent Integration" instruction ("Return AgentResponse now containing: Response instead of: PipelineResult"). A breaking field rename, not an additive change - `PipelineResult` is no longer held anywhere on `AgentResponse`.
- **`argus/agent/service.py`** - `AgentService.__init__()` gained a second required dependency, `response_engine: IResponseEngine`. `run()` gained a fifth step between the prior "invoke `cognitive_pipeline.run()`" and "return `AgentResponse`" steps: invoke `response_engine.build_response(pipeline_result.plan)`, wrapping any exception as `AgentExecutionError` (the same shape used for `cognitive_pipeline.run()` failures).
- **`argus/agent/interfaces.py`** - `IAgentService.run()`'s own docstring updated to describe the five-step sequence and both delegated-call failure paths; no change to the abstract method's own signature.
- **`argus/bootstrap.py`**: registered `ResponseEngine` as the twenty-fourth core service and fourteenth `IService` adopter (fifth zero-gated). Constructed immediately after `cognitive_pipeline` and immediately before `agent_service`, per the explicit "Planner -> Pipeline -> Response Engine -> Agent Service" dependency order. `AgentService`'s own construction updated to pass `response_engine=response_engine`. Startup Sequence gained a new step 24 ("Construct the Response Engine"); the prior Agent Service/registration/application steps renumbered 25/26/27; `_register_core_services()` gained a `response_engine: IResponseEngine` parameter and the twenty-fourth entry in its `core_services` tuple.
- `tests/test_bootstrap.py` / `argus/tests/test_bootstrap.py`: `CORE_SERVICE_NAMES` synced to include `"response_engine"`, per the standing Package 011 rule for the duplicate tree; the pre-existing Package 026 end-to-end test updated for the `response`/`pipeline_result` field rename.

### Not Changed

- **`argus/pipeline/` is completely unchanged** - "The Pipeline remains completely unchanged," confirmed via `git diff --stat -- argus/pipeline` showing zero lines changed.
- **`argus/runtime/`, `argus/planner/`, `argus/planning/`, `argus/context/`, `argus/conversation/`, `argus/memory/`, `argus/memory_integration/`, `argus/knowledge/`, `argus/knowledge_graph/`, `argus/decision/`, `argus/reasoning/` are all unchanged** - "Runtime: No changes. Pipeline: No changes. Planner: No changes. Memory: No changes. Knowledge: No changes."
- **`argus/events/event_types.py` was intentionally left unchanged** - "No new EventTypes."
- No AI or LLM integration, no formatting, no rendering, no persistence - "The Response Engine is a transformation layer only."

### ADR Update

- `design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md` gained an Empirical Finding for Package 027. `IResponseEngine` inheriting `IService` was again read from the "core service" + "lifecycle" Testing-category convention, but ADR-0002's criterion, applied independently to `build_response()`'s purely synchronous, in-memory, no-collaborator transformation, would NOT have suggested adoption - the **fourth** divergent case (after Packages 018, 020, 021), breaking the exact three-divergent/three-convergent tie Package 026's own finding established. `ResponseEngine` is also the first core service in this codebase's history with a fully empty constructor.

### Known Limitations

- `Response` wraps the `Plan` only - no natural-language text, markdown, or rendering anywhere in this package; a caller wanting any of those must build it from `response.plan` themselves, in a future package explicitly scoped to do so.
- `ResponseMetadata.extra` only ever reflects `plan.metadata` (`planning_session_id`, `cognitive_context_id`, `constraints`) - the original `AgentRequest`/`PipelineRequest` metadata (`agent_request_id`, caller-supplied keys) is not visible inside it, since `ResponseEngine` never sees that data at all; those keys remain directly visible on `AgentResponse.metadata` itself, one layer up.
- `ResponseEngine.build_response()` is never gated - callers may invoke it at any lifecycle state, including before `initialize()`/`start()` are ever called.
- No AI, no optimization, no persistence, no concurrency - unchanged from every prior package in this phase.
- The Response Engine is not yet invoked by anything except `AgentService` - no other caller exists yet.
