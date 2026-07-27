"""Unit tests for argus.decision.priority.DecisionRecordPriority."""

import unittest

from argus.decision import DecisionRecordPriority


class MembersTests(unittest.TestCase):
    def test_has_exactly_four_members(self):
        self.assertEqual(
            {member.name for member in DecisionRecordPriority},
            {"LOW", "NORMAL", "HIGH", "CRITICAL"},
        )

    def test_values_are_lowercase_strings_matching_member_names(self):
        for member in DecisionRecordPriority:
            self.assertEqual(member.value, member.name.lower())


class NoOrderingBehaviorTests(unittest.TestCase):
    def test_is_a_plain_enum_not_a_str_subclass(self):
        self.assertFalse(issubclass(DecisionRecordPriority, str))

    def test_is_not_an_intenum_or_other_ordered_variant(self):
        # "No ordering behavior" - a plain Enum, not IntEnum or any
        # subclass that would grant ordering through inherited
        # comparison operators. See priority.py's own module
        # docstring.
        self.assertFalse(issubclass(DecisionRecordPriority, int))

    def test_members_do_not_support_less_than_comparison(self):
        with self.assertRaises(TypeError):
            DecisionRecordPriority.LOW < DecisionRecordPriority.HIGH

    def test_members_do_not_support_greater_than_comparison(self):
        with self.assertRaises(TypeError):
            DecisionRecordPriority.CRITICAL > DecisionRecordPriority.LOW

    def test_defines_no_public_methods_beyond_enum_machinery(self):
        public_methods = [
            name
            for name in vars(DecisionRecordPriority)
            if not name.startswith("_")
            and callable(getattr(DecisionRecordPriority, name))
            and name not in DecisionRecordPriority.__members__
        ]
        self.assertEqual(public_methods, [])


class RoundTripTests(unittest.TestCase):
    def test_every_member_round_trips_through_its_own_value(self):
        for member in DecisionRecordPriority:
            self.assertIs(DecisionRecordPriority(member.value), member)

    def test_members_are_distinct(self):
        values = [member.value for member in DecisionRecordPriority]
        self.assertEqual(len(values), len(set(values)))


class EqualityAndIdentityTests(unittest.TestCase):
    def test_same_member_is_identical_across_references(self):
        self.assertIs(DecisionRecordPriority.NORMAL, DecisionRecordPriority.NORMAL)

    def test_different_members_are_not_equal(self):
        self.assertNotEqual(DecisionRecordPriority.LOW, DecisionRecordPriority.HIGH)


if __name__ == "__main__":
    unittest.main()
