"""Unit tests for
argus.capability_executor.status.CapabilityExecutionStatus."""

import unittest

from argus.capability_executor import CapabilityExecutionStatus


class MembersTests(unittest.TestCase):
    def test_has_exactly_five_members(self):
        self.assertEqual(
            {member.name for member in CapabilityExecutionStatus},
            {"PENDING", "RESOLVED", "COMPLETED", "FAILED", "NOT_FOUND"},
        )

    def test_values_are_lowercase_strings_matching_member_names(self):
        for member in CapabilityExecutionStatus:
            self.assertEqual(member.value, member.name.lower())


class NoTransitionLogicTests(unittest.TestCase):
    def test_is_a_plain_enum_not_a_str_subclass(self):
        # "No transition logic" - a plain Enum, not a str subclass,
        # mirroring ExecutionStatus's (032) / TaskStatus's own shape.
        self.assertFalse(issubclass(CapabilityExecutionStatus, str))

    def test_defines_no_public_methods_beyond_enum_machinery(self):
        public_methods = [
            name
            for name in vars(CapabilityExecutionStatus)
            if not name.startswith("_")
            and callable(getattr(CapabilityExecutionStatus, name))
            and name not in CapabilityExecutionStatus.__members__
        ]
        self.assertEqual(public_methods, [])


class RoundTripTests(unittest.TestCase):
    def test_every_member_round_trips_through_its_own_value(self):
        for member in CapabilityExecutionStatus:
            self.assertIs(CapabilityExecutionStatus(member.value), member)

    def test_members_are_distinct(self):
        values = [member.value for member in CapabilityExecutionStatus]
        self.assertEqual(len(values), len(set(values)))


class EqualityAndIdentityTests(unittest.TestCase):
    def test_same_member_is_identical_across_references(self):
        self.assertIs(
            CapabilityExecutionStatus.COMPLETED, CapabilityExecutionStatus.COMPLETED
        )

    def test_different_members_are_not_equal(self):
        self.assertNotEqual(
            CapabilityExecutionStatus.PENDING, CapabilityExecutionStatus.COMPLETED
        )


if __name__ == "__main__":
    unittest.main()
