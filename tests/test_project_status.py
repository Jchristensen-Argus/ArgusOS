"""Unit tests for argus.project.status.ProjectStatus."""

import unittest

from argus.project import ProjectStatus


class MembersTests(unittest.TestCase):
    def test_has_exactly_five_members(self):
        self.assertEqual(
            {member.name for member in ProjectStatus},
            {"PLANNING", "ACTIVE", "PAUSED", "COMPLETED", "ARCHIVED"},
        )

    def test_values_are_lowercase_strings_matching_member_names(self):
        for member in ProjectStatus:
            self.assertEqual(member.value, member.name.lower())


class NoTransitionLogicTests(unittest.TestCase):
    def test_is_a_plain_enum_not_a_str_subclass(self):
        # Mirrors TaskStatus's (029) / CapabilityExecutionStatus's
        # (034) own shape.
        self.assertFalse(issubclass(ProjectStatus, str))

    def test_defines_no_public_methods_beyond_enum_machinery(self):
        public_methods = [
            name
            for name in vars(ProjectStatus)
            if not name.startswith("_")
            and callable(getattr(ProjectStatus, name))
            and name not in ProjectStatus.__members__
        ]
        self.assertEqual(public_methods, [])


class RoundTripTests(unittest.TestCase):
    def test_every_member_round_trips_through_its_own_value(self):
        for member in ProjectStatus:
            self.assertIs(ProjectStatus(member.value), member)

    def test_members_are_distinct(self):
        values = [member.value for member in ProjectStatus]
        self.assertEqual(len(values), len(set(values)))


class EqualityAndIdentityTests(unittest.TestCase):
    def test_same_member_is_identical_across_references(self):
        self.assertIs(ProjectStatus.PLANNING, ProjectStatus.PLANNING)

    def test_different_members_are_not_equal(self):
        self.assertNotEqual(ProjectStatus.PLANNING, ProjectStatus.ACTIVE)


if __name__ == "__main__":
    unittest.main()
