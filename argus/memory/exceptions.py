"""
Exceptions raised by the ArgusOS Memory Service.

Purpose:
    Give callers explicit, catchable failure modes for memory
    operations, per the coding standard's "explicit exceptions instead
    of silent failures" and factory/packages/007_MEMORY_SERVICE.md.

Responsibilities:
    - Provide a general memory-subsystem error base, and more specific
      subtypes for "not found" and "duplicate key" failures, so callers
      can catch either the broad or the precise failure mode.

Non-Responsibilities:
    - These exceptions carry no behavior beyond a message; they do not
      log, retry, or recover.

Dependencies:
    None.
"""


class MemoryServiceError(Exception):
    """Base exception for the memory subsystem.

    Named MemoryServiceError rather than MemoryError because
    MemoryError is a built-in Python exception (raised by the
    interpreter for out-of-memory conditions); shadowing it would
    confuse callers and break code that catches the built-in. Raised
    directly for failures that are not specifically "not found" or
    "duplicate key", such as an empty key or a malformed record on
    disk.
    """


class MemoryNotFoundError(MemoryServiceError):
    """Raised when an operation references a memory key that has no
    corresponding, non-expired record."""


class DuplicateMemoryError(MemoryServiceError):
    """Raised when put() is called with a key that is already present
    in the memory store."""
