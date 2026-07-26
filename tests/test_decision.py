"""Unit tests for argus.decision.decision.Decision."""

import unittest
from types import MappingProxyType

from argus.decision.rule import DecisionRule
from argus.reasoning.result import ReasoningResult


def _always_true(results):
    return True


class DecisionTests(unittest.TestCase):
    def test_defaults(self):
        from argus.decision.decision import Decision

        decision = Decision(decision_type="my_decision")
        self.assertEqual(decision.decision_type, "my_decision")
        self.assertTrue(decision.decision_id)
        self.assertEqual(decision.matched_rules, ())
        self.assertEqual(decision.reasoning_results, ())
        self.assertEqual(dict(decision.metadata), {})

    def test_all_fields_set(self):
        from argus.decision.decision import Decision

        rule = DecisionRule(name="r1", predicate=_always_true)
        result = ReasoningResult(matched_entities=(), reasoning_steps=("step",))
        decision = Decision(
            decision_type="my_decision",
            decision_id="d1",
            matched_rules=[rule],
            reasoning_results=[result],
            metadata={"count": 1},
        )
        self.assertEqual(decision.decision_id, "d1")
        self.assertEqual(decision.matched_rules, (rule,))
        self.assertEqual(decision.reasoning_results, (result,))
        self.assertEqual(dict(decision.metadata), {"count": 1})

    def test_id_defaults_to_unique_uuid(self):
        from argus.decision.decision import Decision

        d1 = Decision(decision_type="x")
        d2 = Decision(decision_type="x")
        self.assertNotEqual(d1.decision_id, d2.decision_id)

    def test_sequences_wrapped_as_tuples(self):
        from argus.decision.decision import Decision

        rule = DecisionRule(name="r1", predicate=_always_true)
        decision = Decision(decision_type="x", matched_rules=[rule], reasoning_results=[])
        self.assertIsInstance(decision.matched_rules, tuple)
        self.assertIsInstance(decision.reasoning_results, tuple)

    def test_metadata_wrapped_in_read_only_mapping(self):
        from argus.decision.decision import Decision

        decision = Decision(decision_type="x", metadata={"a": 1})
        self.assertIsInstance(decision.metadata, MappingProxyType)
        with self.assertRaises(TypeError):
            decision.metadata["a"] = 2

    def test_metadata_defensive_copy(self):
        from argus.decision.decision import Decision

        source = {"a": 1}
        decision = Decision(decision_type="x", metadata=source)
        source["a"] = 999
        self.assertEqual(decision.metadata["a"], 1)

    def test_is_immutable(self):
        from argus.decision.decision import Decision

        decision = Decision(decision_type="x")
        with self.assertRaises(Exception):
            decision.decision_type = "y"


if __name__ == "__main__":
    unittest.main()
