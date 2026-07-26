"""
Exceptions raised by the ArgusOS Reasoning Engine.

Purpose:
    Give callers explicit, catchable failure modes for invalid
    reasoning queries and unresolvable graph references, per the
    coding standard's "raise meaningful exceptions... never silently
    ignore errors" and factory/packages/020_REASONING_ENGINE.md.
    Mirrors the exception hierarchy shape already established by
    argus.knowledge_graph.exceptions (Package 018) and
    argus.memory_integration.exceptions (Package 019). The Reasoning
    Engine never lets a raw argus.knowledge_graph exception escape its
    own public API unwrapped - every failure surfaces as one of these,
    matching Memory Integration's own "owns the bridge, not the
    systems it bridges" boundary discipline, applied here to "owns the
    reasoning layer, not the graph."

Responsibilities:
    - Provide a general reasoning-subsystem error base, and more
      specific subtypes for "invalid query/parameters" and
      "referenced entity or relationship does not exist" failures.

Non-Responsibilities:
    - These exceptions carry no behavior beyond a message; they do
      not log, retry, or recover.
    - No dedicated lifecycle-state exception exists here - unlike
      Memory Integration (Package 019), none of the Reasoning Engine's
      public methods are gated on the RUNNING state, so no method can
      ever raise for that reason. ReasoningError is used directly for
      the Reasoning Engine's own IService lifecycle transition
      failures (initialize()/start()/stop() called out of order),
      exactly mirroring KnowledgeGraphError's identical role in
      argus/knowledge_graph/exceptions.py - see
      argus/reasoning/interfaces.py's Architectural Note for why.

Dependencies:
    None.
"""


class ReasoningError(Exception):
    """Base exception for the Reasoning Engine subsystem. Raised
    directly for failures that are not one of the more specific
    subtypes below (for example, an invalid IService lifecycle
    transition)."""


class InvalidReasoningQueryError(ReasoningError):
    """Raised when a public ReasoningEngine method is given a
    malformed ReasoningQuery, or invalid parameters directly (a
    non-string or empty entity_id/relationship_type, a non-positive
    depth or max_depth, or a ReasoningQuery with none of entity_id,
    entity_type, or relationship_type set)."""


class ReasoningTargetNotFoundError(ReasoningError):
    """Raised when a query references an entity_id (or, for
    find_paths(), a source_entity_id/target_entity_id) with no
    corresponding registered Entity in the Knowledge Graph. Wraps the
    underlying argus.knowledge_graph.exceptions.EntityNotFoundError -
    see this module's own docstring."""
