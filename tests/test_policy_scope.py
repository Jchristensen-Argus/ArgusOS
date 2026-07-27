"""Unit tests for argus.policy.scope.PolicyScope."""

import unittest

from argus.policy import PolicyScope


class MembersTests(unittest.TestCase):
    def test_has_exactly_seven_members(self):
        self.assertEqual(
            {member.name for member in PolicyScope},
            {"GLOBAL", "WORKSPACE", "PROJECT", "GOAL", "PLAN", "TASK", "CAPABILITY"},
        )

    def test_values_are_lowercase_strings_matching_member_names(self):
        for member in PolicyScope:
            self.assertEqual(member.value, member.name.lower())

    def test_member_order_mirrors_organizational_hierarchy(self):
        # GLOBAL, WORKSPACE, PROJECT, GOAL, PLAN, TASK, CAPABILITY -
        # presentational only, no behavioral significance. See
        # scope.py's own module docstring.
        self.assertEqual(
            [member.name for member in PolicyScope],
            ["GLOBAL", "WORKSPACE", "PROJECT", "GOAL", "PLAN", "TASK", "CAPABILITY"],
        )


class NoInheritanceOrEvaluationLogicTests(unittest.TestCase):
    def test_is_a_plain_enum_not_a_str_subclass(self):
        self.assertFalse(issubclass(PolicyScope, str))

    def test_is_not_an_intenum_or_other_ordered_variant(self):
        self.assertFalse(issubclass(PolicyScope, int))

    def test_members_do_not_support_less_than_comparison(self):
        with self.assertRaises(TypeError):
            PolicyScope.GLOBAL < PolicyScope.TASK

    def test_members_do_not_support_greater_than_comparison(self):
        with self.assertRaises(TypeError):
            PolicyScope.CAPABILITY > PolicyScope.GLOBAL

    def test_defines_no_public_methods_beyond_enum_machinery(self):
        public_methods = [
            name
            for name in vars(PolicyScope)
            if not name.startswith("_")
            and callable(getattr(PolicyScope, name))
            and name not in PolicyScope.__members__
        ]
        self.assertEqual(public_methods, [])


class RoundTripTests(unittest.TestCase):
    def test_every_member_round_trips_through_its_own_value(self):
        for member in PolicyScope:
            self.assertIs(PolicyScope(member.value), member)

    def test_members_are_distinct(self):
        values = [member.value for member in PolicyScope]
        self.assertEqual(len(values), len(set(values)))


class EqualityAndIdentityTests(unittest.TestCase):
    def test_same_member_is_identical_across_references(self):
        self.assertIs(PolicyScope.GLOBAL, PolicyScope.GLOBAL)

    def test_different_members_are_not_equal(self):
        self.assertNotEqual(PolicyScope.GLOBAL, PolicyScope.TASK)


if __name__ == "__main__":
    unittest.main()
