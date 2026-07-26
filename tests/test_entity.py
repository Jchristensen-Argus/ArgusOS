"""Unit tests for argus.knowledge_graph.entity.Entity."""

import unittest
from types import MappingProxyType

from argus.knowledge_graph import Entity


class EntityTests(unittest.TestCase):
    def test_defaults(self):
        entity = Entity(entity_type="person", name="Alice")

        self.assertTrue(entity.id)
        self.assertEqual(dict(entity.attributes), {})

    def test_ids_are_unique(self):
        first = Entity(entity_type="person", name="Alice")
        second = Entity(entity_type="person", name="Bob")

        self.assertNotEqual(first.id, second.id)

    def test_attributes_is_an_immutable_mapping(self):
        entity = Entity(entity_type="person", name="Alice", attributes={"age": 30})

        self.assertIsInstance(entity.attributes, MappingProxyType)
        with self.assertRaises(TypeError):
            entity.attributes["age"] = 31

    def test_is_frozen(self):
        entity = Entity(entity_type="person", name="Alice")

        with self.assertRaises(Exception):
            entity.name = "Changed"

    def test_explicit_id_is_preserved(self):
        entity = Entity(id="custom-id", entity_type="person", name="Alice")

        self.assertEqual(entity.id, "custom-id")

    def test_entity_type_and_name_are_preserved(self):
        entity = Entity(entity_type="workflow", name="Onboarding")

        self.assertEqual(entity.entity_type, "workflow")
        self.assertEqual(entity.name, "Onboarding")


if __name__ == "__main__":
    unittest.main()
