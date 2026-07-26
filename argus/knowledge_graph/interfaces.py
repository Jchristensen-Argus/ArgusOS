"""
Public interface contract for the ArgusOS Knowledge Graph.

Purpose:
    Define IKnowledgeGraph, the contract other modules depend on, per
    factory/packages/018_KNOWLEDGE_GRAPH.md.

Architectural Note - IKnowledgeGraph Inherits IService, But No Method
Is Gated:
    Unlike every prior IService-adoption decision in this codebase,
    which was this Engineer's own judgment call applying ADR-0002's
    proposed criterion ("adopt IService only when start()/stop() would
    do real, distinct work"), this package's work order explicitly
    instructs "Create: IKnowledgeGraph - Extend IService" - adoption
    itself is not a judgment call here. Applying ADR-0002's criterion
    to this package's actual methods independently, however, would not
    have suggested adoption: add_entity/remove_entity/get_entity/
    list_entities/add_relationship/remove_relationship/
    list_relationships/neighbors/find_by_type are all synchronous,
    in-memory data operations with no external call, no dispatch, and
    no phase distinction any of them could plausibly be gated on - "It
    is an in-memory semantic graph" with "No graph algorithms yet...
    Only foundational graph operations," architecturally much closer
    to Capability Registry (013)/Plugin Manager (014)/Planner (015)
    (deliberate non-adopters) than to Agent Runtime (016)/Connector
    Manager (017) (genuinely gated adopters). Per the explicit
    instruction, `IKnowledgeGraph` DOES inherit `IService` and
    `KnowledgeGraph` implements the full initialize()/start()/stop()/
    status() lifecycle boilerplate - but none of the graph's own
    methods are gated on the RUNNING state, exactly mirroring
    IntentRouter's (Package 009) identical shape: an IService adopter
    whose own domain methods (parse()/route()/register_handler())
    are entirely unaffected by lifecycle state. This makes
    KnowledgeGraph the second such case in this codebase - see
    design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md's newly
    appended Empirical Finding for this package, which records this
    as the first case where an explicit Founder instruction to adopt
    IService does not align with what ADR-0002's own criterion would
    independently conclude. KnowledgeGraph is registered with the
    Lifecycle Manager as LifecycleState.REGISTERED only (never
    started) by bootstrap.py, exactly like every other core service -
    gated or not.

Responsibilities:
    - IKnowledgeGraph: add_entity / remove_entity / get_entity /
      list_entities / add_relationship / remove_relationship /
      list_relationships / neighbors / find_by_type, plus the
      inherited IService contract (initialize / start / stop /
      status).

Non-Responsibilities:
    - This module implements no behavior; see
      argus.knowledge_graph.graph.KnowledgeGraph.
    - IKnowledgeGraph does not perform vector search, execute Plans,
      call connectors, store files, perform persistence, or
      communicate externally - see this package's Objective and
      Constraints.

Dependencies:
    argus.knowledge_graph.entity (Entity),
    argus.knowledge_graph.relationship (Relationship),
    argus.lifecycle.interfaces (IService).
"""

from abc import abstractmethod
from typing import Sequence

from argus.knowledge_graph.entity import Entity
from argus.knowledge_graph.relationship import Relationship
from argus.lifecycle.interfaces import IService


class IKnowledgeGraph(IService):
    """
    Contract for the Knowledge Graph's registry-and-query service. See
    this module's docstring for why IKnowledgeGraph inherits IService
    despite none of its own methods being lifecycle-gated.
    """

    @abstractmethod
    def add_entity(self, entity: Entity) -> None:
        """Register a new Entity. Raises DuplicateEntityError if
        `entity.id` is already registered."""

    @abstractmethod
    def remove_entity(self, entity_id: str) -> None:
        """Remove a previously registered Entity, together with every
        Relationship that references it as source or target (see
        argus/knowledge_graph/graph.py's module docstring, Cascading
        Removal). Raises EntityNotFoundError if `entity_id` is
        unknown."""

    @abstractmethod
    def get_entity(self, entity_id: str) -> Entity:
        """Return the Entity registered under `entity_id`. Raises
        EntityNotFoundError if unknown."""

    @abstractmethod
    def list_entities(self) -> Sequence[Entity]:
        """Return every currently registered Entity."""

    @abstractmethod
    def add_relationship(self, relationship: Relationship) -> None:
        """Register a new Relationship. Raises
        DuplicateRelationshipError if `relationship.id` is already
        registered, and EntityNotFoundError if either
        `source_entity_id` or `target_entity_id` does not refer to a
        currently registered Entity."""

    @abstractmethod
    def remove_relationship(self, relationship_id: str) -> None:
        """Remove a previously registered Relationship. Raises
        RelationshipNotFoundError if `relationship_id` is unknown."""

    @abstractmethod
    def list_relationships(self) -> Sequence[Relationship]:
        """Return every currently registered Relationship."""

    @abstractmethod
    def neighbors(self, entity_id: str) -> Sequence[Entity]:
        """Return every distinct Entity connected to `entity_id` by
        at least one Relationship, in either direction. Raises
        EntityNotFoundError if `entity_id` is unknown."""

    @abstractmethod
    def find_by_type(self, entity_type: str) -> Sequence[Entity]:
        """Return every currently registered Entity whose
        `entity_type` equals the given value."""
