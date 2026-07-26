"""
Exceptions raised by the ArgusOS Memory Integration bridge.

Purpose:
    Give callers explicit, catchable failure modes for memory-to-graph
    translation, synchronization, and lifecycle failures, per the
    coding standard's "raise meaningful exceptions... never silently
    ignore errors" and factory/packages/019_MEMORY_INTEGRATION.md.
    Mirrors the exception hierarchy shape already established by
    argus.knowledge_graph.exceptions (Package 018),
    argus.connectors.exceptions (Package 017), and
    argus.runtime.exceptions (Package 016). Memory Integration never
    lets a raw argus.memory or argus.knowledge_graph exception escape
    its own public API unwrapped - every failure surfaces as one of
    these, per this package's own "owns the bridge" boundary.

Responsibilities:
    - Provide a general memory-integration-subsystem error base, and
      more specific subtypes for "invalid memory record," "mapping
      failed," "not currently synchronized," and "invalid IService
      lifecycle state" failures.

Non-Responsibilities:
    - These exceptions carry no behavior beyond a message; they do
      not log, retry, or recover.

Dependencies:
    None.
"""


class MemoryIntegrationError(Exception):
    """Base exception for the Memory Integration subsystem. Raised
    directly for failures that are not one of the more specific
    subtypes below."""


class InvalidMemoryRecordError(MemoryIntegrationError):
    """Raised when a MemoryMapper method is given something that is
    not a MemoryRecord, or a MemoryRecord with an empty key - or when
    synchronize_memory()/remove_memory() is given a non-string or
    empty key."""


class MemoryMappingError(MemoryIntegrationError):
    """Raised when translating a MemoryRecord into a graph Entity, or
    adding it to the Knowledge Graph, fails. Wraps the underlying
    argus.knowledge_graph exception; the triggering failure is
    published as MEMORY_MAPPING_FAILED before this is raised."""


class MemoryNotSynchronizedError(MemoryIntegrationError):
    """Raised by remove_memory() when the given key has no
    corresponding Entity currently tracked as synchronized."""


class InvalidMemoryIntegrationStateError(MemoryIntegrationError):
    """Raised by synchronize_memory()/synchronize_all()/remove_memory()
    when the MemoryIntegration service's own IService lifecycle state
    is not RUNNING."""
