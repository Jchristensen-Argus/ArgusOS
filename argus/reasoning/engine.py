"""
ReasoningEngine: deterministic, read-only implementation of
IReasoningEngine for the ArgusOS Reasoning Engine.

Purpose:
    Implement IReasoningEngine: query the Knowledge Graph - by entity
    id (with bounded outward traversal), by entity type, by
    relationship type, or by entity type and relationship type
    together (a simple graph pattern) - find direct neighbors, find
    bounded simple paths between two entities, and produce
    count-based, descriptive summaries, per
    factory/packages/020_REASONING_ENGINE.md. "It does not make
    decisions. It does not execute plans. It performs deterministic
    reasoning only." The Reasoning Engine never mutates the Knowledge
    Graph or the Memory Service - every call it makes to either
    injected dependency is one of that dependency's own read-only,
    already-established query methods.

Architectural Decision - Genuine Use of the Injected
IMemoryIntegration:
    This package's own Objective states the Reasoning Engine
    "consumes information from the Knowledge Graph and Memory
    Integration to produce structured reasoning results," and its
    Bootstrap section explicitly lists both as dependencies - stronger
    language than Package 018's "the Planner *may* consult the
    Knowledge Graph" (a future capability, deliberately left
    unexercised in that package). Every public method of this class
    therefore genuinely calls the injected IMemoryIntegration, not
    merely holds a reference to it: each attaches
    IMemoryIntegration.synchronization_status()'s own snapshot
    (already ungated, purely a read of MemoryIntegration's internal
    bookkeeping - see
    argus/memory_integration/integration.py's "It owns no data
    itself") to that call's ReasoningResult.metadata, under the key
    "memory_synchronization_status". This deliberately does NOT
    attempt to correlate individual graph Entities back to specific
    memory keys: MemoryMapper's `f"memory:{key}"` id scheme (argus/
    memory_integration/mapper.py) is that package's own private
    implementation detail, not a documented part of IMemoryIntegration's
    or IKnowledgeGraph's public contract, and reaching into it here
    would create a hidden, fragile coupling this package's own
    "does not perform graph reasoning [or] inference" boundary (that
    boundary belongs to Memory Integration, per Package 019) should
    not create. Attaching the bridge's own whole-system status
    snapshot as plain, factual, descriptive metadata is the most
    restrained interpretation of "consumes information from ...
    Memory Integration" available without inventing new, unspecified
    architecture.

Traversal Semantics:
    query()'s entity_id branch and find_paths() both treat every
    Relationship as traversable in either direction - matching
    IKnowledgeGraph.neighbors()'s own established "connected ... in
    either direction" precedent (Package 018) - and both are bounded
    by an explicit depth/max_depth parameter, making every traversal
    a finite, deterministic, exhaustive enumeration (breadth-first
    reachability for query(); depth-first simple-path enumeration for
    find_paths()) rather than a heuristic search. Package 018's own
    "No graph algorithms yet... only foundational graph operations"
    was a deliberate deferral, not a permanent prohibition - "yet"
    - and this package, per its own explicit find_paths() method and
    "evaluate simple graph patterns" responsibility, is that deferred
    future package for bounded, deterministic multi-hop traversal.
    Nothing here is a heuristic algorithm or machine learning - see
    this package's own Constraints.

Responsibilities:
    - ReasoningEngine: the sole implementation of IReasoningEngine.

Non-Responsibilities:
    - ReasoningEngine never calls any IKnowledgeGraph or
      IMemoryIntegration method that could mutate either system - see
      this package's Objective and Constraints ("shall NOT... modify
      the graph... modify memory").
    - ReasoningEngine never invokes an LLM, performs probabilistic
      reasoning, executes actions, or communicates externally.

Dependencies:
    argus.events (Event, EventType, IEventBus), argus.knowledge_graph
    (Entity, IKnowledgeGraph, its exceptions), argus.lifecycle.lifecycle
    (LifecycleState), argus.memory_integration.interfaces
    (IMemoryIntegration), argus.reasoning.exceptions,
    argus.reasoning.interfaces (IReasoningEngine), argus.reasoning.query
    (ReasoningQuery), argus.reasoning.result (ReasoningResult).
"""

from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Set, Tuple

from argus.events.event import Event
from argus.events.event_types import EventType
from argus.events.interfaces import IEventBus
from argus.knowledge_graph.entity import Entity
from argus.knowledge_graph.exceptions import EntityNotFoundError
from argus.knowledge_graph.interfaces import IKnowledgeGraph
from argus.knowledge_graph.relationship import Relationship
from argus.lifecycle.lifecycle import LifecycleState
from argus.memory_integration.interfaces import IMemoryIntegration
from argus.reasoning.exceptions import (
    InvalidReasoningQueryError,
    ReasoningError,
    ReasoningTargetNotFoundError,
)
from argus.reasoning.interfaces import IReasoningEngine
from argus.reasoning.query import ReasoningQuery
from argus.reasoning.result import ReasoningResult


class ReasoningEngine(IReasoningEngine):
    """
    Deterministic, read-only implementation of IReasoningEngine.

    Purpose:
        Answer structural queries against an injected IKnowledgeGraph,
        enriching results with an injected IMemoryIntegration's own
        synchronization status snapshot. See the module docstring for
        the full design rationale.

    Dependencies:
        An IKnowledgeGraph, an IMemoryIntegration, and an IEventBus,
        all injected by the caller (bootstrap.py).
    """

    def __init__(
        self,
        knowledge_graph: IKnowledgeGraph,
        memory_integration: IMemoryIntegration,
        event_bus: IEventBus,
    ) -> None:
        self._knowledge_graph = knowledge_graph
        self._memory_integration = memory_integration
        self._event_bus = event_bus
        self._state: LifecycleState = LifecycleState.CREATED

    # -- IService (see interfaces.py's Architectural Note: adopted per
    #    explicit instruction; no method below is gated on RUNNING) --

    def initialize(self) -> None:
        if self._state != LifecycleState.CREATED:
            raise ReasoningError(
                f"Cannot initialize: ReasoningEngine is {self._state.name}, expected CREATED."
            )
        self._state = LifecycleState.INITIALIZING

    def start(self) -> None:
        if self._state != LifecycleState.INITIALIZING:
            raise ReasoningError(
                f"Cannot start: ReasoningEngine is {self._state.name}, expected INITIALIZING."
            )
        self._state = LifecycleState.RUNNING

    def stop(self) -> None:
        if self._state != LifecycleState.RUNNING:
            raise ReasoningError(
                f"Cannot stop: ReasoningEngine is {self._state.name}, expected RUNNING."
            )
        self._state = LifecycleState.STOPPING
        self._state = LifecycleState.STOPPED

    def status(self) -> LifecycleState:
        return self._state

    # -- IReasoningEngine ---------------------------------------------

    def query(self, reasoning_query: ReasoningQuery) -> ReasoningResult:
        payload = {
            "entity_id": getattr(reasoning_query, "entity_id", None),
            "entity_type": getattr(reasoning_query, "entity_type", None),
            "relationship_type": getattr(reasoning_query, "relationship_type", None),
        }
        return self._execute("query", payload, lambda: self._do_query(reasoning_query))

    def neighbors(self, entity_id: str) -> ReasoningResult:
        payload = {"entity_id": entity_id}
        return self._execute("neighbors", payload, lambda: self._do_neighbors(entity_id))

    def find_paths(
        self, source_entity_id: str, target_entity_id: str, *, max_depth: int = 3
    ) -> ReasoningResult:
        payload = {
            "source_entity_id": source_entity_id,
            "target_entity_id": target_entity_id,
            "max_depth": max_depth,
        }
        return self._execute(
            "find_paths",
            payload,
            lambda: self._do_find_paths(source_entity_id, target_entity_id, max_depth),
        )

    def related_entities(
        self, entity_id: str, *, relationship_type: Optional[str] = None
    ) -> ReasoningResult:
        payload = {"entity_id": entity_id, "relationship_type": relationship_type}
        return self._execute(
            "related_entities",
            payload,
            lambda: self._do_related_entities(entity_id, relationship_type),
        )

    def entity_summary(self, entity_id: str) -> ReasoningResult:
        payload = {"entity_id": entity_id}
        return self._execute(
            "entity_summary", payload, lambda: self._do_entity_summary(entity_id)
        )

    def relationship_summary(self, relationship_type: str) -> ReasoningResult:
        payload = {"relationship_type": relationship_type}
        return self._execute(
            "relationship_summary",
            payload,
            lambda: self._do_relationship_summary(relationship_type),
        )

    # -- query() branch implementation ---------------------------------

    def _do_query(self, reasoning_query: ReasoningQuery) -> ReasoningResult:
        if not isinstance(reasoning_query, ReasoningQuery):
            raise InvalidReasoningQueryError(
                f"query() requires a ReasoningQuery, got {reasoning_query!r}."
            )
        if (
            reasoning_query.entity_id is None
            and reasoning_query.entity_type is None
            and reasoning_query.relationship_type is None
        ):
            raise InvalidReasoningQueryError(
                "ReasoningQuery must set at least one of entity_id, entity_type, "
                "or relationship_type."
            )
        self._require_positive_int(reasoning_query.depth, "depth")

        if reasoning_query.entity_id is not None:
            return self._query_by_entity_id(reasoning_query)
        if reasoning_query.entity_type is not None and reasoning_query.relationship_type is not None:
            return self._query_by_pattern(reasoning_query)
        if reasoning_query.entity_type is not None:
            return self._query_by_entity_type(reasoning_query)
        return self._query_by_relationship_type(reasoning_query)

    def _query_by_entity_id(self, reasoning_query: ReasoningQuery) -> ReasoningResult:
        entity_id = reasoning_query.entity_id
        self._require_entity(entity_id)

        visited_ids, steps = self._bfs_reachable(
            entity_id, reasoning_query.depth, reasoning_query.relationship_type
        )
        matched_entities = tuple(self._knowledge_graph.get_entity(eid) for eid in visited_ids)
        matched_relationships = self._induced_relationships(
            visited_ids, reasoning_query.relationship_type
        )

        if reasoning_query.entity_type is not None:
            matched_entities = tuple(
                e for e in matched_entities if e.entity_type == reasoning_query.entity_type
            )
            steps.append(
                f"filtered to entity_type={reasoning_query.entity_type!r}: "
                f"{len(matched_entities)} remain"
            )

        if reasoning_query.filters:
            matched_entities = tuple(
                e for e in matched_entities if self._matches_filters(e.attributes, reasoning_query.filters)
            )
            steps.append(f"applied filters: {len(matched_entities)} entities remain")

        metadata = {
            "branch": "entity_id",
            "entity_id": entity_id,
            "depth": reasoning_query.depth,
            "matched_entity_count": len(matched_entities),
            "matched_relationship_count": len(matched_relationships),
        }
        metadata.update(self._memory_sync_metadata())
        return ReasoningResult(
            matched_entities=matched_entities,
            matched_relationships=matched_relationships,
            reasoning_steps=tuple(steps),
            metadata=metadata,
        )

    def _query_by_entity_type(self, reasoning_query: ReasoningQuery) -> ReasoningResult:
        matched_entities = self._knowledge_graph.find_by_type(reasoning_query.entity_type)
        steps = [
            f"searched entities by entity_type={reasoning_query.entity_type!r}: "
            f"found {len(matched_entities)}"
        ]
        if reasoning_query.filters:
            matched_entities = tuple(
                e for e in matched_entities if self._matches_filters(e.attributes, reasoning_query.filters)
            )
            steps.append(f"applied filters: {len(matched_entities)} entities remain")

        metadata = {
            "branch": "entity_type",
            "entity_type": reasoning_query.entity_type,
            "matched_entity_count": len(matched_entities),
            "matched_relationship_count": 0,
        }
        metadata.update(self._memory_sync_metadata())
        return ReasoningResult(
            matched_entities=matched_entities,
            matched_relationships=(),
            reasoning_steps=tuple(steps),
            metadata=metadata,
        )

    def _query_by_relationship_type(self, reasoning_query: ReasoningQuery) -> ReasoningResult:
        matched_relationships = tuple(
            r
            for r in self._knowledge_graph.list_relationships()
            if r.relationship_type == reasoning_query.relationship_type
        )
        steps = [
            f"searched relationships by relationship_type="
            f"{reasoning_query.relationship_type!r}: found {len(matched_relationships)}"
        ]
        if reasoning_query.filters:
            matched_relationships = tuple(
                r
                for r in matched_relationships
                if self._matches_filters(r.attributes, reasoning_query.filters)
            )
            steps.append(f"applied filters: {len(matched_relationships)} relationships remain")

        metadata = {
            "branch": "relationship_type",
            "relationship_type": reasoning_query.relationship_type,
            "matched_entity_count": 0,
            "matched_relationship_count": len(matched_relationships),
        }
        metadata.update(self._memory_sync_metadata())
        return ReasoningResult(
            matched_entities=(),
            matched_relationships=matched_relationships,
            reasoning_steps=tuple(steps),
            metadata=metadata,
        )

    def _query_by_pattern(self, reasoning_query: ReasoningQuery) -> ReasoningResult:
        candidate_relationships = tuple(
            r
            for r in self._knowledge_graph.list_relationships()
            if r.relationship_type == reasoning_query.relationship_type
        )
        steps = [
            f"evaluated pattern entity_type={reasoning_query.entity_type!r} + "
            f"relationship_type={reasoning_query.relationship_type!r}: "
            f"{len(candidate_relationships)} relationships of that type"
        ]

        matched_relationships = []
        matched_entity_ids: List[str] = []
        for r in candidate_relationships:
            source = self._knowledge_graph.get_entity(r.source_entity_id)
            target = self._knowledge_graph.get_entity(r.target_entity_id)
            touched = False
            if source.entity_type == reasoning_query.entity_type:
                if source.id not in matched_entity_ids:
                    matched_entity_ids.append(source.id)
                touched = True
            if target.entity_type == reasoning_query.entity_type:
                if target.id not in matched_entity_ids:
                    matched_entity_ids.append(target.id)
                touched = True
            if touched:
                matched_relationships.append(r)

        matched_relationships = tuple(matched_relationships)
        if reasoning_query.filters:
            matched_relationships = tuple(
                r
                for r in matched_relationships
                if self._matches_filters(r.attributes, reasoning_query.filters)
            )
            kept_ids = set()
            for r in matched_relationships:
                kept_ids.add(r.source_entity_id)
                kept_ids.add(r.target_entity_id)
            matched_entity_ids = [eid for eid in matched_entity_ids if eid in kept_ids]
            steps.append(f"applied filters: {len(matched_relationships)} relationships remain")

        matched_entities = tuple(self._knowledge_graph.get_entity(eid) for eid in matched_entity_ids)
        steps.append(
            f"pattern matched {len(matched_relationships)} relationships and "
            f"{len(matched_entities)} entities of the requested type"
        )

        metadata = {
            "branch": "pattern",
            "entity_type": reasoning_query.entity_type,
            "relationship_type": reasoning_query.relationship_type,
            "matched_entity_count": len(matched_entities),
            "matched_relationship_count": len(matched_relationships),
        }
        metadata.update(self._memory_sync_metadata())
        return ReasoningResult(
            matched_entities=matched_entities,
            matched_relationships=matched_relationships,
            reasoning_steps=tuple(steps),
            metadata=metadata,
        )

    # -- other public methods' implementations -------------------------

    def _do_neighbors(self, entity_id: str) -> ReasoningResult:
        self._require_non_empty_string(entity_id, "entity_id")
        self._require_entity(entity_id)

        neighbor_entities, touching = self._direct_neighbor_entities(entity_id)
        steps = [
            f"resolved entity {entity_id!r}",
            f"found {len(neighbor_entities)} direct neighbors via {len(touching)} relationships",
        ]
        metadata = {
            "entity_id": entity_id,
            "neighbor_count": len(neighbor_entities),
            "relationship_count": len(touching),
        }
        metadata.update(self._memory_sync_metadata())
        return ReasoningResult(
            matched_entities=neighbor_entities,
            matched_relationships=touching,
            reasoning_steps=tuple(steps),
            metadata=metadata,
        )

    def _do_related_entities(
        self, entity_id: str, relationship_type: Optional[str]
    ) -> ReasoningResult:
        self._require_non_empty_string(entity_id, "entity_id")
        if relationship_type is not None:
            self._require_non_empty_string(relationship_type, "relationship_type")
        self._require_entity(entity_id)

        neighbor_entities, touching = self._direct_neighbor_entities(entity_id, relationship_type)
        steps = [
            f"resolved entity {entity_id!r}",
            f"found {len(neighbor_entities)} related entities "
            f"(relationship_type={relationship_type!r}) via {len(touching)} relationships",
        ]
        metadata = {
            "entity_id": entity_id,
            "relationship_type": relationship_type,
            "neighbor_count": len(neighbor_entities),
            "relationship_count": len(touching),
        }
        metadata.update(self._memory_sync_metadata())
        return ReasoningResult(
            matched_entities=neighbor_entities,
            matched_relationships=touching,
            reasoning_steps=tuple(steps),
            metadata=metadata,
        )

    def _do_entity_summary(self, entity_id: str) -> ReasoningResult:
        self._require_non_empty_string(entity_id, "entity_id")
        root = self._require_entity(entity_id)

        touching = self._relationships_touching(entity_id)
        outgoing = tuple(r for r in touching if r.source_entity_id == entity_id)
        incoming = tuple(r for r in touching if r.target_entity_id == entity_id)
        neighbor_ids: List[str] = []
        for r in touching:
            other_id = self._other_endpoint(r, entity_id)
            if other_id not in neighbor_ids:
                neighbor_ids.append(other_id)

        steps = [
            f"resolved entity {entity_id!r}",
            f"computed summary: {len(outgoing)} outgoing, {len(incoming)} incoming, "
            f"{len(neighbor_ids)} distinct neighbors",
        ]
        metadata = {
            "entity_id": entity_id,
            "entity_type": root.entity_type,
            "outgoing_count": len(outgoing),
            "incoming_count": len(incoming),
            "neighbor_count": len(neighbor_ids),
        }
        metadata.update(self._memory_sync_metadata())
        return ReasoningResult(
            matched_entities=(root,),
            matched_relationships=touching,
            reasoning_steps=tuple(steps),
            metadata=metadata,
        )

    def _do_relationship_summary(self, relationship_type: str) -> ReasoningResult:
        self._require_non_empty_string(relationship_type, "relationship_type")

        matched_relationships = tuple(
            r
            for r in self._knowledge_graph.list_relationships()
            if r.relationship_type == relationship_type
        )
        entity_ids: List[str] = []
        for r in matched_relationships:
            for eid in (r.source_entity_id, r.target_entity_id):
                if eid not in entity_ids:
                    entity_ids.append(eid)
        matched_entities = tuple(self._knowledge_graph.get_entity(eid) for eid in entity_ids)

        steps = [
            f"searched relationships by relationship_type={relationship_type!r}: "
            f"found {len(matched_relationships)}",
            f"found {len(matched_entities)} distinct endpoint entities",
        ]
        metadata = {
            "relationship_type": relationship_type,
            "relationship_count": len(matched_relationships),
            "distinct_entity_count": len(matched_entities),
        }
        metadata.update(self._memory_sync_metadata())
        return ReasoningResult(
            matched_entities=matched_entities,
            matched_relationships=matched_relationships,
            reasoning_steps=tuple(steps),
            metadata=metadata,
        )

    def _do_find_paths(
        self, source_entity_id: str, target_entity_id: str, max_depth: int
    ) -> ReasoningResult:
        self._require_non_empty_string(source_entity_id, "source_entity_id")
        self._require_non_empty_string(target_entity_id, "target_entity_id")
        self._require_positive_int(max_depth, "max_depth")
        self._require_entity(source_entity_id)
        self._require_entity(target_entity_id)

        steps = [
            f"resolved source entity {source_entity_id!r}",
            f"resolved target entity {target_entity_id!r}",
        ]

        if source_entity_id == target_entity_id:
            paths: Tuple[Tuple[str, ...], ...] = ((source_entity_id,),)
            steps.append("source and target are the same entity; trivial path of length 0")
            matched_entities = (self._knowledge_graph.get_entity(source_entity_id),)
            matched_relationships: Tuple[Relationship, ...] = ()
        else:
            raw_paths = self._enumerate_simple_paths(source_entity_id, target_entity_id, max_depth)
            steps.append(f"found {len(raw_paths)} path(s) within max_depth={max_depth}")

            paths = tuple(tuple(entity_ids) for entity_ids, _ in raw_paths)

            entity_id_order: List[str] = []
            relationship_id_order: List[str] = []
            for entity_ids, relationship_ids in raw_paths:
                for eid in entity_ids:
                    if eid not in entity_id_order:
                        entity_id_order.append(eid)
                for rid in relationship_ids:
                    if rid not in relationship_id_order:
                        relationship_id_order.append(rid)

            relationship_lookup = {r.id: r for r in self._knowledge_graph.list_relationships()}
            matched_entities = tuple(
                self._knowledge_graph.get_entity(eid) for eid in entity_id_order
            )
            matched_relationships = tuple(
                relationship_lookup[rid] for rid in relationship_id_order
            )

        metadata = {
            "source_entity_id": source_entity_id,
            "target_entity_id": target_entity_id,
            "max_depth": max_depth,
            "paths": paths,
            "path_count": len(paths),
        }
        metadata.update(self._memory_sync_metadata())
        return ReasoningResult(
            matched_entities=matched_entities,
            matched_relationships=matched_relationships,
            reasoning_steps=tuple(steps),
            metadata=metadata,
        )

    # -- traversal helpers ----------------------------------------------

    def _bfs_reachable(
        self, root_id: str, depth: int, relationship_type: Optional[str]
    ) -> Tuple[List[str], List[str]]:
        """
        Breadth-first reachability from `root_id`, up to `depth` hops,
        optionally restricted to Relationships of `relationship_type`.
        Returns (visited entity ids in discovery order, human-readable
        step descriptions).
        """
        visited_order = [root_id]
        visited: Set[str] = {root_id}
        frontier = [root_id]
        steps = [f"resolved root entity {root_id!r}"]

        for hop in range(1, depth + 1):
            frontier_set = set(frontier)
            candidate_relationships = [
                r
                for r in self._knowledge_graph.list_relationships()
                if (relationship_type is None or r.relationship_type == relationship_type)
                and (r.source_entity_id in frontier_set or r.target_entity_id in frontier_set)
            ]
            new_ids: List[str] = []
            for r in candidate_relationships:
                for candidate_id in (r.source_entity_id, r.target_entity_id):
                    if candidate_id not in visited and candidate_id not in new_ids:
                        new_ids.append(candidate_id)

            steps.append(
                f"hop {hop}: discovered {len(new_ids)} new entities via "
                f"{len(candidate_relationships)} relationships"
            )
            for nid in new_ids:
                visited.add(nid)
                visited_order.append(nid)
            frontier = new_ids
            if not frontier:
                break

        return visited_order, steps

    def _induced_relationships(
        self, visited_ids: Sequence[str], relationship_type: Optional[str]
    ) -> Tuple[Relationship, ...]:
        visited_set = set(visited_ids)
        return tuple(
            r
            for r in self._knowledge_graph.list_relationships()
            if (relationship_type is None or r.relationship_type == relationship_type)
            and r.source_entity_id in visited_set
            and r.target_entity_id in visited_set
        )

    def _enumerate_simple_paths(
        self, source_id: str, target_id: str, max_depth: int
    ) -> List[Tuple[List[str], List[str]]]:
        results: List[Tuple[List[str], List[str]]] = []

        def dfs(current_id: str, path_ids: List[str], path_relationship_ids: List[str], visited: Set[str]) -> None:
            if len(path_relationship_ids) >= max_depth:
                return
            for r in self._relationships_touching(current_id):
                other_id = self._other_endpoint(r, current_id)
                if other_id in visited:
                    continue
                new_path_ids = path_ids + [other_id]
                new_path_relationship_ids = path_relationship_ids + [r.id]
                if other_id == target_id:
                    results.append((new_path_ids, new_path_relationship_ids))
                else:
                    dfs(other_id, new_path_ids, new_path_relationship_ids, visited | {other_id})

        dfs(source_id, [source_id], [], {source_id})
        return results

    def _relationships_touching(
        self, entity_id: str, relationship_type: Optional[str] = None
    ) -> Tuple[Relationship, ...]:
        return tuple(
            r
            for r in self._knowledge_graph.list_relationships()
            if (r.source_entity_id == entity_id or r.target_entity_id == entity_id)
            and (relationship_type is None or r.relationship_type == relationship_type)
        )

    def _direct_neighbor_entities(
        self, entity_id: str, relationship_type: Optional[str] = None
    ) -> Tuple[Tuple[Entity, ...], Tuple[Relationship, ...]]:
        touching = self._relationships_touching(entity_id, relationship_type)
        neighbor_ids: List[str] = []
        for r in touching:
            other_id = self._other_endpoint(r, entity_id)
            if other_id not in neighbor_ids:
                neighbor_ids.append(other_id)
        neighbor_entities = tuple(self._knowledge_graph.get_entity(nid) for nid in neighbor_ids)
        return neighbor_entities, touching

    @staticmethod
    def _other_endpoint(relationship: Relationship, entity_id: str) -> str:
        """
        Returns the endpoint of `relationship` other than `entity_id`.
        Every call site passes a relationship already known to touch
        `entity_id` (filtered through _relationships_touching()) -
        mirroring KnowledgeGraph.neighbors()'s own identical "every
        relationship passed in is guaranteed to touch the given
        entity_id" invariant (see argus/knowledge_graph/graph.py's
        own neighbors() docstring and its "redundant defensive
        filter" simplification from Package 018) - so no defensive
        "doesn't touch entity_id at all" branch is needed here
        either.
        """
        if relationship.source_entity_id == entity_id:
            return relationship.target_entity_id
        return relationship.source_entity_id

    @staticmethod
    def _matches_filters(attributes: Mapping[str, Any], filters: Mapping[str, Any]) -> bool:
        return all(key in attributes and attributes[key] == value for key, value in filters.items())

    def _memory_sync_metadata(self) -> Dict[str, Any]:
        return {"memory_synchronization_status": self._memory_integration.synchronization_status()}

    # -- validation / lookup helpers -------------------------------------

    def _require_entity(self, entity_id: str) -> Entity:
        self._require_non_empty_string(entity_id, "entity_id")
        try:
            return self._knowledge_graph.get_entity(entity_id)
        except EntityNotFoundError as error:
            raise ReasoningTargetNotFoundError(
                f"No entity registered under {entity_id!r}."
            ) from error

    @staticmethod
    def _require_non_empty_string(value: Any, name: str) -> None:
        if not isinstance(value, str) or not value:
            raise InvalidReasoningQueryError(f"{name} must be a non-empty string.")

    @staticmethod
    def _require_positive_int(value: Any, name: str) -> None:
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise InvalidReasoningQueryError(f"{name} must be a positive integer.")

    # -- event publication / execution wrapper ---------------------------

    def _execute(
        self,
        operation: str,
        base_payload: Mapping[str, Any],
        work: Callable[[], ReasoningResult],
    ) -> ReasoningResult:
        """
        Run `work()` (one public method's actual logic), publishing
        REASONING_QUERY_FAILED if it raises a ReasoningError, or
        REASONING_QUERY_EXECUTED followed by REASONING_RESULT_CREATED
        if it succeeds - mutually exclusive outcomes for a single
        call, matching CONNECTOR_INVOKED/CONNECTOR_FAILED's (Package
        017) precedent, extended to three events only because this
        package's own Events section names three: EXECUTED marks that
        the underlying read-only Knowledge Graph / Memory Integration
        calls completed; RESULT_CREATED marks that a structured
        ReasoningResult was subsequently assembled from them - see
        this module's own docstring.
        """
        try:
            result = work()
        except ReasoningError as error:
            self._publish(
                EventType.REASONING_QUERY_FAILED,
                {**base_payload, "operation": operation, "reason": str(error)},
            )
            raise

        self._publish(EventType.REASONING_QUERY_EXECUTED, {**base_payload, "operation": operation})
        self._publish(
            EventType.REASONING_RESULT_CREATED,
            {
                **base_payload,
                "operation": operation,
                "matched_entity_count": len(result.matched_entities),
                "matched_relationship_count": len(result.matched_relationships),
            },
        )
        return result

    def _publish(self, event_type: EventType, payload: dict) -> None:
        self._event_bus.publish(
            Event(type=event_type, source="reasoning_engine", payload=payload)
        )
