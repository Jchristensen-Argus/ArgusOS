"""Unit tests for argus.context.context.CognitiveContext."""

import dataclasses
import unittest
from datetime import datetime, timezone

from argus.context.context import CognitiveContext
from argus.context.metadata import ContextMetadata
from argus.reasoning.result import ReasoningResult


def _fixed_metadata(correlation_id="corr-1"):
    return ContextMetadata(
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        version="1.0",
        correlation_id=correlation_id,
        extra={},
    )


class CognitiveContextEmptyTests(unittest.TestCase):
    def test_empty_context_defaults(self):
        context = CognitiveContext()
        self.assertIsNone(context.conversation_id)
        self.assertEqual(context.memory_references, ())
        self.assertEqual(context.knowledge_references, ())
        self.assertEqual(context.reasoning_results, ())
        self.assertEqual(context.decision_references, ())
        self.assertIsInstance(context.metadata, ContextMetadata)

    def test_empty_context_has_generated_context_id(self):
        context = CognitiveContext()
        self.assertIsInstance(context.context_id, str)
        self.assertTrue(context.context_id)

    def test_default_context_id_is_unique_per_instance(self):
        first = CognitiveContext()
        second = CognitiveContext()
        self.assertNotEqual(first.context_id, second.context_id)

    def test_default_metadata_is_independent_per_instance(self):
        first = CognitiveContext()
        second = CognitiveContext()
        self.assertNotEqual(first.metadata.correlation_id, second.metadata.correlation_id)


class CognitiveContextPopulatedTests(unittest.TestCase):
    def test_all_fields_set(self):
        reasoning_result = ReasoningResult(reasoning_steps=("step-1",))
        context = CognitiveContext(
            context_id="ctx-1",
            conversation_id="conv-1",
            memory_references=["m1", "m2"],
            knowledge_references=["k1"],
            reasoning_results=[reasoning_result],
            decision_references=["d1", "d2"],
            metadata=_fixed_metadata(),
        )
        self.assertEqual(context.context_id, "ctx-1")
        self.assertEqual(context.conversation_id, "conv-1")
        self.assertEqual(context.memory_references, ("m1", "m2"))
        self.assertEqual(context.knowledge_references, ("k1",))
        self.assertEqual(context.reasoning_results, (reasoning_result,))
        self.assertEqual(context.decision_references, ("d1", "d2"))
        self.assertEqual(context.metadata, _fixed_metadata())

    def test_sequence_fields_are_wrapped_in_tuples(self):
        context = CognitiveContext(
            memory_references=["m1"],
            knowledge_references=["k1"],
            reasoning_results=[ReasoningResult()],
            decision_references=["d1"],
        )
        self.assertIsInstance(context.memory_references, tuple)
        self.assertIsInstance(context.knowledge_references, tuple)
        self.assertIsInstance(context.reasoning_results, tuple)
        self.assertIsInstance(context.decision_references, tuple)

    def test_sequence_fields_defensive_copy_not_shared_with_caller(self):
        source = ["m1"]
        context = CognitiveContext(memory_references=source)
        source.append("m2")
        self.assertEqual(context.memory_references, ("m1",))


class CognitiveContextImmutabilityTests(unittest.TestCase):
    def test_cannot_reassign_fields(self):
        context = CognitiveContext()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            context.conversation_id = "changed"
        with self.assertRaises(dataclasses.FrozenInstanceError):
            context.memory_references = ("m1",)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            context.reasoning_results = ()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            context.metadata = ContextMetadata()

    def test_memory_references_tuple_cannot_be_mutated_in_place(self):
        context = CognitiveContext(memory_references=["m1"])
        with self.assertRaises(AttributeError):
            context.memory_references.append("m2")


class CognitiveContextEqualityTests(unittest.TestCase):
    def test_equal_when_every_field_matches(self):
        result = ReasoningResult(reasoning_steps=("step",))
        first = CognitiveContext(
            context_id="same",
            conversation_id="c",
            memory_references=["m1"],
            reasoning_results=[result],
            metadata=_fixed_metadata(),
        )
        second = CognitiveContext(
            context_id="same",
            conversation_id="c",
            memory_references=["m1"],
            reasoning_results=[result],
            metadata=_fixed_metadata(),
        )
        self.assertEqual(first, second)

    def test_not_equal_when_context_id_differs(self):
        first = CognitiveContext(context_id="a", conversation_id="c", metadata=_fixed_metadata())
        second = CognitiveContext(context_id="b", conversation_id="c", metadata=_fixed_metadata())
        self.assertNotEqual(first, second)

    def test_not_equal_when_conversation_id_differs(self):
        first = CognitiveContext(context_id="same", conversation_id="c1", metadata=_fixed_metadata())
        second = CognitiveContext(context_id="same", conversation_id="c2", metadata=_fixed_metadata())
        self.assertNotEqual(first, second)

    def test_not_equal_when_metadata_differs(self):
        first = CognitiveContext(context_id="same", metadata=_fixed_metadata("corr-1"))
        second = CognitiveContext(context_id="same", metadata=_fixed_metadata("corr-2"))
        self.assertNotEqual(first, second)

    def test_two_default_constructed_contexts_are_not_equal(self):
        # Both context_id (uuid4) and metadata.correlation_id (uuid4)
        # are freshly generated per instance, so two contexts built
        # with no explicit arguments are never equal to each other.
        first = CognitiveContext()
        second = CognitiveContext()
        self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
