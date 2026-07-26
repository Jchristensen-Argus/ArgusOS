"""Unit tests for argus.reasoning.engine.ReasoningEngine."""

import logging
import unittest
from typing import Sequence

from argus.events import EventType, InMemoryEventBus
from argus.knowledge_graph import Entity, KnowledgeGraph, Relationship
from argus.lifecycle import LifecycleState
from argus.memory import MemoryRecord, MemoryService
from argus.memory.interfaces import IMemoryStorage
from argus.memory_integration import MemoryIntegration
from argus.reasoning import ReasoningEngine, ReasoningQuery
from argus.reasoning.exceptions import (
    InvalidReasoningQueryError,
    ReasoningError,
    ReasoningTargetNotFoundError,
)


def _silent_logger() -> logging.Logger:
    logger = logging.getLogger("test_reasoning_engine")
    logger.addHandler(logging.NullHandler())
    logger.propagate = False
    return logger


class _InMemoryStorage(IMemoryStorage):
    """A minimal, fully in-memory IMemoryStorage stand-in - no disk
    I/O of any kind - matching argus/tests/test_memory_integration.py's
    own precedent, used only so MemoryIntegration (a required
    ReasoningEngine dependency) never touches memory_store.json."""

    def __init__(self):
        self._records = []

    def load(self) -> Sequence[MemoryRecord]:
        return tuple(self._records)

    def save(self, records: Sequence[MemoryRecord]) -> None:
        self._records = list(records)


class ReasoningEngineTestCase(unittest.TestCase):
    """
    Base fixture: a small, fixed graph -

        alice --knows--> bob --works_at--> acme
        alice --works_at--> acme
        alice --works_at--> acme   (a second, parallel relationship)
        alice --self_ref--> alice  (a self-loop)
        carol                       (isolated - no relationships)

    - reused by every test below. `dana` exists only in some tests
    that need a second isolated/unreachable entity.
    """

    def setUp(self):
        self.event_bus = InMemoryEventBus(logger=_silent_logger())
        self.graph = KnowledgeGraph(event_bus=self.event_bus)
        self.memory_service = MemoryService(storage=_InMemoryStorage(), event_bus=self.event_bus)
        self.memory_integration = MemoryIntegration(
            memory_service=self.memory_service,
            knowledge_graph=self.graph,
            event_bus=self.event_bus,
        )
        self.engine = ReasoningEngine(
            knowledge_graph=self.graph,
            memory_integration=self.memory_integration,
            event_bus=self.event_bus,
        )

        self.alice = Entity(
            entity_type="person", name="Alice", id="alice", attributes={"age": 30, "active": True}
        )
        self.bob = Entity(
            entity_type="person", name="Bob", id="bob", attributes={"age": 25, "active": False}
        )
        self.acme = Entity(entity_type="org", name="Acme", id="acme", attributes={"industry": "tech"})
        self.carol = Entity(entity_type="person", name="Carol", id="carol", attributes={"age": 40})
        for entity in (self.alice, self.bob, self.acme, self.carol):
            self.graph.add_entity(entity)

        self.r_knows = Relationship(
            source_entity_id="alice", target_entity_id="bob", relationship_type="knows", id="r-knows"
        )
        self.r_works_bob = Relationship(
            source_entity_id="bob",
            target_entity_id="acme",
            relationship_type="works_at",
            id="r-works-bob",
            attributes={"role": "engineer"},
        )
        self.r_works_alice = Relationship(
            source_entity_id="alice",
            target_entity_id="acme",
            relationship_type="works_at",
            id="r-works-alice",
            attributes={"role": "manager"},
        )
        self.r_works_alice_2 = Relationship(
            source_entity_id="alice",
            target_entity_id="acme",
            relationship_type="works_at",
            id="r-works-alice-2",
            attributes={"role": "advisor"},
        )
        self.r_self = Relationship(
            source_entity_id="alice", target_entity_id="alice", relationship_type="self_ref", id="r-self"
        )
        for relationship in (
            self.r_knows,
            self.r_works_bob,
            self.r_works_alice,
            self.r_works_alice_2,
            self.r_self,
        ):
            self.graph.add_relationship(relationship)

    def _events(self, *event_types):
        received = []
        for event_type in event_types:
            self.event_bus.subscribe(event_type, received.append)
        return received


# -- Lifecycle -------------------------------------------------------------


class LifecycleTests(ReasoningEngineTestCase):
    def test_initial_state_is_created(self):
        self.assertEqual(self.engine.status(), LifecycleState.CREATED)

    def test_initialize_start_stop_transitions(self):
        self.engine.initialize()
        self.assertEqual(self.engine.status(), LifecycleState.INITIALIZING)
        self.engine.start()
        self.assertEqual(self.engine.status(), LifecycleState.RUNNING)
        self.engine.stop()
        self.assertEqual(self.engine.status(), LifecycleState.STOPPED)

    def test_initialize_twice_raises(self):
        self.engine.initialize()
        with self.assertRaises(ReasoningError):
            self.engine.initialize()

    def test_start_before_initialize_raises(self):
        with self.assertRaises(ReasoningError):
            self.engine.start()

    def test_stop_before_start_raises(self):
        self.engine.initialize()
        with self.assertRaises(ReasoningError):
            self.engine.stop()

    def test_public_methods_work_without_starting(self):
        # None of ReasoningEngine's six public methods are gated on
        # RUNNING - see interfaces.py's Architectural Note.
        self.assertEqual(self.engine.status(), LifecycleState.CREATED)
        result = self.engine.neighbors("alice")
        self.assertIn(self.bob, result.matched_entities)


# -- query(): entity_id branch ----------------------------------------------


class QueryByEntityIdTests(ReasoningEngineTestCase):
    def test_depth_1_direct_neighbors_only(self):
        result = self.engine.query(ReasoningQuery(entity_id="alice", depth=1))
        ids = {e.id for e in result.matched_entities}
        self.assertEqual(ids, {"alice", "bob", "acme"})

    def test_depth_2_reaches_further(self):
        result = self.engine.query(ReasoningQuery(entity_id="acme", depth=2))
        ids = {e.id for e in result.matched_entities}
        # acme -> bob (hop1), acme -> alice (hop1, direct), bob -> alice (hop2, already visited)
        self.assertEqual(ids, {"acme", "bob", "alice"})

    def test_depth_exceeding_graph_size_breaks_early(self):
        # carol is isolated; alice's whole reachable component is
        # exhausted well before depth=10 - covers the BFS's own
        # "if not frontier: break" early-exit branch.
        result = self.engine.query(ReasoningQuery(entity_id="alice", depth=10))
        ids = {e.id for e in result.matched_entities}
        self.assertEqual(ids, {"alice", "bob", "acme"})
        self.assertNotIn("carol", ids)

    def test_relationship_type_filter_restricts_traversal(self):
        # At depth=1, only works_at-typed edges from alice are
        # followed - "knows" (to bob) is excluded.
        result = self.engine.query(
            ReasoningQuery(entity_id="alice", depth=1, relationship_type="works_at")
        )
        ids = {e.id for e in result.matched_entities}
        self.assertEqual(ids, {"alice", "acme"})

    def test_relationship_type_filter_can_reach_further_entities(self):
        # At depth=2, bob is legitimately reachable via works_at alone
        # (bob --works_at--> acme, acme already in the depth-1
        # frontier) - the filter restricts *which edges* are
        # followed, not how far traversal can reach.
        result = self.engine.query(
            ReasoningQuery(entity_id="alice", depth=2, relationship_type="works_at")
        )
        ids = {e.id for e in result.matched_entities}
        self.assertEqual(ids, {"alice", "acme", "bob"})

    def test_entity_type_filter_applied_after_traversal(self):
        result = self.engine.query(
            ReasoningQuery(entity_id="alice", depth=2, entity_type="org")
        )
        ids = {e.id for e in result.matched_entities}
        self.assertEqual(ids, {"acme"})

    def test_filters_applied_after_traversal(self):
        result = self.engine.query(
            ReasoningQuery(entity_id="alice", depth=1, filters={"active": False})
        )
        ids = {e.id for e in result.matched_entities}
        self.assertEqual(ids, {"bob"})

    def test_matched_relationships_are_induced_subgraph(self):
        result = self.engine.query(ReasoningQuery(entity_id="alice", depth=2))
        relationship_ids = {r.id for r in result.matched_relationships}
        self.assertEqual(
            relationship_ids,
            {"r-knows", "r-works-bob", "r-works-alice", "r-works-alice-2", "r-self"},
        )

    def test_unknown_entity_id_raises(self):
        with self.assertRaises(ReasoningTargetNotFoundError):
            self.engine.query(ReasoningQuery(entity_id="nonexistent"))

    def test_self_loop_appears_once(self):
        result = self.engine.query(ReasoningQuery(entity_id="alice", depth=1))
        alice_count = sum(1 for e in result.matched_entities if e.id == "alice")
        self.assertEqual(alice_count, 1)


# -- query(): entity_type branch ---------------------------------------------


class QueryByEntityTypeTests(ReasoningEngineTestCase):
    def test_finds_all_entities_of_type(self):
        result = self.engine.query(ReasoningQuery(entity_type="person"))
        ids = {e.id for e in result.matched_entities}
        self.assertEqual(ids, {"alice", "bob", "carol"})
        self.assertEqual(result.matched_relationships, ())

    def test_filters_restrict_matches(self):
        result = self.engine.query(ReasoningQuery(entity_type="person", filters={"active": True}))
        ids = {e.id for e in result.matched_entities}
        self.assertEqual(ids, {"alice"})

    def test_no_matches_for_unknown_type(self):
        result = self.engine.query(ReasoningQuery(entity_type="vehicle"))
        self.assertEqual(result.matched_entities, ())


# -- query(): relationship_type branch ---------------------------------------


class QueryByRelationshipTypeTests(ReasoningEngineTestCase):
    def test_finds_all_relationships_of_type(self):
        result = self.engine.query(ReasoningQuery(relationship_type="works_at"))
        ids = {r.id for r in result.matched_relationships}
        self.assertEqual(ids, {"r-works-bob", "r-works-alice", "r-works-alice-2"})
        self.assertEqual(result.matched_entities, ())

    def test_filters_restrict_matches(self):
        result = self.engine.query(
            ReasoningQuery(relationship_type="works_at", filters={"role": "engineer"})
        )
        ids = {r.id for r in result.matched_relationships}
        self.assertEqual(ids, {"r-works-bob"})

    def test_no_matches_for_unknown_type(self):
        result = self.engine.query(ReasoningQuery(relationship_type="married_to"))
        self.assertEqual(result.matched_relationships, ())


# -- query(): combined entity_type + relationship_type (pattern) branch -----


class QueryPatternTests(ReasoningEngineTestCase):
    def test_matches_relationships_and_type_matching_endpoints(self):
        result = self.engine.query(
            ReasoningQuery(entity_type="org", relationship_type="works_at")
        )
        entity_ids = {e.id for e in result.matched_entities}
        relationship_ids = {r.id for r in result.matched_relationships}
        self.assertEqual(entity_ids, {"acme"})
        self.assertEqual(relationship_ids, {"r-works-bob", "r-works-alice", "r-works-alice-2"})

    def test_matches_when_both_endpoints_match_type(self):
        # alice --self_ref--> alice: both endpoints are "person".
        result = self.engine.query(
            ReasoningQuery(entity_type="person", relationship_type="self_ref")
        )
        entity_ids = {e.id for e in result.matched_entities}
        self.assertEqual(entity_ids, {"alice"})
        self.assertEqual({r.id for r in result.matched_relationships}, {"r-self"})

    def test_no_relationships_of_that_type_match_entity_type(self):
        result = self.engine.query(
            ReasoningQuery(entity_type="vehicle", relationship_type="works_at")
        )
        self.assertEqual(result.matched_entities, ())
        self.assertEqual(result.matched_relationships, ())

    def test_filters_restrict_pattern_matches(self):
        result = self.engine.query(
            ReasoningQuery(
                entity_type="org", relationship_type="works_at", filters={"role": "manager"}
            )
        )
        relationship_ids = {r.id for r in result.matched_relationships}
        self.assertEqual(relationship_ids, {"r-works-alice"})
        entity_ids = {e.id for e in result.matched_entities}
        self.assertEqual(entity_ids, {"acme"})


# -- query(): invalid input ---------------------------------------------------


class QueryValidationTests(ReasoningEngineTestCase):
    def test_requires_reasoning_query_instance(self):
        with self.assertRaises(InvalidReasoningQueryError):
            self.engine.query("not-a-query")

    def test_requires_at_least_one_field(self):
        with self.assertRaises(InvalidReasoningQueryError):
            self.engine.query(ReasoningQuery())

    def test_rejects_zero_depth(self):
        with self.assertRaises(InvalidReasoningQueryError):
            self.engine.query(ReasoningQuery(entity_id="alice", depth=0))

    def test_rejects_negative_depth(self):
        with self.assertRaises(InvalidReasoningQueryError):
            self.engine.query(ReasoningQuery(entity_id="alice", depth=-1))

    def test_rejects_non_int_depth(self):
        with self.assertRaises(InvalidReasoningQueryError):
            self.engine.query(ReasoningQuery(entity_id="alice", depth="two"))

    def test_rejects_bool_depth(self):
        with self.assertRaises(InvalidReasoningQueryError):
            self.engine.query(ReasoningQuery(entity_id="alice", depth=True))


# -- neighbors() --------------------------------------------------------------


class NeighborsTests(ReasoningEngineTestCase):
    def test_returns_direct_neighbors_and_relationships(self):
        result = self.engine.neighbors("bob")
        ids = {e.id for e in result.matched_entities}
        self.assertEqual(ids, {"alice", "acme"})
        relationship_ids = {r.id for r in result.matched_relationships}
        self.assertEqual(relationship_ids, {"r-knows", "r-works-bob"})

    def test_includes_self_loop_entity_as_its_own_neighbor(self):
        result = self.engine.neighbors("alice")
        ids = [e.id for e in result.matched_entities]
        self.assertIn("alice", ids)

    def test_isolated_entity_returns_empty(self):
        result = self.engine.neighbors("carol")
        self.assertEqual(result.matched_entities, ())
        self.assertEqual(result.matched_relationships, ())

    def test_unknown_entity_raises(self):
        with self.assertRaises(ReasoningTargetNotFoundError):
            self.engine.neighbors("nonexistent")

    def test_invalid_entity_id_type_raises(self):
        with self.assertRaises(InvalidReasoningQueryError):
            self.engine.neighbors(123)

    def test_empty_entity_id_raises(self):
        with self.assertRaises(InvalidReasoningQueryError):
            self.engine.neighbors("")


# -- related_entities() --------------------------------------------------------


class RelatedEntitiesTests(ReasoningEngineTestCase):
    def test_no_type_filter_matches_neighbors(self):
        neighbors_result = self.engine.neighbors("alice")
        related_result = self.engine.related_entities("alice")
        self.assertEqual(
            {e.id for e in neighbors_result.matched_entities},
            {e.id for e in related_result.matched_entities},
        )

    def test_relationship_type_filter(self):
        result = self.engine.related_entities("alice", relationship_type="works_at")
        ids = {e.id for e in result.matched_entities}
        self.assertEqual(ids, {"acme"})

    def test_relationship_type_filter_no_matches(self):
        result = self.engine.related_entities("carol", relationship_type="knows")
        self.assertEqual(result.matched_entities, ())

    def test_unknown_entity_raises(self):
        with self.assertRaises(ReasoningTargetNotFoundError):
            self.engine.related_entities("nonexistent")

    def test_invalid_relationship_type_raises(self):
        with self.assertRaises(InvalidReasoningQueryError):
            self.engine.related_entities("alice", relationship_type="")


# -- entity_summary() ----------------------------------------------------------


class EntitySummaryTests(ReasoningEngineTestCase):
    def test_counts_outgoing_incoming_and_neighbors(self):
        result = self.engine.entity_summary("alice")
        self.assertEqual(result.matched_entities, (self.alice,))
        # alice's outgoing: knows->bob, works_at->acme (x2), self_ref->alice = 4
        self.assertEqual(result.metadata["outgoing_count"], 4)
        # alice's incoming: self_ref (alice->alice) = 1
        self.assertEqual(result.metadata["incoming_count"], 1)
        # distinct neighbors: bob, acme, alice(self) = 3
        self.assertEqual(result.metadata["neighbor_count"], 3)
        self.assertEqual(result.metadata["entity_type"], "person")

    def test_isolated_entity_summary(self):
        result = self.engine.entity_summary("carol")
        self.assertEqual(result.matched_entities, (self.carol,))
        self.assertEqual(result.metadata["outgoing_count"], 0)
        self.assertEqual(result.metadata["incoming_count"], 0)
        self.assertEqual(result.metadata["neighbor_count"], 0)
        self.assertEqual(result.matched_relationships, ())

    def test_unknown_entity_raises(self):
        with self.assertRaises(ReasoningTargetNotFoundError):
            self.engine.entity_summary("nonexistent")


# -- relationship_summary() ----------------------------------------------------


class RelationshipSummaryTests(ReasoningEngineTestCase):
    def test_counts_relationships_and_distinct_entities(self):
        result = self.engine.relationship_summary("works_at")
        self.assertEqual(len(result.matched_relationships), 3)
        self.assertEqual(result.metadata["relationship_count"], 3)
        ids = {e.id for e in result.matched_entities}
        self.assertEqual(ids, {"alice", "bob", "acme"})
        self.assertEqual(result.metadata["distinct_entity_count"], 3)

    def test_no_matches(self):
        result = self.engine.relationship_summary("married_to")
        self.assertEqual(result.matched_relationships, ())
        self.assertEqual(result.matched_entities, ())
        self.assertEqual(result.metadata["relationship_count"], 0)

    def test_invalid_relationship_type_raises(self):
        with self.assertRaises(InvalidReasoningQueryError):
            self.engine.relationship_summary("")

    def test_invalid_relationship_type_wrong_type_raises(self):
        with self.assertRaises(InvalidReasoningQueryError):
            self.engine.relationship_summary(None)


# -- find_paths() ---------------------------------------------------------------


class FindPathsTests(ReasoningEngineTestCase):
    def test_multiple_paths_within_depth(self):
        result = self.engine.find_paths("alice", "acme", max_depth=2)
        paths = result.metadata["paths"]
        # direct alice->acme (x2 parallel relationships) + alice->bob->acme = 3 paths
        self.assertEqual(result.metadata["path_count"], 3)
        self.assertIn(("alice", "acme"), paths)
        self.assertIn(("alice", "bob", "acme"), paths)

    def test_respects_max_depth(self):
        result = self.engine.find_paths("alice", "acme", max_depth=1)
        # only the two direct, parallel relationships qualify at depth 1
        self.assertEqual(result.metadata["path_count"], 2)
        for path in result.metadata["paths"]:
            self.assertEqual(path, ("alice", "acme"))

    def test_no_path_found(self):
        result = self.engine.find_paths("alice", "carol", max_depth=5)
        self.assertEqual(result.metadata["path_count"], 0)
        self.assertEqual(result.matched_entities, ())
        self.assertEqual(result.matched_relationships, ())

    def test_same_source_and_target_is_trivial_path(self):
        result = self.engine.find_paths("alice", "alice")
        self.assertEqual(result.metadata["path_count"], 1)
        self.assertEqual(result.metadata["paths"], (("alice",),))
        self.assertEqual(result.matched_entities, (self.alice,))
        self.assertEqual(result.matched_relationships, ())

    def test_default_max_depth_is_three(self):
        result = self.engine.find_paths("bob", "alice")
        # bob->alice via knows (reverse direction, depth 1) and
        # bob->acme->alice (depth 2, via works_at both ways)
        self.assertGreaterEqual(result.metadata["path_count"], 1)
        self.assertEqual(result.metadata["max_depth"], 3)

    def test_unknown_source_raises(self):
        with self.assertRaises(ReasoningTargetNotFoundError):
            self.engine.find_paths("nonexistent", "alice")

    def test_unknown_target_raises(self):
        with self.assertRaises(ReasoningTargetNotFoundError):
            self.engine.find_paths("alice", "nonexistent")

    def test_rejects_non_positive_max_depth(self):
        with self.assertRaises(InvalidReasoningQueryError):
            self.engine.find_paths("alice", "acme", max_depth=0)

    def test_rejects_empty_source_id(self):
        with self.assertRaises(InvalidReasoningQueryError):
            self.engine.find_paths("", "acme")

    def test_rejects_empty_target_id(self):
        with self.assertRaises(InvalidReasoningQueryError):
            self.engine.find_paths("alice", "")

    def test_matched_relationships_deduplicated(self):
        result = self.engine.find_paths("alice", "acme", max_depth=2)
        relationship_ids = [r.id for r in result.matched_relationships]
        self.assertEqual(len(relationship_ids), len(set(relationship_ids)))


# -- empty graph ------------------------------------------------------------


class EmptyGraphTests(unittest.TestCase):
    def setUp(self):
        self.event_bus = InMemoryEventBus(logger=_silent_logger())
        self.graph = KnowledgeGraph(event_bus=self.event_bus)
        self.memory_service = MemoryService(storage=_InMemoryStorage(), event_bus=self.event_bus)
        self.memory_integration = MemoryIntegration(
            memory_service=self.memory_service,
            knowledge_graph=self.graph,
            event_bus=self.event_bus,
        )
        self.engine = ReasoningEngine(
            knowledge_graph=self.graph,
            memory_integration=self.memory_integration,
            event_bus=self.event_bus,
        )

    def test_query_by_entity_type_returns_empty(self):
        result = self.engine.query(ReasoningQuery(entity_type="anything"))
        self.assertEqual(result.matched_entities, ())

    def test_query_by_relationship_type_returns_empty(self):
        result = self.engine.query(ReasoningQuery(relationship_type="anything"))
        self.assertEqual(result.matched_relationships, ())

    def test_neighbors_on_unknown_entity_raises(self):
        with self.assertRaises(ReasoningTargetNotFoundError):
            self.engine.neighbors("anything")

    def test_find_paths_on_unknown_entities_raises(self):
        with self.assertRaises(ReasoningTargetNotFoundError):
            self.engine.find_paths("a", "b")

    def test_relationship_summary_returns_empty(self):
        result = self.engine.relationship_summary("anything")
        self.assertEqual(result.matched_relationships, ())
        self.assertEqual(result.matched_entities, ())


# -- event publication --------------------------------------------------------


class EventPublicationTests(ReasoningEngineTestCase):
    def test_successful_call_publishes_executed_then_result_created(self):
        received = self._events(
            EventType.REASONING_QUERY_EXECUTED,
            EventType.REASONING_RESULT_CREATED,
            EventType.REASONING_QUERY_FAILED,
        )
        self.engine.neighbors("alice")
        self.assertEqual(
            [event.type for event in received],
            [EventType.REASONING_QUERY_EXECUTED, EventType.REASONING_RESULT_CREATED],
        )
        self.assertEqual(received[0].source, "reasoning_engine")
        self.assertEqual(received[0].payload["operation"], "neighbors")
        # alice's direct neighbors: bob (knows), acme (works_at x2,
        # deduplicated), and alice itself (the self_ref self-loop) = 3.
        self.assertEqual(received[1].payload["matched_entity_count"], 3)

    def test_failed_call_publishes_query_failed_only(self):
        received = self._events(
            EventType.REASONING_QUERY_EXECUTED,
            EventType.REASONING_RESULT_CREATED,
            EventType.REASONING_QUERY_FAILED,
        )
        with self.assertRaises(ReasoningTargetNotFoundError):
            self.engine.neighbors("nonexistent")
        self.assertEqual([event.type for event in received], [EventType.REASONING_QUERY_FAILED])
        self.assertEqual(received[0].payload["operation"], "neighbors")
        self.assertIn("reason", received[0].payload)

    def test_every_public_method_publishes_on_success(self):
        received = self._events(EventType.REASONING_QUERY_EXECUTED, EventType.REASONING_RESULT_CREATED)

        self.engine.query(ReasoningQuery(entity_id="alice"))
        self.engine.neighbors("alice")
        self.engine.find_paths("alice", "acme")
        self.engine.related_entities("alice")
        self.engine.entity_summary("alice")
        self.engine.relationship_summary("works_at")

        operations = [
            event.payload["operation"] for event in received if event.type == EventType.REASONING_QUERY_EXECUTED
        ]
        self.assertEqual(
            operations,
            ["query", "neighbors", "find_paths", "related_entities", "entity_summary", "relationship_summary"],
        )

    def test_every_public_method_publishes_on_failure(self):
        received = self._events(EventType.REASONING_QUERY_FAILED)

        for call in (
            lambda: self.engine.query(ReasoningQuery()),
            lambda: self.engine.neighbors("nonexistent"),
            lambda: self.engine.find_paths("nonexistent", "alice"),
            lambda: self.engine.related_entities("nonexistent"),
            lambda: self.engine.entity_summary("nonexistent"),
            lambda: self.engine.relationship_summary(""),
        ):
            with self.assertRaises(ReasoningError):
                call()

        self.assertEqual(len(received), 6)
        for event in received:
            self.assertEqual(event.type, EventType.REASONING_QUERY_FAILED)


# -- Memory Integration metadata --------------------------------------------


class MemorySynchronizationMetadataTests(ReasoningEngineTestCase):
    def test_result_metadata_includes_synchronization_status_snapshot(self):
        result = self.engine.neighbors("alice")
        self.assertIn("memory_synchronization_status", result.metadata)
        status = result.metadata["memory_synchronization_status"]
        self.assertEqual(status, self.memory_integration.synchronization_status())

    def test_metadata_reflects_live_synchronization_state(self):
        self.memory_service.put(MemoryRecord(key="k1", value={"hello": "world"}))
        self.memory_integration.initialize()
        self.memory_integration.start()
        try:
            self.memory_integration.synchronize_memory("k1")
        finally:
            self.memory_integration.stop()

        result = self.engine.entity_summary("alice")
        status = result.metadata["memory_synchronization_status"]
        self.assertEqual(status["synchronized_count"], 1)
        self.assertIn("k1", status["synchronized_keys"])


if __name__ == "__main__":
    unittest.main()
