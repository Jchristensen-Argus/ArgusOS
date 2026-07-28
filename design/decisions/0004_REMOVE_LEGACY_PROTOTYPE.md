# ADR-0004: Remove the Pre-Factory Prototype (ai.py, brain.py, commands.py, conversation.py, identity.py, memory.py, shell.py)

## Status

Accepted

---

## Date

2026-07-27

---

## Context

Seven files at the top level of `argus/` — `ai.py`, `brain.py`, `commands.py`, `conversation.py`, `identity.py`, `memory.py`, `shell.py` — predate the Factory package system (001–041). They implement a small interactive-shell prototype: an Ollama-backed chat loop, a JSON-file memory list, a keyword-based `Brain.think()` router, and a `CommandManager`/`Shell` REPL.

A full repository verification pass (2026-07-27, ahead of Sprint 1) confirmed three things about this code, not assumed:

- **Not wired in.** `main.py`'s own docstring states plainly that "the pre-Factory interactive Shell (`argus/shell.py`) is intentionally not invoked here pending a future implementation package that reintegrates it." `bootstrap.py` does not reference any of the seven files. Nothing in the numbered `argus/` packages (007+) imports them either.
- **Currently broken, not merely unused.** `argus/memory.py` and `argus/conversation.py` are flat modules sharing a name with the real packages `argus/memory/` (Package 007) and `argus/conversation/` (Package 011). Python's import system resolves `argus.memory`/`argus.conversation` to the package directories, not the flat files, so `ai.py`, `commands.py`, and `shell.py` — each of which does `from argus.memory import Memory` — raise `ImportError` immediately on import, verified empirically. `identity.py` and `brain.py` alone import cleanly, but both are dead: nothing calls them.
- **No design doc.** Unlike every package in the 001–041 series, no `factory/packages/*.md` document describes this code's rationale — there is no framework document this removal would be orphaning, per ADR-0003's own standard for what counts as a canonical artifact.

Leaving broken, unreferenced code alongside a clean, fully-tested 41-package architecture creates real risk for exactly the audience ADR-0003 and this repository's conventions are written for: a future contributor (human or AI) encountering `argus/memory.py` next to `argus/memory/` with no explanation of which one is real.

## Decision

Retire `argus/ai.py`, `argus/brain.py`, `argus/commands.py`, `argus/conversation.py`, `argus/identity.py`, `argus/memory.py`, and `argus/shell.py`.

**Implementation note, recorded here rather than left implicit:** the intended action was outright file deletion. The working environment this decision was executed in could not delete files at the filesystem level (verified — a `rm` on a file created in the same session, moments earlier, also failed with a permission error; this is a mount-level restriction, not specific to these seven files). Each file's content was replaced with a short deprecation stub pointing back to this ADR instead. The practical effect is the same — none of the seven contain reachable code any longer, and each states plainly not to import from it — but the files still physically exist in the tree pending a manual `git rm` outside this environment. This gap is tracked as an open item below rather than glossed over.

This is not a migration — no functionality moves anywhere, because none of these seven files were reachable from any live entry point (see Context above). If interactive-shell functionality is wanted in the future, it should be built as a proper Module or Core capability against the current architecture (Core/Module/Integration, per the Cognitive Architecture and the Sales OS precedent), not reintroduced from this prototype, whose two working files (`identity.py`, `brain.py`) predate every naming and value-object convention now in use across 001–041.

Full git history preserves the original content regardless of how this is finished.

## Consequences

Positive

- Removes the only import-broken code in the repository.
- Removes the only unexplained divergence from the "every module has a framework document" convention ADR-0003 establishes.
- Eliminates the specific name-collision risk (`argus/memory.py` vs. `argus/memory/`, `argus/conversation.py` vs. `argus/conversation/`) that caused the breakage in the first place.

Trade-offs

- None identified. No code path depended on these files; removal changes no runtime behavior, verified by re-running `python -c "from argus.bootstrap import bootstrap"` after removal (see verification note below).

## Verification

After content replacement, `argus.bootstrap.bootstrap` was re-imported successfully and the existing test suite's collection was confirmed unaffected — no test file under `tests/` referenced any of the seven retired files.

## Open Item

Physical removal of these seven now-empty-of-logic files from the working tree (`git rm argus/ai.py argus/brain.py argus/commands.py argus/conversation.py argus/identity.py argus/memory.py argus/shell.py`) should be completed outside this session, wherever file deletion is possible. Until then, each file's stub content is the authoritative signal that it is retired, not the file's absence.

## Related Documents

- `design/decisions/0003_FRAMEWORK_DOCUMENTS_AS_CANONICAL_SOURCE.md`
- `factory/standards/FRAMEWORK_DOCUMENT_LOCATION_CONVENTION.md`
