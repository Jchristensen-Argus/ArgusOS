"""
The Relationship value object for the ArgusOS Knowledge Graph.

Purpose:
    Represent a single, immutable, directed edge in the Knowledge
    Graph's in-memory semantic graph - connecting a source Entity to a
    target Entity by id, with a type and arbitrary descriptive
    attributes - per factory/packages/018_KNOWLEDGE_GRAPH.md. A
    Relationship is pure data: it holds no live reference to either
    Entity it connects, only their `id`s. KnowledgeGraph (argus/
    knowledge_graph/graph.py) is the only component that resolves a
    Relationship's `source_entity_id`/`target_entity_id` against
    actual registered Entities.

Naming Notes:
    - `id`, not `relationship_id`, for this model's own identity
      field - the same established convention already applied to
      `Entity.id` (see entity.py's own Naming Note), `Capability.id`,
      `Plugin.id`, `Plan.id`, `PlanStep.id`, `Execution.id`, and
      `Connector.id`.
    - `source_entity_id`/`target_entity_id`, not the work order's
      literal `source_entity`/`target_entity` suggestion. Every prior
      reference-to-another-model field in this codebase carries an
      explicit `_id` suffix (`Capability.workflow_id`,
      `Execution.plan_id`) specifically to make unambiguous that the
      field holds an id string, not a live object reference - a
      Relationship holding live `Entity` objects would violate this
      package's own "pure data, no live references" requirement and
      would go stale the moment an Entity were removed and re-added
      under a new object identity. `source_entity_id`/
      `target_entity_id` follow that same established convention.

Responsibilities:
    - Relationship: hold edge identity, its two endpoint Entity ids,
      type, and metadata as an immutable value object.

Non-Responsibilities:
    - Relationship does not register, remove, or look itself up, and
      does not verify that its `source_entity_id`/`target_entity_id`
      refer to Entities that actually exist - see
      argus.knowledge_graph.graph.KnowledgeGraph.add_relationship()
      for that check.
    - This module has no dependency on any other
      argus.knowledge_graph module (not even entity.py) - matching
      the "pure, dependency-free leaf" precedent set by every other
      value object in this codebase.

Dependencies:
    None beyond the standard library.
"""

import uuid
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True)
class Relationship:
    """
    An immutable, directed edge in the Knowledge Graph.

    Fields:
        source_entity_id: The `id` of the Entity this edge originates
            from. Required, non-empty.
        target_entity_id: The `id` of the Entity this edge points to.
            Required, non-empty. May equal `source_entity_id` (a
            self-loop) - Version 1 does not forbid this.
        relationship_type: The kind of connection this edge
            represents (for example, "reports_to", "depends_on").
            Required, non-empty. A plain string, not a closed enum,
            matching `Entity.entity_type`.
        id: Unique identifier for this Relationship. Defaults to a
            fresh uuid4 string.
        attributes: Arbitrary additional descriptive data. Defaults to
            an empty mapping.
    """

    source_entity_id: str
    target_entity_id: str
    relationship_type: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "attributes", MappingProxyType(dict(self.attributes)))
