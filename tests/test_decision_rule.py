"""Unit tests for argus.decision.rule.DecisionRule."""

import unittest

from argus.decision.rule import DecisionRule


def _always_true(results):
    return True


class DecisionRuleTests(unittest.TestCase):
    def test_defaults(self):
        rule = DecisionRule(name="my_rule", predicate=_always_true)
        self.assertEqual(rule.name, "my_rule")
        self.assertIs(rule.predicate, _always_true)
        self.assertEqual(rule.priority, 0)
        self.assertTrue(rule.id)
        self.assertEqual(rule.description, "")

    def test_all_fields_set(self):
        rule = DecisionRule(
            name="my_rule",
            predicate=_always_true,
            priority=5,
            id="rule-1",
            description="Always matches.",
        )
        self.assertEqual(rule.name, "my_rule")
        self.assertIs(rule.predicate, _always_true)
        self.assertEqual(rule.priority, 5)
        self.assertEqual(rule.id, "rule-1")
        self.assertEqual(rule.description, "Always matches.")

    def test_id_defaults_to_unique_uuid(self):
        rule_a = DecisionRule(name="a", predicate=_always_true)
        rule_b = DecisionRule(name="b", predicate=_always_true)
        self.assertNotEqual(rule_a.id, rule_b.id)

    def test_is_immutable(self):
        rule = DecisionRule(name="my_rule", predicate=_always_true)
        with self.assertRaises(Exception):
            rule.name = "renamed"

    def test_predicate_is_callable_with_results(self):
        def rule_predicate(reasoning_results):
            return len(reasoning_results) > 0

        rule = DecisionRule(name="my_rule", predicate=rule_predicate)
        self.assertTrue(rule.predicate(("fake_result",)))
        self.assertFalse(rule.predicate(()))

    def test_equality(self):
        rule_a = DecisionRule(name="a", predicate=_always_true, id="same-id")
        rule_b = DecisionRule(name="a", predicate=_always_true, id="same-id")
        self.assertEqual(rule_a, rule_b)

    def test_inequality_by_id(self):
        rule_a = DecisionRule(name="a", predicate=_always_true, id="id-1")
        rule_b = DecisionRule(name="a", predicate=_always_true, id="id-2")
        self.assertNotEqual(rule_a, rule_b)


if __name__ == "__main__":
    unittest.main()
