"""Unit tests for argus.goal.status.GoalStatus."""

import unittest

from argus.goal import GoalStatus


class MembersTests(unittest.TestCase):
    def test_has_exactly_five_members(self):
        self.assertEqual(
            {member.name for member in GoalStatus},
            {"PLANNING", "ACTIVE", "PAUSED", "COMPLETED", "ABANDONED"},
        )

    def test_values_are_lowercase_strings_matching_member_names(self):
        for member in GoalStatus:
            self.assertEqual(member.value, member.name.lower())


class NoTransitionLogicTests(unittest.TestCase):
    def test_is_a_plain_enum_not_a_str_subclass(self):
        # Mirrors ProjectStatus's (036) / WorkspaceStatus's (037) own
        # shape.
        self.assertFalse(issubclass(GoalStatus, str))

    def test_defines_no_public_methods_beyond_enum_machinery(self):
        public_methods = [
            name
            for name in vars(GoalStatus)
            if not name.startswith("_")
            and callable(getattr(GoalStatus, name))
            and name not in GoalStatus.__members__
        ]
        self.assertEqual(public_methods, [])


class RoundTripTests(unittest.TestCase):
    def test_every_member_round_trips_through_its_own_value(self):
        for member in GoalStatus:
            self.assertIs(GoalStatus(member.value), member)

    def test_members_are_distinct(self):
        values = [member.value for member in GoalStatus]
        self.assertEqual(len(values), len(set(values)))


class EqualityAndIdentityTests(unittest.TestCase):
    def test_same_member_is_identical_across_references(self):
        self.assertIs(GoalStatus.PLANNING, GoalStatus.PLANNING)

    def test_different_members_are_not_equal(self):
        self.assertNotEqual(GoalStatus.PLANNING, GoalStatus.ACTIVE)


if __name__ == "__main__":
    unittest.main()
