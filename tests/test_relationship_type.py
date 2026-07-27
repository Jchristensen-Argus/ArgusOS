"""Unit tests for argus.task_relationship.relationship_type.RelationshipType."""

import unittest
from enum import Enum

from argus.task_relationship import RelationshipType


class EnumerationCorrectnessTests(unittest.TestCase):
    def test_is_a_plain_enum_not_a_str_subclass(self):
        # Mirrors TaskStatus (029)/PlanStatus's own shape - a plain
        # Enum, not a str subclass.
        self.assertTrue(issubclass(RelationshipType, Enum))
        self.assertFalse(issubclass(RelationshipType, str))

    def test_exactly_four_members(self):
        self.assertEqual(len(RelationshipType), 4)

    def test_member_names(self):
        self.assertEqual(
            {member.name for member in RelationshipType},
            {"PRECEDES", "FOLLOWS", "RELATED", "BLOCKS"},
        )

    def test_member_values(self):
        self.assertEqual(RelationshipType.PRECEDES.value, "precedes")
        self.assertEqual(RelationshipType.FOLLOWS.value, "follows")
        self.assertEqual(RelationshipType.RELATED.value, "related")
        self.assertEqual(RelationshipType.BLOCKS.value, "blocks")

    def test_values_are_all_distinct(self):
        values = [member.value for member in RelationshipType]
        self.assertEqual(len(values), len(set(values)))


class NoInterpretationTests(unittest.TestCase):
    def test_relationship_type_has_no_methods_beyond_enum_machinery(self):
        # "Do not interpret them. Do not infer behavior." -
        # RelationshipType is a bare enumeration with no methods of
        # its own beyond what Enum itself provides.
        own_attrs = set(vars(RelationshipType)) - set(vars(Enum))
        member_names = {member.name for member in RelationshipType}
        suspicious = {
            name
            for name in own_attrs
            if not name.startswith("_") and name not in member_names
        }
        self.assertEqual(suspicious, set())


class EqualityAndIdentityTests(unittest.TestCase):
    def test_members_are_singletons(self):
        self.assertIs(RelationshipType.PRECEDES, RelationshipType("precedes"))

    def test_different_members_are_not_equal(self):
        self.assertNotEqual(RelationshipType.PRECEDES, RelationshipType.FOLLOWS)


if __name__ == "__main__":
    unittest.main()
