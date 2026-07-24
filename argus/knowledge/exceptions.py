"""
Exceptions raised by the ArgusOS Knowledge Service.

Purpose:
    Give callers explicit, catchable failure modes for knowledge
    operations, per the coding standard's "explicit exceptions instead
    of silent failures" and factory/packages/006_KNOWLEDGE_SERVICE.md.

Responsibilities:
    - Provide a general knowledge-subsystem error base, and more
      specific subtypes for "not found" and "duplicate key" failures,
      so callers can catch either the broad or the precise failure
      mode.

Non-Responsibilities:
    - These exceptions carry no behavior beyond a message; they do not
      log, retry, or recover.

Dependencies:
    None.
"""


class KnowledgeError(Exception):
    """Base exception for the knowledge subsystem. Raised directly for
    failures that are not specifically "not found" or "duplicate key",
    such as an empty key/category or a malformed record on disk."""


class KnowledgeNotFoundError(KnowledgeError):
    """Raised when an operation references a knowledge key that has no
    corresponding record."""


class DuplicateKnowledgeError(KnowledgeError):
    """Raised when put() is called with a key that is already present
    in the knowledge store."""
