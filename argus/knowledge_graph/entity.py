"""
The Entity value object for the ArgusOS Knowledge Graph.

Purpose:
    Represent a single, immutable node in the Knowledge Graph's
    in-memory semantic graph - identity, type, human-readable name,
    and arbitrary descriptive attributes - per
    factory/packages/018_KNOWLEDGE_GRAPH.md. An Entity is pure data:
    it holds no live reference to any Relationship, and does not know
    what it is connected to. KnowledgeGraph (argus/knowledge_graph/
    graph.py) is the only component that tracks which Relationships
    reference a given Entity.

Naming Note - `id`, not `entity_id`:
    This package's work order suggests `entity_id` as a field name.
    Every prior value object in this codebase names its own identity
    field `id` (Capability.id, Plugin.id, Plan.id, PlanStep.id,
    Execution.id, Connector.id) and is referenced by outside callers
    via a `*_id`-suffixed parameter name instead (e.g.
    KnowledgeGraph.get_entity(entity_id)). This module follows that
    established convention: the field here is `id`; the Knowledge
    Graph's own public methods use `entity_id` for the parameter name
    that refers to it.

Responsibilities:
    - Entity: hold node identity and metadata as an immutable value
      object.

Non-Responsibilities:
    - Entity does not register, remove, or look itself up - see
      argus.knowledge_graph.interfaces.IKnowledgeGraph and
      argus.knowledge_graph.graph.KnowledgeGraph.
    - This module has no dependency on any other
      argus.knowledge_graph module, matching the "pure,
      dependency-free leaf" precedent set by
      argus.capability.capability, argus.plugins.plugin,
      argus.planner.plan, argus.runtime.execution, and
      argus.connectors.connector.

Dependencies:
    None beyond the standard library.
"""

import uuid
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True)
class Entity:
    """
    An immutable node in the Knowledge Graph.

    Fields:
        entity_type: The kind of thing this Entity represents (for
            example, "person", "workflow", "concept"). Required,
            non-empty. A plain string, not a closed enum - the
            Knowledge Graph imposes no fixed taxonomy in Version 1.
        name: Human-readable name. Required, non-empty. Not enforced
            unique - lookup is always by `id`, never by `name`,
            matching every other registry in this codebase.
        id: Unique identifier for this Entity. Defaults to a fresh
            uuid4 string.
        attributes: Arbitrary additional descriptive data. Defaults to
            an empty mapping.
    """

    entity_type: str
    name: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "attributes", MappingProxyType(dict(self.attributes)))
