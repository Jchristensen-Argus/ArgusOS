# Changelog

All notable changes to ArgusOS will be documented in this file.

---

# ArgusOS Changelog

---

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