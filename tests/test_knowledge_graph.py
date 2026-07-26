"""Unit tests for argus.knowledge_graph.graph.KnowledgeGraph."""

import logging
import unittest

from argus.events import EventType, InMemoryEventBus
from argus.knowledge_graph import (
    DuplicateEntityError,
    DuplicateRelationshipError,
    Entity,
    EntityNotFoundError,
    IKnowledgeGraph,
    InvalidEntityError,
    InvalidRelationshipError,
    KnowledgeGraph,
    Relationship,
    RelationshipNotFoundError,
)
from argus.lifecycle import LifecycleState


def _silent_logger() -> logging.Logger:
    logger = logging.getLogger("test_knowledge_graph")
    logger.addHandler(logging.NullHandler())
    logger.propagate = False
    return logger


class KnowledgeGraphTestCase(unittest.TestCase):
    def setUp(self):
        self.event_bus = InMemoryEventBus(logger=_silent_logger())
        self.received = []
        for event_type in (
            EventType.ENTITY_ADDED,
            EventType.ENTITY_REMOVED,
            EventType.RELATIONSHIP_ADDED,
            EventType.RELATIONSHIP_REMOVED,
        ):
            self.event_bus.subscribe(event_type, self.received.append)
        self.graph = KnowledgeGraph(event_bus=self.event_bus)

    def _entity(self, **overrides):
        defaults = dict(entity_type="person", name="Alice")
        defaults.update(overrides)
        return Entity(**defaults)

    def _relationship(self, source, target, **overrides):
        defaults = dict(source_entity_id=source, target_entity_id=target, relationship_type="knows")
        defaults.update(overrides)
        return Relationship(**defaults)


class ConstructionTests(KnowledgeGraphTestCase):
    def test_implements_iknowledge_graph(self):
        self.assertIsInstance(self.graph, IKnowledgeGraph)

    def test_starts_in_created_state(self):
        self.assertEqual(self.graph.status(), LifecycleState.CREATED)

    def test_starts_with_no_entities_or_relationships(self):
        self.assertEqual(self.graph.list_entities(), ())
        self.assertEqual(self.graph.list_relationships(), ())


class EntityRegistrationTests(KnowledgeGraphTestCase):
    def test_add_then_get(self):
        entity = self._entity()

        self.graph.add_entity(entity)

        self.assertEqual(self.graph.get_entity(entity.id), entity)

    def test_add_publishes_entity_added(self):
        entity = self._entity()

        self.graph.add_entity(entity)

        types = [event.type for event in self.received]
        self.assertIn(EventType.ENTITY_ADDED, types)

    def test_add_rejects_non_entity(self):
        with self.assertRaises(InvalidEntityError):
            self.graph.add_entity("not-an-entity")

    def test_add_rejects_empty_entity_type(self):
        entity = Entity(entity_type="", name="Alice")

        with self.assertRaises(InvalidEntityError):
            self.graph.add_entity(entity)

    def test_add_rejects_empty_name(self):
        entity = Entity(entity_type="person", name="")

        with self.assertRaises(InvalidEntityError):
            self.graph.add_entity(entity)

    def test_add_rejects_empty_id(self):
        entity = Entity(id="", entity_type="person", name="Alice")

        with self.assertRaises(InvalidEntityError):
            self.graph.add_entity(entity)

    def test_duplicate_entity_raises(self):
        entity = self._entity()
        self.graph.add_entity(entity)

        with self.assertRaises(DuplicateEntityError):
            self.graph.add_entity(entity)

    def test_duplicate_entity_does_not_publish_again(self):
        entity = self._entity()
        self.graph.add_entity(entity)
        self.received.clear()

        with self.assertRaises(DuplicateEntityError):
            self.graph.add_entity(entity)

        self.assertEqual(self.received, [])


class EntityLookupTests(KnowledgeGraphTestCase):
    def test_get_unknown_entity_raises(self):
        with self.assertRaises(EntityNotFoundError):
            self.graph.get_entity("unknown")

    def test_get_with_empty_id_raises_invalid_entity_error(self):
        with self.assertRaises(InvalidEntityError):
            self.graph.get_entity("")

    def test_get_with_non_string_id_raises_invalid_entity_error(self):
        with self.assertRaises(InvalidEntityError):
            self.graph.get_entity(123)

    def test_list_entities_returns_all_registered(self):
        first = self._entity(name="Alice")
        second = self._entity(name="Bob")
        self.graph.add_entity(first)
        self.graph.add_entity(second)

        listed = self.graph.list_entities()

        self.assertEqual(len(listed), 2)
        self.assertIn(first, listed)
        self.assertIn(second, listed)

    def test_find_by_type_filters_correctly(self):
        person = self._entity(entity_type="person", name="Alice")
        workflow = self._entity(entity_type="workflow", name="Onboarding")
        self.graph.add_entity(person)
        self.graph.add_entity(workflow)

        found = self.graph.find_by_type("person")

        self.assertEqual(found, (person,))

    def test_find_by_type_with_no_matches_returns_empty(self):
        self.graph.add_entity(self._entity(entity_type="person"))

        self.assertEqual(self.graph.find_by_type("workflow"), ())


class EntityRemovalTests(KnowledgeGraphTestCase):
    def test_remove_removes_entity(self):
        entity = self._entity()
        self.graph.add_entity(entity)

        self.graph.remove_entity(entity.id)

        with self.assertRaises(EntityNotFoundError):
            self.graph.get_entity(entity.id)

    def test_remove_unknown_entity_raises(self):
        with self.assertRaises(EntityNotFoundError):
            self.graph.remove_entity("unknown")

    def test_remove_publishes_entity_removed(self):
        entity = self._entity()
        self.graph.add_entity(entity)
        self.received.clear()

        self.graph.remove_entity(entity.id)

        types = [event.type for event in self.received]
        self.assertIn(EventType.ENTITY_REMOVED, types)

    def test_remove_cascades_to_relationships_as_source(self):
        alice = self._entity(name="Alice")
        bob = self._entity(name="Bob")
        self.graph.add_entity(alice)
        self.graph.add_entity(bob)
        relationship = self._relationship(alice.id, bob.id)
        self.graph.add_relationship(relationship)

        self.graph.remove_entity(alice.id)

        self.assertEqual(self.graph.list_relationships(), ())

    def test_remove_cascades_to_relationships_as_target(self):
        alice = self._entity(name="Alice")
        bob = self._entity(name="Bob")
        self.graph.add_entity(alice)
        self.graph.add_entity(bob)
        relationship = self._relationship(alice.id, bob.id)
        self.graph.add_relationship(relationship)

        self.graph.remove_entity(bob.id)

        self.assertEqual(self.graph.list_relationships(), ())

    def test_cascaded_removal_does_not_publish_relationship_removed(self):
        alice = self._entity(name="Alice")
        bob = self._entity(name="Bob")
        self.graph.add_entity(alice)
        self.graph.add_entity(bob)
        self.graph.add_relationship(self._relationship(alice.id, bob.id))
        self.received.clear()

        self.graph.remove_entity(alice.id)

        types = [event.type for event in self.received]
        self.assertIn(EventType.ENTITY_REMOVED, types)
        self.assertNotIn(EventType.RELATIONSHIP_REMOVED, types)

    def test_remove_does_not_affect_unrelated_relationships(self):
        alice = self._entity(name="Alice")
        bob = self._entity(name="Bob")
        carol = self._entity(name="Carol")
        self.graph.add_entity(alice)
        self.graph.add_entity(bob)
        self.graph.add_entity(carol)
        unrelated = self._relationship(bob.id, carol.id)
        self.graph.add_relationship(unrelated)

        self.graph.remove_entity(alice.id)

        self.assertEqual(self.graph.list_relationships(), (unrelated,))


class RelationshipRegistrationTests(KnowledgeGraphTestCase):
    def setUp(self):
        super().setUp()
        self.alice = self._entity(name="Alice")
        self.bob = self._entity(name="Bob")
        self.graph.add_entity(self.alice)
        self.graph.add_entity(self.bob)

    def test_add_then_list(self):
        relationship = self._relationship(self.alice.id, self.bob.id)

        self.graph.add_relationship(relationship)

        self.assertEqual(self.graph.list_relationships(), (relationship,))

    def test_add_publishes_relationship_added(self):
        relationship = self._relationship(self.alice.id, self.bob.id)

        self.graph.add_relationship(relationship)

        types = [event.type for event in self.received]
        self.assertIn(EventType.RELATIONSHIP_ADDED, types)

    def test_add_rejects_non_relationship(self):
        with self.assertRaises(InvalidRelationshipError):
            self.graph.add_relationship("not-a-relationship")

    def test_add_rejects_empty_relationship_type(self):
        relationship = Relationship(
            source_entity_id=self.alice.id, target_entity_id=self.bob.id, relationship_type=""
        )

        with self.assertRaises(InvalidRelationshipError):
            self.graph.add_relationship(relationship)

    def test_add_rejects_empty_source_entity_id(self):
        relationship = Relationship(
            source_entity_id="", target_entity_id=self.bob.id, relationship_type="knows"
        )

        with self.assertRaises(InvalidRelationshipError):
            self.graph.add_relationship(relationship)

    def test_add_rejects_empty_target_entity_id(self):
        relationship = Relationship(
            source_entity_id=self.alice.id, target_entity_id="", relationship_type="knows"
        )

        with self.assertRaises(InvalidRelationshipError):
            self.graph.add_relationship(relationship)

    def test_add_rejects_empty_id(self):
        relationship = Relationship(
            id="",
            source_entity_id=self.alice.id,
            target_entity_id=self.bob.id,
            relationship_type="knows",
        )

        with self.assertRaises(InvalidRelationshipError):
            self.graph.add_relationship(relationship)

    def test_add_rejects_unknown_source_entity(self):
        relationship = self._relationship("unknown", self.bob.id)

        with self.assertRaises(EntityNotFoundError):
            self.graph.add_relationship(relationship)

    def test_add_rejects_unknown_target_entity(self):
        relationship = self._relationship(self.alice.id, "unknown")

        with self.assertRaises(EntityNotFoundError):
            self.graph.add_relationship(relationship)

    def test_invalid_reference_does_not_publish(self):
        relationship = self._relationship("unknown", self.bob.id)
        self.received.clear()

        with self.assertRaises(EntityNotFoundError):
            self.graph.add_relationship(relationship)

        self.assertEqual(self.received, [])

    def test_self_loop_is_permitted(self):
        relationship = self._relationship(self.alice.id, self.alice.id)

        self.graph.add_relationship(relationship)

        self.assertEqual(self.graph.list_relationships(), (relationship,))

    def test_duplicate_relationship_raises(self):
        relationship = self._relationship(self.alice.id, self.bob.id)
        self.graph.add_relationship(relationship)

        with self.assertRaises(DuplicateRelationshipError):
            self.graph.add_relationship(relationship)

    def test_multiple_relationships_between_same_pair_are_allowed(self):
        first = self._relationship(self.alice.id, self.bob.id, relationship_type="knows")
        second = self._relationship(self.alice.id, self.bob.id, relationship_type="works_with")

        self.graph.add_relationship(first)
        self.graph.add_relationship(second)

        self.assertEqual(len(self.graph.list_relationships()), 2)


class RelationshipRemovalTests(KnowledgeGraphTestCase):
    def setUp(self):
        super().setUp()
        self.alice = self._entity(name="Alice")
        self.bob = self._entity(name="Bob")
        self.graph.add_entity(self.alice)
        self.graph.add_entity(self.bob)

    def test_remove_removes_relationship(self):
        relationship = self._relationship(self.alice.id, self.bob.id)
        self.graph.add_relationship(relationship)

        self.graph.remove_relationship(relationship.id)

        self.assertEqual(self.graph.list_relationships(), ())

    def test_remove_unknown_relationship_raises(self):
        with self.assertRaises(RelationshipNotFoundError):
            self.graph.remove_relationship("unknown")

    def test_remove_with_empty_id_raises_invalid_relationship_error(self):
        with self.assertRaises(InvalidRelationshipError):
            self.graph.remove_relationship("")

    def test_remove_publishes_relationship_removed(self):
        relationship = self._relationship(self.alice.id, self.bob.id)
        self.graph.add_relationship(relationship)
        self.received.clear()

        self.graph.remove_relationship(relationship.id)

        types = [event.type for event in self.received]
        self.assertIn(EventType.RELATIONSHIP_REMOVED, types)

    def test_removing_relationship_does_not_remove_entities(self):
        relationship = self._relationship(self.alice.id, self.bob.id)
        self.graph.add_relationship(relationship)

        self.graph.remove_relationship(relationship.id)

        self.assertEqual(len(self.graph.list_entities()), 2)


class NeighborsTests(KnowledgeGraphTestCase):
    def setUp(self):
        super().setUp()
        self.alice = self._entity(name="Alice")
        self.bob = self._entity(name="Bob")
        self.carol = self._entity(name="Carol")
        self.graph.add_entity(self.alice)
        self.graph.add_entity(self.bob)
        self.graph.add_entity(self.carol)

    def test_neighbors_via_outgoing_relationship(self):
        self.graph.add_relationship(self._relationship(self.alice.id, self.bob.id))

        self.assertEqual(self.graph.neighbors(self.alice.id), (self.bob,))

    def test_neighbors_via_incoming_relationship(self):
        self.graph.add_relationship(self._relationship(self.bob.id, self.alice.id))

        self.assertEqual(self.graph.neighbors(self.alice.id), (self.bob,))

    def test_neighbors_with_no_relationships_is_empty(self):
        self.assertEqual(self.graph.neighbors(self.alice.id), ())

    def test_neighbors_deduplicates(self):
        self.graph.add_relationship(
            self._relationship(self.alice.id, self.bob.id, relationship_type="knows")
        )
        self.graph.add_relationship(
            self._relationship(self.alice.id, self.bob.id, relationship_type="works_with")
        )

        self.assertEqual(self.graph.neighbors(self.alice.id), (self.bob,))

    def test_neighbors_includes_multiple_distinct_entities(self):
        self.graph.add_relationship(self._relationship(self.alice.id, self.bob.id))
        self.graph.add_relationship(self._relationship(self.alice.id, self.carol.id))

        neighbors = self.graph.neighbors(self.alice.id)

        self.assertEqual(set(e.id for e in neighbors), {self.bob.id, self.carol.id})

    def test_neighbors_unknown_entity_raises(self):
        with self.assertRaises(EntityNotFoundError):
            self.graph.neighbors("unknown")

    def test_neighbors_excludes_unrelated_entities(self):
        self.graph.add_relationship(self._relationship(self.alice.id, self.bob.id))

        neighbors = self.graph.neighbors(self.alice.id)

        self.assertNotIn(self.carol, neighbors)

    def test_neighbors_skips_relationships_not_involving_the_entity(self):
        # alice-bob is the only relationship that should count toward
        # alice's neighbors; bob-carol involves neither alice as
        # source nor target, exercising neighbors()'s "this
        # relationship doesn't touch entity_id at all" skip branch.
        self.graph.add_relationship(self._relationship(self.alice.id, self.bob.id))
        self.graph.add_relationship(self._relationship(self.bob.id, self.carol.id))

        neighbors = self.graph.neighbors(self.alice.id)

        self.assertEqual(neighbors, (self.bob,))


class LifecycleTests(KnowledgeGraphTestCase):
    def test_initialize_then_start_transitions_to_running(self):
        self.graph.initialize()
        self.graph.start()

        self.assertEqual(self.graph.status(), LifecycleState.RUNNING)

    def test_stop_transitions_to_stopped(self):
        self.graph.initialize()
        self.graph.start()
        self.graph.stop()

        self.assertEqual(self.graph.status(), LifecycleState.STOPPED)

    def test_start_before_initialize_raises(self):
        with self.assertRaises(Exception):
            self.graph.start()

    def test_stop_before_start_raises(self):
        self.graph.initialize()

        with self.assertRaises(Exception):
            self.graph.stop()

    def test_initialize_twice_raises(self):
        self.graph.initialize()

        with self.assertRaises(Exception):
            self.graph.initialize()

    def test_graph_methods_are_ungated_before_running(self):
        # Unlike IntentDispatcher.dispatch() or AgentRuntime.start_execution(),
        # none of KnowledgeGraph's own methods are lifecycle-gated - they
        # all work regardless of IService state, exactly mirroring
        # IntentRouter's identical shape (see interfaces.py's Architectural
        # Note).
        entity = self._entity()

        self.graph.add_entity(entity)

        self.assertEqual(self.graph.get_entity(entity.id), entity)

    def test_graph_methods_are_ungated_after_stop(self):
        self.graph.initialize()
        self.graph.start()
        self.graph.stop()

        entity = self._entity()
        self.graph.add_entity(entity)

        self.assertEqual(self.graph.get_entity(entity.id), entity)


if __name__ == "__main__":
    unittest.main()
