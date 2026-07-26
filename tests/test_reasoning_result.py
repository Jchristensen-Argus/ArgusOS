"""Unit tests for argus.reasoning.result.ReasoningResult."""

import unittest
from types import MappingProxyType

from argus.knowledge_graph.entity import Entity
from argus.knowledge_graph.relationship import Relationship
from argus.reasoning.result import ReasoningResult


class ReasoningResultTests(unittest.TestCase):
    def test_defaults(self):
        result = ReasoningResult()
        self.assertEqual(result.matched_entities, ())
        self.assertEqual(result.matched_relationships, ())
        self.assertEqual(result.reasoning_steps, ())
        self.assertEqual(dict(result.metadata), {})

    def test_all_fields_set(self):
        e1 = Entity(entity_type="person", name="Alice", id="e1")
        r1 = Relationship(source_entity_id="e1", target_entity_id="e1", relationship_type="knows", id="r1")
        result = ReasoningResult(
            matched_entities=[e1],
            matched_relationships=[r1],
            reasoning_steps=["step one"],
            metadata={"count": 1},
        )
        self.assertEqual(result.matched_entities, (e1,))
        self.assertEqual(result.matched_relationships, (r1,))
        self.assertEqual(result.reasoning_steps, ("step one",))
        self.assertEqual(dict(result.metadata), {"count": 1})

    def test_sequences_wrapped_as_tuples(self):
        e1 = Entity(entity_type="person", name="Alice", id="e1")
        result = ReasoningResult(matched_entities=[e1], reasoning_steps=["a", "b"])
        self.assertIsInstance(result.matched_entities, tuple)
        self.assertIsInstance(result.matched_relationships, tuple)
        self.assertIsInstance(result.reasoning_steps, tuple)

    def test_metadata_wrapped_in_read_only_mapping(self):
        result = ReasoningResult(metadata={"a": 1})
        self.assertIsInstance(result.metadata, MappingProxyType)
        with self.assertRaises(TypeError):
            result.metadata["a"] = 2

    def test_metadata_defensive_copy(self):
        source = {"a": 1}
        result = ReasoningResult(metadata=source)
        source["a"] = 999
        self.assertEqual(result.metadata["a"], 1)

    def test_is_immutable(self):
        result = ReasoningResult()
        with self.assertRaises(Exception):
            result.matched_entities = ()

    def test_no_confidence_or_explanation_fields(self):
        # Descriptive-only discipline: ReasoningResult exposes exactly
        # the four fields the work order names, nothing else.
        result = ReasoningResult()
        field_names = {f for f in result.__dataclass_fields__}
        self.assertEqual(
            field_names,
            {"matched_entities", "matched_relationships", "reasoning_steps", "metadata"},
        )


if __name__ == "__main__":
    unittest.main()
