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
