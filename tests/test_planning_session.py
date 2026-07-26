"""Unit tests for argus.planning.session.PlanningSession."""

import dataclasses
import unittest
from datetime import datetime, timezone

from argus.context.context import CognitiveContext
from argus.planning.constraint import PlanningConstraint
from argus.planning.goal import PlanningGoal
from argus.planning.metadata import PlanningMetadata
from argus.planning.session import PlanningSession


def _fixed_metadata(correlation_id="corr-1"):
    return PlanningMetadata(
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        version="1.0",
        correlation_id=correlation_id,
        extra={},
    )


class PlanningSessionEmptyTests(unittest.TestCase):
    def test_empty_session_defaults(self):
        session = PlanningSession()
        self.assertIsNone(session.cognitive_context)
        self.assertEqual(session.goals, ())
        self.assertEqual(session.constraints, ())
        self.assertIsInstance(session.metadata, PlanningMetadata)

    def test_empty_session_has_generated_session_id(self):
        session = PlanningSession()
        self.assertIsInstance(session.session_id, str)
        self.assertTrue(session.session_id)

    def test_default_session_id_is_unique_per_instance(self):
        first = PlanningSession()
        second = PlanningSession()
        self.assertNotEqual(first.session_id, second.session_id)

    def test_default_metadata_is_independent_per_instance(self):
        first = PlanningSession()
        second = PlanningSession()
        self.assertNotEqual(first.metadata.correlation_id, second.metadata.correlation_id)


class PlanningSessionPopulatedTests(unittest.TestCase):
    def test_all_fields_set(self):
        context = CognitiveContext(conversation_id="conv-1")
        goal = PlanningGoal(name="goal-1")
        constraint = PlanningConstraint(name="constraint-1")
        session = PlanningSession(
            session_id="session-1",
            cognitive_context=context,
            goals=[goal],
            constraints=[constraint],
            metadata=_fixed_metadata(),
        )
        self.assertEqual(session.session_id, "session-1")
        self.assertIs(session.cognitive_context, context)
        self.assertEqual(session.goals, (goal,))
        self.assertEqual(session.constraints, (constraint,))
        self.assertEqual(session.metadata, _fixed_metadata())

    def test_multiple_goals_preserve_call_order_regardless_of_priority(self):
        low_priority_first = PlanningGoal(name="first", priority=100)
        high_priority_second = PlanningGoal(name="second", priority=1)
        session = PlanningSession(goals=[low_priority_first, high_priority_second])
        self.assertEqual(session.goals, (low_priority_first, high_priority_second))

    def test_multiple_constraints_preserve_order(self):
        first = PlanningConstraint(name="first")
        second = PlanningConstraint(name="second")
        session = PlanningSession(constraints=[first, second])
        self.assertEqual(session.constraints, (first, second))

    def test_sequence_fields_are_wrapped_in_tuples(self):
        session = PlanningSession(
            goals=[PlanningGoal(name="g1")],
            constraints=[PlanningConstraint(name="c1")],
        )
        self.assertIsInstance(session.goals, tuple)
        self.assertIsInstance(session.constraints, tuple)

    def test_sequence_fields_defensive_copy_not_shared_with_caller(self):
        source = [PlanningGoal(name="g1")]
        session = PlanningSession(goals=source)
        source.append(PlanningGoal(name="g2"))
        self.assertEqual(len(session.goals), 1)

    def test_cognitive_context_is_held_directly_not_copied(self):
        context = CognitiveContext(conversation_id="conv-1")
        session = PlanningSession(cognitive_context=context)
        self.assertIs(session.cognitive_context, context)


class PlanningSessionImmutabilityTests(unittest.TestCase):
    def test_cannot_reassign_fields(self):
        session = PlanningSession()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            session.session_id = "changed"
        with self.assertRaises(dataclasses.FrozenInstanceError):
            session.cognitive_context = CognitiveContext()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            session.goals = ()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            session.metadata = PlanningMetadata()

    def test_goals_tuple_cannot_be_mutated_in_place(self):
        session = PlanningSession(goals=[PlanningGoal(name="g1")])
        with self.assertRaises(AttributeError):
            session.goals.append(PlanningGoal(name="g2"))

    def test_contained_cognitive_context_remains_immutable(self):
        context = CognitiveContext(conversation_id="conv-1")
        session = PlanningSession(cognitive_context=context)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            session.cognitive_context.conversation_id = "changed"


class PlanningSessionEqualityTests(unittest.TestCase):
    def test_equal_when_every_field_matches(self):
        goal = PlanningGoal(name="g1", goal_id="g1")
        first = PlanningSession(session_id="same", goals=[goal], metadata=_fixed_metadata())
        second = PlanningSession(session_id="same", goals=[goal], metadata=_fixed_metadata())
        self.assertEqual(first, second)

    def test_not_equal_when_session_id_differs(self):
        first = PlanningSession(session_id="a", metadata=_fixed_metadata())
        second = PlanningSession(session_id="b", metadata=_fixed_metadata())
        self.assertNotEqual(first, second)

    def test_not_equal_when_goals_differ(self):
        first = PlanningSession(session_id="same", goals=[PlanningGoal(name="g1", goal_id="g1")], metadata=_fixed_metadata())
        second = PlanningSession(session_id="same", goals=[PlanningGoal(name="g2", goal_id="g2")], metadata=_fixed_metadata())
        self.assertNotEqual(first, second)

    def test_not_equal_when_metadata_differs(self):
        first = PlanningSession(session_id="same", metadata=_fixed_metadata("corr-1"))
        second = PlanningSession(session_id="same", metadata=_fixed_metadata("corr-2"))
        self.assertNotEqual(first, second)

    def test_two_default_constructed_sessions_are_not_equal(self):
        first = PlanningSession()
        second = PlanningSession()
        self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
