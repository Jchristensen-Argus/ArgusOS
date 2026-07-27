"""Unit tests for argus.goal.goal.Goal."""

import copy
import dataclasses
import pickle
import unittest

from argus.goal import Goal, GoalMetadata, GoalPriority, GoalStatus


class DefaultsTests(unittest.TestCase):
    def test_defaults(self):
        goal = Goal()
        self.assertTrue(goal.goal_id)
        self.assertEqual(goal.name, "")
        self.assertEqual(goal.description, "")
        self.assertEqual(goal.status, GoalStatus.PLANNING)
        self.assertEqual(goal.priority, GoalPriority.NORMAL)
        self.assertIsInstance(goal.metadata, GoalMetadata)

    def test_all_fields_set(self):
        metadata = GoalMetadata(extra={"k": "v"})
        goal = Goal(
            goal_id="fixed-id",
            name="Launch product line",
            description="Ship v1",
            status=GoalStatus.ACTIVE,
            priority=GoalPriority.HIGH,
            metadata=metadata,
        )
        self.assertEqual(goal.goal_id, "fixed-id")
        self.assertEqual(goal.name, "Launch product line")
        self.assertEqual(goal.description, "Ship v1")
        self.assertEqual(goal.status, GoalStatus.ACTIVE)
        self.assertEqual(goal.priority, GoalPriority.HIGH)
        self.assertIs(goal.metadata, metadata)

    def test_default_goal_id_is_unique_per_instance(self):
        a = Goal()
        b = Goal()
        self.assertNotEqual(a.goal_id, b.goal_id)


class FieldOrderTests(unittest.TestCase):
    def test_field_order_places_metadata_last(self):
        field_names = [f.name for f in dataclasses.fields(Goal)]
        self.assertEqual(
            field_names,
            ["goal_id", "name", "description", "status", "priority", "metadata"],
        )


class DefaultStatusAndPriorityTests(unittest.TestCase):
    def test_default_status_is_planning(self):
        # Matches ProjectStatus's own default (036), unlike
        # WorkspaceStatus's ACTIVE (037) - see status.py's own module
        # docstring.
        self.assertEqual(Goal().status, GoalStatus.PLANNING)

    def test_default_priority_is_normal_not_low(self):
        # The first genuine exception to the "first-listed member is
        # the default" convention - see priority.py's own module
        # docstring.
        self.assertEqual(Goal().priority, GoalPriority.NORMAL)


class ImmutabilityTests(unittest.TestCase):
    def test_immutability(self):
        goal = Goal()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            goal.goal_id = "mutated"

    def test_name_field_immutable(self):
        goal = Goal()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            goal.name = "mutated"

    def test_priority_field_immutable(self):
        goal = Goal()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            goal.priority = GoalPriority.CRITICAL

    def test_metadata_field_immutable(self):
        goal = Goal()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            goal.metadata = GoalMetadata()


class MiscellaneousRobustnessTests(unittest.TestCase):
    def test_deepcopy_of_scalar_fields_round_trips_equal(self):
        goal = Goal()
        copied_id = copy.deepcopy(goal.goal_id)
        self.assertEqual(copied_id, goal.goal_id)

    def test_pickle_of_scalar_fields_round_trips_equal(self):
        goal = Goal()
        self.assertEqual(pickle.loads(pickle.dumps(goal.goal_id)), goal.goal_id)
        self.assertIs(pickle.loads(pickle.dumps(goal.status)), goal.status)
        self.assertIs(pickle.loads(pickle.dumps(goal.priority)), goal.priority)

    def test_goal_id_is_a_plain_string_suitable_for_json(self):
        goal = Goal()
        self.assertIsInstance(goal.goal_id, str)


class EqualityTests(unittest.TestCase):
    def test_equality_when_all_fields_match(self):
        metadata = GoalMetadata()
        a = Goal(goal_id="g1", name="Grow revenue", metadata=metadata)
        b = Goal(goal_id="g1", name="Grow revenue", metadata=metadata)
        self.assertEqual(a, b)

    def test_not_equal_when_goal_id_differs(self):
        metadata = GoalMetadata()
        a = Goal(goal_id="g1", metadata=metadata)
        b = Goal(goal_id="g2", metadata=metadata)
        self.assertNotEqual(a, b)

    def test_not_equal_when_priority_differs(self):
        metadata = GoalMetadata()
        a = Goal(goal_id="g1", priority=GoalPriority.LOW, metadata=metadata)
        b = Goal(goal_id="g1", priority=GoalPriority.CRITICAL, metadata=metadata)
        self.assertNotEqual(a, b)

    def test_not_equal_when_status_differs(self):
        metadata = GoalMetadata()
        a = Goal(goal_id="g1", status=GoalStatus.PLANNING, metadata=metadata)
        b = Goal(goal_id="g1", status=GoalStatus.ABANDONED, metadata=metadata)
        self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main()
