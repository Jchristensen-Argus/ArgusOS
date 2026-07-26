"""Unit tests for argus.knowledge_graph.relationship.Relationship."""

import unittest
from types import MappingProxyType

from argus.knowledge_graph import Relationship


class RelationshipTests(unittest.TestCase):
    def test_defaults(self):
        relationship = Relationship(
            source_entity_id="a", target_entity_id="b", relationship_type="knows"
        )

        self.assertTrue(relationship.id)
        self.assertEqual(dict(relationship.attributes), {})

    def test_ids_are_unique(self):
        first = Relationship(source_entity_id="a", target_entity_id="b", relationship_type="knows")
        second = Relationship(source_entity_id="a", target_entity_id="b", relationship_type="knows")

        self.assertNotEqual(first.id, second.id)

    def test_attributes_is_an_immutable_mapping(self):
        relationship = Relationship(
            source_entity_id="a",
            target_entity_id="b",
            relationship_type="knows",
            attributes={"since": 2020},
        )

        self.assertIsInstance(relationship.attributes, MappingProxyType)
        with self.assertRaises(TypeError):
            relationship.attributes["since"] = 2021

    def test_is_frozen(self):
        relationship = Relationship(source_entity_id="a", target_entity_id="b", relationship_type="knows")

        with self.assertRaises(Exception):
            relationship.relationship_type = "changed"

    def test_explicit_id_is_preserved(self):
        relationship = Relationship(
            id="custom-id", source_entity_id="a", target_entity_id="b", relationship_type="knows"
        )

        self.assertEqual(relationship.id, "custom-id")

    def test_fields_are_preserved(self):
        relationship = Relationship(source_entity_id="a", target_entity_id="b", relationship_type="knows")

        self.assertEqual(relationship.source_entity_id, "a")
        self.assertEqual(relationship.target_entity_id, "b")
        self.assertEqual(relationship.relationship_type, "knows")

    def test_self_loop_is_permitted(self):
        relationship = Relationship(source_entity_id="a", target_entity_id="a", relationship_type="self")

        self.assertEqual(relationship.source_entity_id, relationship.target_entity_id)


if __name__ == "__main__":
    unittest.main()
