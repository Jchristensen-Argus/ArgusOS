"""Unit tests for argus.goal.builder.GoalBuilder."""

import unittest

from argus.goal import GoalBuilder, GoalPriority, GoalStatus, IGoalBuilder, InvalidGoalError


class IdentityTests(unittest.TestCase):
    def test_is_an_igoalbuilder(self):
        self.assertIsInstance(GoalBuilder(), IGoalBuilder)

    def test_is_not_an_iservice(self):
        from argus.lifecycle import IService

        self.assertNotIsInstance(GoalBuilder(), IService)

    def test_starts_with_default_values(self):
        goal = GoalBuilder().build()
        self.assertEqual(goal.name, "")
        self.assertEqual(goal.description, "")
        self.assertEqual(goal.status, GoalStatus.PLANNING)
        self.assertEqual(goal.priority, GoalPriority.NORMAL)

    def test_constructor_takes_no_arguments(self):
        builder = GoalBuilder()
        self.assertIsInstance(builder, GoalBuilder)

    def test_no_with_goal_id_method_exists(self):
        # This package's own Responsibilities list does not name
        # "assign id" - matching RelationshipBuilder's (031),
        # ExecutionResultBuilder's (032),
        # CapabilityExecutionResultBuilder's (034),
        # CapabilityContextBuilder's (035), ProjectBuilder's (036),
        # and WorkspaceBuilder's (037) own shape.
        self.assertFalse(hasattr(GoalBuilder(), "with_goal_id"))

    def test_no_with_owner_method_exists(self):
        self.assertFalse(hasattr(GoalBuilder(), "with_owner"))

    def test_no_with_tags_method_exists(self):
        self.assertFalse(hasattr(GoalBuilder(), "with_tags"))

    def test_has_with_priority_method(self):
        # Unlike owner/tags, priority is explicitly named in this
        # package's own Responsibilities list - see builder.py's own
        # module docstring.
        self.assertTrue(hasattr(GoalBuilder(), "with_priority"))


class WithNameTests(unittest.TestCase):
    def test_with_name_returns_self_for_chaining(self):
        builder = GoalBuilder()
        result = builder.with_name("Grow revenue")
        self.assertIs(result, builder)

    def test_with_name_is_overwritten_not_accumulated(self):
        goal = GoalBuilder().with_name("First").with_name("Second").build()
        self.assertEqual(goal.name, "Second")

    def test_with_name_rejects_empty_string(self):
        with self.assertRaises(InvalidGoalError):
            GoalBuilder().with_name("")

    def test_with_name_rejects_non_string(self):
        with self.assertRaises(InvalidGoalError):
            GoalBuilder().with_name(123)

    def test_with_name_rejects_none(self):
        with self.assertRaises(InvalidGoalError):
            GoalBuilder().with_name(None)


class WithDescriptionTests(unittest.TestCase):
    def test_with_description_returns_self_for_chaining(self):
        builder = GoalBuilder()
        result = builder.with_description("Ship v1")
        self.assertIs(result, builder)

    def test_with_description_is_overwritten_not_accumulated(self):
        goal = (
            GoalBuilder().with_description("First").with_description("Second").build()
        )
        self.assertEqual(goal.description, "Second")

    def test_with_description_accepts_empty_string(self):
        goal = GoalBuilder().with_description("").build()
        self.assertEqual(goal.description, "")

    def test_with_description_rejects_non_string(self):
        with self.assertRaises(InvalidGoalError):
            GoalBuilder().with_description(123)

    def test_with_description_rejects_none(self):
        with self.assertRaises(InvalidGoalError):
            GoalBuilder().with_description(None)


class WithStatusTests(unittest.TestCase):
    def test_with_status_returns_self_for_chaining(self):
        builder = GoalBuilder()
        result = builder.with_status(GoalStatus.ACTIVE)
        self.assertIs(result, builder)

    def test_with_status_is_overwritten_not_accumulated(self):
        goal = (
            GoalBuilder()
            .with_status(GoalStatus.ACTIVE)
            .with_status(GoalStatus.PAUSED)
            .build()
        )
        self.assertEqual(goal.status, GoalStatus.PAUSED)

    def test_with_status_rejects_non_status(self):
        with self.assertRaises(InvalidGoalError):
            GoalBuilder().with_status("active")

    def test_with_status_rejects_none(self):
        with self.assertRaises(InvalidGoalError):
            GoalBuilder().with_status(None)

    def test_default_status_is_planning(self):
        goal = GoalBuilder().build()
        self.assertEqual(goal.status, GoalStatus.PLANNING)


class WithPriorityTests(unittest.TestCase):
    def test_with_priority_returns_self_for_chaining(self):
        builder = GoalBuilder()
        result = builder.with_priority(GoalPriority.HIGH)
        self.assertIs(result, builder)

    def test_with_priority_is_overwritten_not_accumulated(self):
        goal = (
            GoalBuilder()
            .with_priority(GoalPriority.HIGH)
            .with_priority(GoalPriority.CRITICAL)
            .build()
        )
        self.assertEqual(goal.priority, GoalPriority.CRITICAL)

    def test_with_priority_rejects_non_priority(self):
        with self.assertRaises(InvalidGoalError):
            GoalBuilder().with_priority("high")

    def test_with_priority_rejects_none(self):
        with self.assertRaises(InvalidGoalError):
            GoalBuilder().with_priority(None)

    def test_default_priority_is_normal(self):
        goal = GoalBuilder().build()
        self.assertEqual(goal.priority, GoalPriority.NORMAL)


class WithMetadataTests(unittest.TestCase):
    def test_with_metadata_returns_self_for_chaining(self):
        builder = GoalBuilder()
        result = builder.with_metadata("k", "v")
        self.assertIs(result, builder)

    def test_with_metadata_populates_extra(self):
        goal = GoalBuilder().with_metadata("region", "US").build()
        self.assertEqual(goal.metadata.extra["region"], "US")

    def test_with_metadata_accumulates_distinct_keys(self):
        goal = GoalBuilder().with_metadata("a", 1).with_metadata("b", 2).build()
        self.assertEqual(dict(goal.metadata.extra), {"a": 1, "b": 2})

    def test_with_metadata_same_key_overwrites(self):
        goal = (
            GoalBuilder()
            .with_metadata("k", "first")
            .with_metadata("k", "second")
            .build()
        )
        self.assertEqual(goal.metadata.extra["k"], "second")

    def test_with_metadata_rejects_empty_key(self):
        with self.assertRaises(InvalidGoalError):
            GoalBuilder().with_metadata("", "v")

    def test_with_metadata_rejects_non_string_key(self):
        with self.assertRaises(InvalidGoalError):
            GoalBuilder().with_metadata(123, "v")

    def test_with_metadata_cannot_set_owner_or_tags(self):
        goal = GoalBuilder().with_metadata("owner", "Jane").build()
        self.assertIsNone(goal.metadata.owner)
        self.assertEqual(goal.metadata.extra["owner"], "Jane")


class BuildTests(unittest.TestCase):
    def test_build_with_no_calls_produces_a_default_goal(self):
        goal = GoalBuilder().build()
        self.assertEqual(goal.name, "")
        self.assertEqual(goal.description, "")
        self.assertEqual(goal.status, GoalStatus.PLANNING)
        self.assertEqual(goal.priority, GoalPriority.NORMAL)

    def test_build_produces_a_fresh_goal_id_each_call(self):
        builder = GoalBuilder().with_name("Grow revenue")
        first = builder.build()
        second = builder.build()
        self.assertNotEqual(first.goal_id, second.goal_id)

    def test_build_after_build_does_not_mutate_the_earlier_goal(self):
        builder = GoalBuilder().with_name("First")
        first = builder.build()
        builder.with_name("Second")
        second = builder.build()
        self.assertEqual(first.name, "First")
        self.assertEqual(second.name, "Second")

    def test_full_chain_produces_the_expected_goal(self):
        goal = (
            GoalBuilder()
            .with_name("Launch product line")
            .with_description("Ship v1")
            .with_status(GoalStatus.ACTIVE)
            .with_priority(GoalPriority.HIGH)
            .with_metadata("k", "v")
            .build()
        )
        self.assertEqual(goal.name, "Launch product line")
        self.assertEqual(goal.description, "Ship v1")
        self.assertEqual(goal.status, GoalStatus.ACTIVE)
        self.assertEqual(goal.priority, GoalPriority.HIGH)
        self.assertEqual(goal.metadata.extra["k"], "v")


if __name__ == "__main__":
    unittest.main()
