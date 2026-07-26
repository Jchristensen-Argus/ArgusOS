"""Unit tests for argus.planning.goal.PlanningGoal."""

import dataclasses
import unittest

from argus.planning.goal import PlanningGoal


class PlanningGoalTests(unittest.TestCase):
    def test_defaults(self):
        goal = PlanningGoal(name="my_goal")
        self.assertEqual(goal.name, "my_goal")
        self.assertTrue(goal.goal_id)
        self.assertIsInstance(goal.goal_id, str)
        self.assertEqual(goal.description, "")
        self.assertEqual(goal.priority, 0)

    def test_all_fields_set(self):
        goal = PlanningGoal(
            name="my_goal",
            goal_id="goal-1",
            description="A goal.",
            priority=7,
        )
        self.assertEqual(goal.name, "my_goal")
        self.assertEqual(goal.goal_id, "goal-1")
        self.assertEqual(goal.description, "A goal.")
        self.assertEqual(goal.priority, 7)

    def test_default_goal_id_is_unique_per_instance(self):
        first = PlanningGoal(name="a")
        second = PlanningGoal(name="a")
        self.assertNotEqual(first.goal_id, second.goal_id)

    def test_immutability(self):
        goal = PlanningGoal(name="my_goal")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            goal.name = "changed"
        with self.assertRaises(dataclasses.FrozenInstanceError):
            goal.priority = 99

    def test_priority_accepts_any_int_with_no_side_effects(self):
        # Priority is descriptive only - no scheduling logic exists
        # anywhere in this module to validate or act on it.
        low = PlanningGoal(name="low", priority=-100)
        high = PlanningGoal(name="high", priority=100)
        self.assertEqual(low.priority, -100)
        self.assertEqual(high.priority, 100)

    def test_equality_when_all_fields_match(self):
        first = PlanningGoal(name="a", goal_id="same", description="d", priority=1)
        second = PlanningGoal(name="a", goal_id="same", description="d", priority=1)
        self.assertEqual(first, second)

    def test_inequality_by_goal_id(self):
        first = PlanningGoal(name="a", goal_id="x")
        second = PlanningGoal(name="a", goal_id="y")
        self.assertNotEqual(first, second)

    def test_inequality_by_priority(self):
        first = PlanningGoal(name="a", goal_id="same", priority=1)
        second = PlanningGoal(name="a", goal_id="same", priority=2)
        self.assertNotEqual(first, second)

    def test_two_default_constructed_goals_with_same_name_are_not_equal(self):
        first = PlanningGoal(name="a")
        second = PlanningGoal(name="a")
        self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
