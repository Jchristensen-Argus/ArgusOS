"""Unit tests for argus.context.builder.ContextBuilder."""

import unittest

from argus.context.builder import ContextBuilder
from argus.context.context import CognitiveContext
from argus.context.exceptions import InvalidContextError
from argus.context.interfaces import ICognitiveContextBuilder
from argus.reasoning.result import ReasoningResult


class ContextBuilderInterfaceTests(unittest.TestCase):
    def test_context_builder_implements_interface(self):
        self.assertIsInstance(ContextBuilder(), ICognitiveContextBuilder)

    def test_context_builder_is_not_an_iservice(self):
        from argus.lifecycle.interfaces import IService

        self.assertNotIsInstance(ContextBuilder(), IService)


class ContextBuilderEmptyTests(unittest.TestCase):
    def test_build_with_no_calls_returns_empty_context(self):
        context = ContextBuilder().build()
        self.assertIsInstance(context, CognitiveContext)
        self.assertIsNone(context.conversation_id)
        self.assertEqual(context.memory_references, ())
        self.assertEqual(context.knowledge_references, ())
        self.assertEqual(context.reasoning_results, ())
        self.assertEqual(context.decision_references, ())
        self.assertEqual(dict(context.metadata.extra), {})


class ContextBuilderChainingTests(unittest.TestCase):
    def test_every_with_method_returns_the_builder(self):
        builder = ContextBuilder()
        self.assertIs(builder.with_conversation("c1"), builder)
        self.assertIs(builder.with_memory("m1"), builder)
        self.assertIs(builder.with_knowledge("k1"), builder)
        self.assertIs(builder.with_reasoning(ReasoningResult()), builder)
        self.assertIs(builder.with_decision("d1"), builder)
        self.assertIs(builder.with_metadata("key", "value"), builder)

    def test_full_fluent_chain_produces_populated_context(self):
        result = ReasoningResult(reasoning_steps=("step",))
        context = (
            ContextBuilder()
            .with_conversation("conv-1")
            .with_memory("m1")
            .with_memory("m2")
            .with_knowledge("k1")
            .with_reasoning(result)
            .with_decision("d1")
            .with_metadata("foo", "bar")
            .build()
        )
        self.assertEqual(context.conversation_id, "conv-1")
        self.assertEqual(context.memory_references, ("m1", "m2"))
        self.assertEqual(context.knowledge_references, ("k1",))
        self.assertEqual(context.reasoning_results, (result,))
        self.assertEqual(context.decision_references, ("d1",))
        self.assertEqual(dict(context.metadata.extra), {"foo": "bar"})

    def test_memory_references_accumulate_across_calls(self):
        context = ContextBuilder().with_memory("m1").with_memory("m2").with_memory("m3").build()
        self.assertEqual(context.memory_references, ("m1", "m2", "m3"))

    def test_knowledge_references_accumulate_across_calls(self):
        context = ContextBuilder().with_knowledge("k1").with_knowledge("k2").build()
        self.assertEqual(context.knowledge_references, ("k1", "k2"))

    def test_reasoning_results_accumulate_across_calls(self):
        first = ReasoningResult(reasoning_steps=("a",))
        second = ReasoningResult(reasoning_steps=("b",))
        context = ContextBuilder().with_reasoning(first).with_reasoning(second).build()
        self.assertEqual(context.reasoning_results, (first, second))

    def test_decision_references_accumulate_across_calls(self):
        context = ContextBuilder().with_decision("d1").with_decision("d2").build()
        self.assertEqual(context.decision_references, ("d1", "d2"))

    def test_conversation_id_last_call_wins(self):
        context = ContextBuilder().with_conversation("first").with_conversation("second").build()
        self.assertEqual(context.conversation_id, "second")

    def test_metadata_accumulates_distinct_keys(self):
        context = ContextBuilder().with_metadata("a", 1).with_metadata("b", 2).build()
        self.assertEqual(dict(context.metadata.extra), {"a": 1, "b": 2})

    def test_metadata_same_key_last_call_wins(self):
        context = ContextBuilder().with_metadata("k", 1).with_metadata("k", 2).build()
        self.assertEqual(dict(context.metadata.extra), {"k": 2})

    def test_metadata_value_may_be_none(self):
        context = ContextBuilder().with_metadata("k", None).build()
        self.assertEqual(dict(context.metadata.extra), {"k": None})


class ContextBuilderValidationTests(unittest.TestCase):
    def test_with_conversation_rejects_empty_string(self):
        with self.assertRaises(InvalidContextError):
            ContextBuilder().with_conversation("")

    def test_with_conversation_rejects_none(self):
        with self.assertRaises(InvalidContextError):
            ContextBuilder().with_conversation(None)

    def test_with_conversation_rejects_non_string(self):
        with self.assertRaises(InvalidContextError):
            ContextBuilder().with_conversation(123)

    def test_with_memory_rejects_empty_string(self):
        with self.assertRaises(InvalidContextError):
            ContextBuilder().with_memory("")

    def test_with_memory_rejects_none(self):
        with self.assertRaises(InvalidContextError):
            ContextBuilder().with_memory(None)

    def test_with_memory_rejects_non_string(self):
        with self.assertRaises(InvalidContextError):
            ContextBuilder().with_memory(123)

    def test_with_knowledge_rejects_empty_string(self):
        with self.assertRaises(InvalidContextError):
            ContextBuilder().with_knowledge("")

    def test_with_knowledge_rejects_none(self):
        with self.assertRaises(InvalidContextError):
            ContextBuilder().with_knowledge(None)

    def test_with_reasoning_rejects_non_reasoning_result(self):
        with self.assertRaises(InvalidContextError):
            ContextBuilder().with_reasoning("not a reasoning result")

    def test_with_reasoning_rejects_none(self):
        with self.assertRaises(InvalidContextError):
            ContextBuilder().with_reasoning(None)

    def test_with_decision_rejects_empty_string(self):
        with self.assertRaises(InvalidContextError):
            ContextBuilder().with_decision("")

    def test_with_decision_rejects_none(self):
        with self.assertRaises(InvalidContextError):
            ContextBuilder().with_decision(None)

    def test_with_metadata_rejects_empty_key(self):
        with self.assertRaises(InvalidContextError):
            ContextBuilder().with_metadata("", "value")

    def test_with_metadata_rejects_none_key(self):
        with self.assertRaises(InvalidContextError):
            ContextBuilder().with_metadata(None, "value")

    def test_with_metadata_rejects_non_string_key(self):
        with self.assertRaises(InvalidContextError):
            ContextBuilder().with_metadata(5, "value")

    def test_validation_failure_does_not_partially_accumulate(self):
        builder = ContextBuilder().with_memory("m1")
        with self.assertRaises(InvalidContextError):
            builder.with_memory("")
        context = builder.build()
        self.assertEqual(context.memory_references, ("m1",))


class ContextBuilderIndependenceTests(unittest.TestCase):
    def test_build_called_twice_returns_independent_contexts(self):
        builder = ContextBuilder().with_memory("m1")
        first = builder.build()
        builder.with_memory("m2")
        second = builder.build()
        self.assertEqual(first.memory_references, ("m1",))
        self.assertEqual(second.memory_references, ("m1", "m2"))
        self.assertNotEqual(first.context_id, second.context_id)

    def test_mutating_returned_context_sequence_does_not_affect_builder_state(self):
        builder = ContextBuilder().with_memory("m1")
        context = builder.build()
        with self.assertRaises(AttributeError):
            context.memory_references.append("m2")

    def test_each_build_gets_a_fresh_metadata_instance(self):
        builder = ContextBuilder()
        first = builder.build()
        second = builder.build()
        self.assertNotEqual(first.metadata.correlation_id, second.metadata.correlation_id)


if __name__ == "__main__":
    unittest.main()
