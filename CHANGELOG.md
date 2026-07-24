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
