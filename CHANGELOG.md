# Changelog

All notable changes to ArgusOS will be documented in this file.

---

# ArgusOS Changelog

---
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