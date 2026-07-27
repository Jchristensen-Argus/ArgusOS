"""Unit tests for argus.policy.status.PolicyStatus."""

import unittest

from argus.policy import PolicyStatus


class MembersTests(unittest.TestCase):
    def test_has_exactly_three_members(self):
        self.assertEqual(
            {member.name for member in PolicyStatus},
            {"ACTIVE", "INACTIVE", "ARCHIVED"},
        )

    def test_values_are_lowercase_strings_matching_member_names(self):
        for member in PolicyStatus:
            self.assertEqual(member.value, member.name.lower())


class NoTransitionLogicTests(unittest.TestCase):
    def test_is_a_plain_enum_not_a_str_subclass(self):
        self.assertFalse(issubclass(PolicyStatus, str))

    def test_defines_no_public_methods_beyond_enum_machinery(self):
        public_methods = [
            name
            for name in vars(PolicyStatus)
            if not name.startswith("_")
            and callable(getattr(PolicyStatus, name))
            and name not in PolicyStatus.__members__
        ]
        self.assertEqual(public_methods, [])


class RoundTripTests(unittest.TestCase):
    def test_every_member_round_trips_through_its_own_value(self):
        for member in PolicyStatus:
            self.assertIs(PolicyStatus(member.value), member)

    def test_members_are_distinct(self):
        values = [member.value for member in PolicyStatus]
        self.assertEqual(len(values), len(set(values)))


class EqualityAndIdentityTests(unittest.TestCase):
    def test_same_member_is_identical_across_references(self):
        self.assertIs(PolicyStatus.ACTIVE, PolicyStatus.ACTIVE)

    def test_different_members_are_not_equal(self):
        self.assertNotEqual(PolicyStatus.ACTIVE, PolicyStatus.ARCHIVED)


if __name__ == "__main__":
    unittest.main()
