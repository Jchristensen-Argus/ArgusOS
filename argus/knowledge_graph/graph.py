"""
KnowledgeGraph: in-memory implementation of IKnowledgeGraph for the
ArgusOS Knowledge Graph.

Purpose:
    Implement IKnowledgeGraph: an in-memory registry of Entities and
    the directed Relationships connecting them, exposing
    add/remove/get/list for both, plus `neighbors()` and
    `find_by_type()` as the package's only two "graph query"
    operations - per factory/packages/018_KNOWLEDGE_GRAPH.md. The
    Knowledge Graph is a structured semantic layer only: it is not a
    database, not long-term storage, not vector search, and performs
    no persistence, no graph traversal algorithms (no shortest path),
    and no inference.

Cascading Removal:
    remove_entity() also removes every Relationship that references
    the removed Entity as `source_entity_id` or `target_entity_id`,
    keeping the graph's own referential integrity intact by
    construction: a Relationship can never outlive either Entity it
    connects. This is a deliberate design decision, not a requirement
    stated verbatim anywhere in the work order - see this module's own
    "Architectural Decision - Cascading Removal" note in
    factory/packages/018_KNOWLEDGE_GRAPH.md for the full rationale
    (the alternative, forbidding removal of an Entity with existing
    Relationships, was considered and rejected as unnecessary
    complexity for "lightweight infrastructure"). Cascaded removals do
    not publish their own RELATIONSHIP_REMOVED events - see this
    class's remove_entity() docstring.

Responsibilities:
    - KnowledgeGraph: the sole implementation of IKnowledgeGraph.

Non-Responsibilities:
    - KnowledgeGraph never executes Plans, calls Connectors, stores
      files, performs persistence, or communicates externally - see
      this package's Objective and Constraints.
    - KnowledgeGraph performs no graph traversal algorithms (no
      shortest path, no multi-hop queries) and no inference -
      `neighbors()` is a single-hop lookup only.

Dependencies:
    argus.knowledge_graph.entity (Entity), argus.knowledge_graph.
    exceptions, argus.knowledge_graph.interfaces (IKnowledgeGraph),
    argus.knowledge_graph.relationship (Relationship), argus.events
    (Event, EventType, IEventBus), argus.lifecycle.lifecycle
    (LifecycleState).
"""

from typing import Dict, Sequence

from argus.events.event import Event
from argus.events.event_types import EventType
from argus.events.interfaces import IEventBus
from argus.knowledge_graph.entity import Entity
from argus.knowledge_graph.exceptions import (
    DuplicateEntityError,
    DuplicateRelationshipError,
    EntityNotFoundError,
    InvalidEntityError,
    InvalidRelationshipError,
    KnowledgeGraphError,
    RelationshipNotFoundError,
)
from argus.knowledge_graph.interfaces import IKnowledgeGraph
from argus.knowledge_graph.relationship import Relationship
from argus.lifecycle.lifecycle import LifecycleState


class KnowledgeGraph(IKnowledgeGraph):
    """
    In-memory implementation of IKnowledgeGraph.

    Purpose:
        Track registered Entities and the Relationships connecting
        them, and answer the package's two supported query
        operations, `neighbors()` and `find_by_type()`. See the
        module docstring for the full design rationale.

    Dependencies:
        An IEventBus, injected by the caller (bootstrap.py).
    """

    def __init__(self, event_bus: IEventBus) -> None:
        self._event_bus = event_bus
        self._entities: Dict[str, Entity] = {}
        self._relationships: Dict[str, Relationship] = {}
        self._state: LifecycleState = LifecycleState.CREATED

    # -- IService (see interfaces.py's Architectural Note: adopted per
    #    explicit instruction; no method below is gated on RUNNING) --

    def initialize(self) -> None:
        if self._state != LifecycleState.CREATED:
            raise KnowledgeGraphError(
                f"Cannot initialize: KnowledgeGraph is {self._state.name}, expected CREATED."
            )
        self._state = LifecycleState.INITIALIZING

    def start(self) -> None:
        if self._state != LifecycleState.INITIALIZING:
            raise KnowledgeGraphError(
                f"Cannot start: KnowledgeGraph is {self._state.name}, expected INITIALIZING."
            )
        self._state = LifecycleState.RUNNING

    def stop(self) -> None:
        if self._state != LifecycleState.RUNNING:
            raise KnowledgeGraphError(
                f"Cannot stop: KnowledgeGraph is {self._state.name}, expected RUNNING."
            )
        self._state = LifecycleState.STOPPING
        self._state = LifecycleState.STOPPED

    def status(self) -> LifecycleState:
        return self._state

    # -- IKnowledgeGraph: entities ---------------------------------------

    def add_entity(self, entity: Entity) -> None:
        if not isinstance(entity, Entity):
            raise InvalidEntityError(f"add_entity() requires an Entity, got {entity!r}.")
        if not entity.id:
            raise InvalidEntityError("Entity.id must be non-empty.")
        if not entity.entity_type:
            raise InvalidEntityError("Entity.entity_type must be non-empty.")
        if not entity.name:
            raise InvalidEntityError("Entity.name must be non-empty.")
        if entity.id in self._entities:
            raise DuplicateEntityError(f"Entity {entity.id!r} is already registered.")

        self._entities[entity.id] = entity
        self._publish(EventType.ENTITY_ADDED, {"entity_id": entity.id})

    def remove_entity(self, entity_id: str) -> None:
        """
        Removes the Entity, then cascades: every Relationship whose
        `source_entity_id` or `target_entity_id` equals `entity_id` is
        also removed. Publishes exactly one ENTITY_REMOVED event for
        the Entity itself; cascaded Relationship removals do not each
        publish their own RELATIONSHIP_REMOVED event, since they are a
        consequence of this single call, not independent
        remove_relationship() calls - matching this codebase's
        established "one call, one event" precedent (for example,
        ConnectorManager.unregister_connector() publishing nothing at
        all, per Package 017).
        """
        self._require_entity(entity_id)

        stale_relationship_ids = [
            relationship_id
            for relationship_id, relationship in self._relationships.items()
            if relationship.source_entity_id == entity_id
            or relationship.target_entity_id == entity_id
        ]
        for relationship_id in stale_relationship_ids:
            del self._relationships[relationship_id]

        del self._entities[entity_id]
        self._publish(EventType.ENTITY_REMOVED, {"entity_id": entity_id})

    def get_entity(self, entity_id: str) -> Entity:
        return self._require_entity(entity_id)

    def list_entities(self) -> Sequence[Entity]:
        return tuple(self._entities.values())

    # -- IKnowledgeGraph: relationships -----------------------------------

    def add_relationship(self, relationship: Relationship) -> None:
        if not isinstance(relationship, Relationship):
            raise InvalidRelationshipError(
                f"add_relationship() requires a Relationship, got {relationship!r}."
            )
        if not relationship.id:
            raise InvalidRelationshipError("Relationship.id must be non-empty.")
        if not relationship.relationship_type:
            raise InvalidRelationshipError("Relationship.relationship_type must be non-empty.")
        if not relationship.source_entity_id:
            raise InvalidRelationshipError("Relationship.source_entity_id must be non-empty.")
        if not relationship.target_entity_id:
            raise InvalidRelationshipError("Relationship.target_entity_id must be non-empty.")
        if relationship.id in self._relationships:
            raise DuplicateRelationshipError(
                f"Relationship {relationship.id!r} is already registered."
            )
        # Invalid-reference check: both endpoints must already exist.
        self._require_entity(relationship.source_entity_id)
        self._require_entity(relationship.target_entity_id)

        self._relationships[relationship.id] = relationship
        self._publish(EventType.RELATIONSHIP_ADDED, {"relationship_id": relationship.id})

    def remove_relationship(self, relationship_id: str) -> None:
        self._require_relationship(relationship_id)
        del self._relationships[relationship_id]
        self._publish(EventType.RELATIONSHIP_REMOVED, {"relationship_id": relationship_id})

    def list_relationships(self) -> Sequence[Relationship]:
        return tuple(self._relationships.values())

    # -- IKnowledgeGraph: queries -----------------------------------------

    def neighbors(self, entity_id: str) -> Sequence[Entity]:
        """
        Every Relationship's endpoints are guaranteed, by construction,
        to reference Entities that currently exist -
        add_relationship() rejects unknown endpoints, and
        remove_entity() cascades to remove every Relationship
        referencing a removed Entity (see this module's own Cascading
        Removal note) - so every id collected below is always safe to
        resolve directly against `self._entities`.
        """
        self._require_entity(entity_id)

        neighbor_ids = []
        for relationship in self._relationships.values():
            if relationship.source_entity_id == entity_id:
                other_id = relationship.target_entity_id
            elif relationship.target_entity_id == entity_id:
                other_id = relationship.source_entity_id
            else:
                continue
            if other_id not in neighbor_ids:
                neighbor_ids.append(other_id)

        return tuple(self._entities[other_id] for other_id in neighbor_ids)

    def find_by_type(self, entity_type: str) -> Sequence[Entity]:
        return tuple(
            entity for entity in self._entities.values() if entity.entity_type == entity_type
        )

    # -- internal helpers -------------------------------------------------

    def _require_entity(self, entity_id: str) -> Entity:
        if not isinstance(entity_id, str) or not entity_id:
            raise InvalidEntityError("entity_id must be a non-empty string.")
        try:
            return self._entities[entity_id]
        except KeyError:
            raise EntityNotFoundError(f"No entity registered under {entity_id!r}.")

    def _require_relationship(self, relationship_id: str) -> Relationship:
        if not isinstance(relationship_id, str) or not relationship_id:
            raise InvalidRelationshipError("relationship_id must be a non-empty string.")
        try:
            return self._relationships[relationship_id]
        except KeyError:
            raise RelationshipNotFoundError(f"No relationship registered under {relationship_id!r}.")

    def _publish(self, event_type: EventType, payload: dict) -> None:
        self._event_bus.publish(
            Event(type=event_type, source="knowledge_graph", payload=payload)
        )
