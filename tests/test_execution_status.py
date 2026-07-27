"""Unit tests for argus.execution_engine.status.ExecutionStatus."""

import unittest

from argus.execution_engine import ExecutionStatus


class MembersTests(unittest.TestCase):
    def test_has_exactly_five_members(self):
        self.assertEqual(
            {member.name for member in ExecutionStatus},
            {"PENDING", "RUNNING", "COMPLETED", "FAILED", "CANCELLED"},
        )

    def test_values_are_lowercase_strings_matching_member_names(self):
        for member in ExecutionStatus:
            self.assertEqual(member.value, member.name.lower())


class NoTransitionLogicTests(unittest.TestCase):
    def test_is_a_plain_enum_not_a_str_subclass(self):
        # "No transition logic" - a plain Enum, not a str subclass,
        # mirroring TaskStatus's (029) / PlanStatus's own shape.
        self.assertFalse(issubclass(ExecutionStatus, str))

    def test_defines_no_public_methods_beyond_enum_machinery(self):
        public_methods = [
            name
            for name in vars(ExecutionStatus)
            if not name.startswith("_")
            and callable(getattr(ExecutionStatus, name))
            and name not in ExecutionStatus.__members__
        ]
        self.assertEqual(public_methods, [])


class RoundTripTests(unittest.TestCase):
    def test_every_member_round_trips_through_its_own_value(self):
        for member in ExecutionStatus:
            self.assertIs(ExecutionStatus(member.value), member)

    def test_members_are_distinct(self):
        values = [member.value for member in ExecutionStatus]
        self.assertEqual(len(values), len(set(values)))


class EqualityAndIdentityTests(unittest.TestCase):
    def test_same_member_is_identical_across_references(self):
        self.assertIs(ExecutionStatus.COMPLETED, ExecutionStatus.COMPLETED)

    def test_different_members_are_not_equal(self):
        self.assertNotEqual(ExecutionStatus.PENDING, ExecutionStatus.COMPLETED)


if __name__ == "__main__":
    unittest.main()
