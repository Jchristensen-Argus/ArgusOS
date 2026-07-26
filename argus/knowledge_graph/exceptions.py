"""
Exceptions raised by the ArgusOS Knowledge Graph.

Purpose:
    Give callers explicit, catchable failure modes for entity and
    relationship registration, lookup, removal, and graph-integrity
    violations, per the coding standard's "raise meaningful
    exceptions... never silently ignore errors" and
    factory/packages/018_KNOWLEDGE_GRAPH.md. Mirrors the exception
    hierarchy shape already established by
    argus.connectors.exceptions (Package 017),
    argus.runtime.exceptions (Package 016), and
    argus.planner.exceptions (Package 015).

Responsibilities:
    - Provide a general knowledge-graph-subsystem error base, and more
      specific subtypes for "invalid input," "duplicate," "not
      found," and "invalid reference" failures, for both Entities and
      Relationships.

Non-Responsibilities:
    - These exceptions carry no behavior beyond a message; they do
      not log, retry, or recover.

Dependencies:
    None.
"""


class KnowledgeGraphError(Exception):
    """Base exception for the Knowledge Graph subsystem. Raised
    directly for failures that are not one of the more specific
    subtypes below (for example, an invalid IService lifecycle
    transition)."""


class InvalidEntityError(KnowledgeGraphError):
    """Raised when add_entity() is given something that is not an
    Entity instance, or an Entity with an empty id, entity_type, or
    name - or when a lookup/removal method is given a non-string or
    empty entity_id."""


class DuplicateEntityError(KnowledgeGraphError):
    """Raised when add_entity() is called with an id that is already
    registered. Callers must call remove_entity() first to replace an
    existing Entity."""


class EntityNotFoundError(KnowledgeGraphError):
    """Raised when get_entity(), remove_entity(), neighbors(), or
    add_relationship()'s source_entity_id/target_entity_id reference
    an entity_id with no corresponding registered Entity."""


class InvalidRelationshipError(KnowledgeGraphError):
    """Raised when add_relationship() is given something that is not
    a Relationship instance, or a Relationship with an empty id,
    source_entity_id, target_entity_id, or relationship_type - or when
    a lookup/removal method is given a non-string or empty
    relationship_id."""


class DuplicateRelationshipError(KnowledgeGraphError):
    """Raised when add_relationship() is called with an id that is
    already registered. Callers must call remove_relationship() first
    to replace an existing Relationship."""


class RelationshipNotFoundError(KnowledgeGraphError):
    """Raised when remove_relationship() references a
    relationship_id with no corresponding registered Relationship."""
