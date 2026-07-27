"""Unit tests for argus.automation.trigger.AutomationTrigger."""

import unittest

from argus.automation import AutomationTrigger


class MembersTests(unittest.TestCase):
    def test_has_exactly_four_members(self):
        self.assertEqual(
            {member.name for member in AutomationTrigger},
            {"MANUAL", "SCHEDULE", "EVENT", "CONDITION"},
        )

    def test_values_are_lowercase_strings_matching_member_names(self):
        for member in AutomationTrigger:
            self.assertEqual(member.value, member.name.lower())

    def test_member_order_places_manual_first(self):
        self.assertEqual(
            [member.name for member in AutomationTrigger],
            ["MANUAL", "SCHEDULE", "EVENT", "CONDITION"],
        )


class NoSchedulingEventOrConditionLogicTests(unittest.TestCase):
    def test_is_a_plain_enum_not_a_str_subclass(self):
        self.assertFalse(issubclass(AutomationTrigger, str))

    def test_is_not_an_intenum_or_other_ordered_variant(self):
        self.assertFalse(issubclass(AutomationTrigger, int))

    def test_members_do_not_support_less_than_comparison(self):
        with self.assertRaises(TypeError):
            AutomationTrigger.MANUAL < AutomationTrigger.EVENT

    def test_members_do_not_support_greater_than_comparison(self):
        with self.assertRaises(TypeError):
            AutomationTrigger.CONDITION > AutomationTrigger.MANUAL

    def test_defines_no_public_methods_beyond_enum_machinery(self):
        public_methods = [
            name
            for name in vars(AutomationTrigger)
            if not name.startswith("_")
            and callable(getattr(AutomationTrigger, name))
            and name not in AutomationTrigger.__members__
        ]
        self.assertEqual(public_methods, [])


class RoundTripTests(unittest.TestCase):
    def test_every_member_round_trips_through_its_own_value(self):
        for member in AutomationTrigger:
            self.assertIs(AutomationTrigger(member.value), member)

    def test_members_are_distinct(self):
        values = [member.value for member in AutomationTrigger]
        self.assertEqual(len(values), len(set(values)))


class EqualityAndIdentityTests(unittest.TestCase):
    def test_same_member_is_identical_across_references(self):
        self.assertIs(AutomationTrigger.MANUAL, AutomationTrigger.MANUAL)

    def test_different_members_are_not_equal(self):
        self.assertNotEqual(AutomationTrigger.MANUAL, AutomationTrigger.EVENT)


if __name__ == "__main__":
    unittest.main()
