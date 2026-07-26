"""Unit tests for argus.reasoning.query.ReasoningQuery."""

import unittest
from types import MappingProxyType

from argus.reasoning.query import ReasoningQuery


class ReasoningQueryTests(unittest.TestCase):
    def test_defaults(self):
        query = ReasoningQuery()
        self.assertIsNone(query.entity_type)
        self.assertIsNone(query.relationship_type)
        self.assertIsNone(query.entity_id)
        self.assertEqual(query.depth, 1)
        self.assertEqual(dict(query.filters), {})

    def test_all_fields_set(self):
        query = ReasoningQuery(
            entity_type="person",
            relationship_type="knows",
            entity_id="e1",
            depth=3,
            filters={"active": True},
        )
        self.assertEqual(query.entity_type, "person")
        self.assertEqual(query.relationship_type, "knows")
        self.assertEqual(query.entity_id, "e1")
        self.assertEqual(query.depth, 3)
        self.assertEqual(dict(query.filters), {"active": True})

    def test_filters_wrapped_in_read_only_mapping(self):
        query = ReasoningQuery(filters={"a": 1})
        self.assertIsInstance(query.filters, MappingProxyType)
        with self.assertRaises(TypeError):
            query.filters["a"] = 2

    def test_filters_defensive_copy(self):
        source = {"a": 1}
        query = ReasoningQuery(filters=source)
        source["a"] = 999
        self.assertEqual(query.filters["a"], 1)

    def test_is_immutable(self):
        query = ReasoningQuery(entity_id="e1")
        with self.assertRaises(Exception):
            query.entity_id = "e2"

    def test_equality(self):
        q1 = ReasoningQuery(entity_id="e1", depth=2, filters={"a": 1})
        q2 = ReasoningQuery(entity_id="e1", depth=2, filters={"a": 1})
        self.assertEqual(q1, q2)

    def test_inequality(self):
        q1 = ReasoningQuery(entity_id="e1")
        q2 = ReasoningQuery(entity_id="e2")
        self.assertNotEqual(q1, q2)


if __name__ == "__main__":
    unittest.main()
