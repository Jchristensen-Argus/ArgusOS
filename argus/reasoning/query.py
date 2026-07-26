"""
The ReasoningQuery value object for the ArgusOS Reasoning Engine.

Purpose:
    Represent a single, immutable request describing what the
    Reasoning Engine should look up in the Knowledge Graph - by
    entity id (with an optional bounded traversal depth and
    relationship-type filter), by entity type, by relationship type,
    or by entity type and relationship type together (a simple graph
    pattern: "relationships of type R touching an entity of type T") -
    per factory/packages/020_REASONING_ENGINE.md. "Queries are
    immutable once created." A ReasoningQuery is pure data: it
    performs no lookup itself and holds no reference to any Entity or
    Relationship - argus.reasoning.engine.ReasoningEngine is the only
    component that interprets one against a live IKnowledgeGraph.

Naming Note:
    This module follows the work order's own suggested field names
    verbatim (entity_type, relationship_type, entity_id, depth,
    filters) - unlike Entity/Relationship (Package 018), there is no
    competing "id"-field convention to reconcile here, since
    ReasoningQuery has no identity of its own; it is a request, not a
    registered, individually-addressable record.

Field Semantics (interpreted by ReasoningEngine.query(); see
engine.py's module docstring for the full branching rules):
    - entity_id set: resolve that Entity, then traverse outward up to
      `depth` hops (default 1 = direct neighbors only), optionally
      restricted to Relationships whose relationship_type equals
      `relationship_type`.
    - entity_id unset, entity_type set, relationship_type unset:
      search Entities by entity_type only (mirrors
      IKnowledgeGraph.find_by_type()).
    - entity_id unset, relationship_type set, entity_type unset:
      search Relationships by relationship_type only.
    - entity_id unset, both entity_type and relationship_type set:
      evaluate the simple graph pattern "Relationships of
      relationship_type with at least one endpoint Entity of
      entity_type."
    - filters: applied uniformly, as an exact-match attribute
      subset test, to whichever of matched_entities/
      matched_relationships the active branch above produces - see
      engine.py's own `_matches_filters()`. Never used to change
      *which* branch above is taken.

Responsibilities:
    - ReasoningQuery: hold query parameters as an immutable value
      object.

Non-Responsibilities:
    - ReasoningQuery performs no validation beyond
      wrapping `filters` in a read-only mapping in __post_init__ -
      matching Entity's/Relationship's/Connector's own "pure leaf,
      validation lives in the consuming service" precedent
      (validation lives in ReasoningEngine; see engine.py).
    - This module has no dependency on argus.knowledge_graph or
      argus.reasoning.result - matching the "pure, dependency-free
      leaf" precedent set by every other value object in this
      codebase.

Dependencies:
    None beyond the standard library.
"""

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Optional


@dataclass(frozen=True)
class ReasoningQuery:
    """
    An immutable request describing what the Reasoning Engine should
    look up. See the module docstring for the full field semantics.

    Fields:
        entity_type: Restrict the search to Entities (or, in the
            combined-pattern branch, Relationship endpoints) of this
            entity_type. Optional.
        relationship_type: Restrict the search to Relationships of
            this relationship_type. Optional.
        entity_id: Resolve and traverse outward from this specific
            Entity. Optional.
        depth: Maximum number of hops to traverse outward from
            entity_id. Only consulted when entity_id is set. Defaults
            to 1 (direct neighbors only).
        filters: Attribute key/value pairs every matched Entity (or
            Relationship, in the relationship-type-only branch) must
            contain, as an exact-match subset test. Defaults to an
            empty mapping (no filtering).
    """

    entity_type: Optional[str] = None
    relationship_type: Optional[str] = None
    entity_id: Optional[str] = None
    depth: int = 1
    filters: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "filters", MappingProxyType(dict(self.filters)))
