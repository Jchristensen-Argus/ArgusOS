"""Unit tests for argus.decision.status.DecisionRecordStatus."""

import unittest

from argus.decision import DecisionRecordStatus


class MembersTests(unittest.TestCase):
    def test_has_exactly_five_members(self):
        self.assertEqual(
            {member.name for member in DecisionRecordStatus},
            {"PENDING", "IN_REVIEW", "APPROVED", "REJECTED", "ARCHIVED"},
        )

    def test_values_are_lowercase_strings_matching_member_names(self):
        for member in DecisionRecordStatus:
            self.assertEqual(member.value, member.name.lower())


class NoTransitionLogicTests(unittest.TestCase):
    def test_is_a_plain_enum_not_a_str_subclass(self):
        self.assertFalse(issubclass(DecisionRecordStatus, str))

    def test_defines_no_public_methods_beyond_enum_machinery(self):
        public_methods = [
            name
            for name in vars(DecisionRecordStatus)
            if not name.startswith("_")
            and callable(getattr(DecisionRecordStatus, name))
            and name not in DecisionRecordStatus.__members__
        ]
        self.assertEqual(public_methods, [])


class RoundTripTests(unittest.TestCase):
    def test_every_member_round_trips_through_its_own_value(self):
        for member in DecisionRecordStatus:
            self.assertIs(DecisionRecordStatus(member.value), member)

    def test_members_are_distinct(self):
        values = [member.value for member in DecisionRecordStatus]
        self.assertEqual(len(values), len(set(values)))


class EqualityAndIdentityTests(unittest.TestCase):
    def test_same_member_is_identical_across_references(self):
        self.assertIs(DecisionRecordStatus.PENDING, DecisionRecordStatus.PENDING)

    def test_different_members_are_not_equal(self):
        self.assertNotEqual(DecisionRecordStatus.PENDING, DecisionRecordStatus.APPROVED)


if __name__ == "__main__":
    unittest.main()
