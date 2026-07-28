"""
DEPRECATED — pre-Factory prototype, retired per ADR-0004.

This module (and its siblings brain.py, commands.py, conversation.py,
identity.py, memory.py, shell.py) was never wired into bootstrap.py or
main.py, and was already import-broken at the time of removal (its
`from argus.memory import Memory` resolved to the real Package 007
package, not this file's own sibling — Package 007's MemoryService has
no class named `Memory`). Content replaced with this stub rather than
the file being deleted outright, because this session's sandbox mount
does not permit file deletion; deleting these paths from the working
tree is a manual follow-up. See design/decisions/0004_REMOVE_LEGACY_PROTOTYPE.md
for full context. Do not import from this module.
"""
