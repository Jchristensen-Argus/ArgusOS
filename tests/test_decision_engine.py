"""Unit tests for argus.decision.engine.DecisionEngine."""

import logging
import unittest

from argus.decision import DecisionEngine, DecisionRule
from argus.decision.exceptions import (
    DecisionError,
    DuplicateRuleError,
    InvalidDecisionInputError,
    InvalidDecisionRuleError,
    RuleEvaluationError,
    RuleNotFoundError,
)
from argus.events import EventType, InMemoryEventBus
from argus.knowledge_graph import Entity, KnowledgeGraph, Relationship
from argus.lifecycle import LifecycleState
from argus.memory import MemoryService
from argus.memory.interfaces import IMemoryStorage
from argus.memory_integration import MemoryIntegration
from argus.reasoning import ReasoningEngine
from argus.reasoning.result import ReasoningResult


def _silent_logger() -> logging.Logger:
    logger = logging.getLogger("test_decision_engine")
    logger.addHandler(logging.NullHandler())
    logger.propagate = False
    return logger


class _InMemoryStorage(IMemoryStorage):
    """A minimal, fully in-memory IMemoryStorage stand-in - no disk
    I/O of any kind - matching argus/tests/test_memory_integration.py's
    and argus/tests/test_reasoning_engine.py's own precedent."""

    def __init__(self):
        self._records = []

    def load(self):
        return tuple(self._records)

    def save(self, records):
        self._records = list(records)


def _matcher(matched):
    """Builds a predicate that always returns `matched`, ignoring
    input - useful when the specific ReasoningResult content is
    irrelevant to the test."""

    def predicate(reasoning_results):
        return matched

    return predicate


def _has_any_matched_entities(reasoning_results):
    return any(result.matched_entities for result in reasoning_results)


def _raises(reasoning_results):
    raise ValueError("simulated predicate failure")


class DecisionEngineTestCase(unittest.TestCase):
    """
    Base fixture: a real ReasoningEngine, KnowledgeGraph, and
    MemoryIntegration, wired exactly as bootstrap.py wires them - used
    to produce genuine ReasoningResult objects to evaluate, matching
    argus/tests/test_reasoning_engine.py's own precedent for testing
    a package that consumes another package's real output type
    (rather than a hand-built stub).
    """

    def setUp(self):
        self.event_bus = InMemoryEventBus(logger=_silent_logger())
        self.graph = KnowledgeGraph(event_bus=self.event_bus)
        self.memory_service = MemoryService(storage=_InMemoryStorage(), event_bus=self.event_bus)
        self.memory_integration = MemoryIntegration(
            memory_service=self.memory_service, knowledge_graph=self.graph, event_bus=self.event_bus
        )
        self.reasoning_engine = ReasoningEngine(
            knowledge_graph=self.graph, memory_integration=self.memory_integration, event_bus=self.event_bus
        )
        self.engine = DecisionEngine(reasoning_engine=self.reasoning_engine, event_bus=self.event_bus)

        self.alice = Entity(entity_type="person", name="Alice", id="alice")
        self.bob = Entity(entity_type="person", name="Bob", id="bob")
        self.graph.add_entity(self.alice)
        self.graph.add_entity(self.bob)
        self.graph.add_relationship(
            Relationship(source_entity_id="alice", target_entity_id="bob", relationship_type="knows", id="r1")
        )

        self.result_with_matches = self.reasoning_engine.neighbors("alice")
        self.result_without_matches = ReasoningResult(
            matched_entities=(), matched_relationships=(), reasoning_steps=(), metadata={}
        )

    def _events(self, *event_types):
        received = []
        for event_type in event_types:
            self.event_bus.subscribe(event_type, received.append)
        return received


# -- Lifecycle -------------------------------------------------------------


class LifecycleTests(DecisionEngineTestCase):
    def test_initial_state_is_created(self):
        self.assertEqual(self.engine.status(), LifecycleState.CREATED)

    def test_initialize_start_stop_transitions(self):
        self.engine.initialize()
        self.assertEqual(self.engine.status(), LifecycleState.INITIALIZING)
        self.engine.start()
        self.assertEqual(self.engine.status(), LifecycleState.RUNNING)
        self.engine.stop()
        self.assertEqual(self.engine.status(), LifecycleState.STOPPED)

    def test_initialize_twice_raises(self):
        self.engine.initialize()
        with self.assertRaises(DecisionError):
            self.engine.initialize()

    def test_start_before_initialize_raises(self):
        with self.assertRaises(DecisionError):
            self.engine.start()

    def test_stop_before_start_raises(self):
        self.engine.initialize()
        with self.assertRaises(DecisionError):
            self.engine.stop()

    def test_public_methods_work_without_starting(self):
        # None of DecisionEngine's six public methods are gated on
        # RUNNING - see interfaces.py's Architectural Note.
        self.assertEqual(self.engine.status(), LifecycleState.CREATED)
        rule = DecisionRule(name="always", predicate=_matcher(True))
        self.engine.register_rule(rule)
        decision = self.engine.evaluate(self.result_with_matches, decision_type="check")
        self.assertEqual(decision.matched_rules, (rule,))


# -- Rule registration --------------------------------------------------------


class RuleRegistrationTests(DecisionEngineTestCase):
    def test_register_rule(self):
        rule = DecisionRule(name="r1", predicate=_matcher(True))
        self.engine.register_rule(rule)
        self.assertEqual(self.engine.list_rules(), (rule,))

    def test_register_duplicate_rule_raises(self):
        rule = DecisionRule(name="r1", predicate=_matcher(True), id="dupe")
        self.engine.register_rule(rule)
        duplicate = DecisionRule(name="r1-again", predicate=_matcher(False), id="dupe")
        with self.assertRaises(DuplicateRuleError):
            self.engine.register_rule(duplicate)

    def test_register_rejects_non_rule(self):
        with self.assertRaises(InvalidDecisionRuleError):
            self.engine.register_rule("not-a-rule")

    def test_register_rejects_empty_id(self):
        rule = DecisionRule(name="r1", predicate=_matcher(True), id="")
        with self.assertRaises(InvalidDecisionRuleError):
            self.engine.register_rule(rule)

    def test_register_rejects_empty_name(self):
        rule = DecisionRule(name="", predicate=_matcher(True))
        with self.assertRaises(InvalidDecisionRuleError):
            self.engine.register_rule(rule)

    def test_register_rejects_non_int_priority(self):
        rule = DecisionRule(name="r1", predicate=_matcher(True), priority="high")
        with self.assertRaises(InvalidDecisionRuleError):
            self.engine.register_rule(rule)

    def test_register_rejects_bool_priority(self):
        rule = DecisionRule(name="r1", predicate=_matcher(True), priority=True)
        with self.assertRaises(InvalidDecisionRuleError):
            self.engine.register_rule(rule)

    def test_register_rejects_non_callable_predicate(self):
        rule = DecisionRule(name="r1", predicate="not-callable")
        with self.assertRaises(InvalidDecisionRuleError):
            self.engine.register_rule(rule)

    def test_remove_rule(self):
        rule = DecisionRule(name="r1", predicate=_matcher(True))
        self.engine.register_rule(rule)
        self.engine.remove_rule(rule.id)
        self.assertEqual(self.engine.list_rules(), ())

    def test_remove_unknown_rule_raises(self):
        with self.assertRaises(RuleNotFoundError):
            self.engine.remove_rule("nonexistent")

    def test_remove_rejects_empty_rule_id(self):
        with self.assertRaises(InvalidDecisionRuleError):
            self.engine.remove_rule("")

    def test_remove_rejects_non_string_rule_id(self):
        with self.assertRaises(InvalidDecisionRuleError):
            self.engine.remove_rule(123)


# -- Rule ordering --------------------------------------------------------------


class RuleOrderingTests(DecisionEngineTestCase):
    def test_list_rules_sorted_by_priority_ascending(self):
        low = DecisionRule(name="low", predicate=_matcher(True), priority=10)
        high = DecisionRule(name="high", predicate=_matcher(True), priority=1)
        self.engine.register_rule(low)
        self.engine.register_rule(high)
        self.assertEqual([r.name for r in self.engine.list_rules()], ["high", "low"])

    def test_equal_priority_ties_broken_by_registration_order(self):
        first = DecisionRule(name="first", predicate=_matcher(True), priority=5)
        second = DecisionRule(name="second", predicate=_matcher(True), priority=5)
        self.engine.register_rule(first)
        self.engine.register_rule(second)
        self.assertEqual([r.name for r in self.engine.list_rules()], ["first", "second"])

    def test_evaluation_respects_priority_order(self):
        order = []

        def record_a(results):
            order.append("a")
            return True

        def record_b(results):
            order.append("b")
            return True

        rule_b = DecisionRule(name="b", predicate=record_b, priority=2)
        rule_a = DecisionRule(name="a", predicate=record_a, priority=1)
        self.engine.register_rule(rule_b)
        self.engine.register_rule(rule_a)

        self.engine.evaluate(self.result_with_matches, decision_type="order_check")
        self.assertEqual(order, ["a", "b"])

    def test_removed_rule_no_longer_evaluated_or_listed(self):
        rule = DecisionRule(name="r1", predicate=_matcher(True))
        self.engine.register_rule(rule)
        self.engine.remove_rule(rule.id)
        decision = self.engine.evaluate(self.result_with_matches, decision_type="check")
        self.assertEqual(decision.matched_rules, ())
        self.assertEqual(self.engine.list_rules(), ())


# -- Deterministic evaluation ---------------------------------------------------


class EvaluationTests(DecisionEngineTestCase):
    def test_evaluate_single_reasoning_result(self):
        rule = DecisionRule(name="has_matches", predicate=_has_any_matched_entities)
        self.engine.register_rule(rule)
        decision = self.engine.evaluate(self.result_with_matches, decision_type="check")
        self.assertEqual(decision.matched_rules, (rule,))
        self.assertEqual(decision.reasoning_results, (self.result_with_matches,))
        self.assertEqual(decision.decision_type, "check")

    def test_evaluate_no_rules_registered(self):
        decision = self.engine.evaluate(self.result_with_matches, decision_type="check")
        self.assertEqual(decision.matched_rules, ())
        self.assertEqual(decision.metadata["total_rule_count"], 0)

    def test_evaluate_all_rules_run_no_short_circuit(self):
        matched_rule = DecisionRule(name="matched", predicate=_matcher(True), priority=1)
        unmatched_rule = DecisionRule(name="unmatched", predicate=_matcher(False), priority=2)
        self.engine.register_rule(matched_rule)
        self.engine.register_rule(unmatched_rule)

        decision = self.engine.evaluate(self.result_with_matches, decision_type="check")
        self.assertEqual(decision.matched_rules, (matched_rule,))
        evaluations = decision.metadata["rule_evaluations"]
        self.assertEqual(len(evaluations), 2)
        self.assertEqual(evaluations[0]["matched"], True)
        self.assertEqual(evaluations[1]["matched"], False)

    def test_evaluate_is_deterministic_across_repeated_calls(self):
        rule = DecisionRule(name="has_matches", predicate=_has_any_matched_entities)
        self.engine.register_rule(rule)
        decision_1 = self.engine.evaluate(self.result_with_matches, decision_type="check")
        decision_2 = self.engine.evaluate(self.result_with_matches, decision_type="check")
        self.assertEqual(decision_1.matched_rules, decision_2.matched_rules)
        self.assertEqual(
            [e["matched"] for e in decision_1.metadata["rule_evaluations"]],
            [e["matched"] for e in decision_2.metadata["rule_evaluations"]],
        )

    def test_evaluate_rejects_non_reasoning_result(self):
        with self.assertRaises(InvalidDecisionInputError):
            self.engine.evaluate("not-a-result", decision_type="check")

    def test_evaluate_rejects_empty_decision_type(self):
        with self.assertRaises(InvalidDecisionInputError):
            self.engine.evaluate(self.result_with_matches, decision_type="")

    def test_evaluate_rejects_non_string_decision_type(self):
        with self.assertRaises(InvalidDecisionInputError):
            self.engine.evaluate(self.result_with_matches, decision_type=None)


class MultipleReasoningResultsTests(DecisionEngineTestCase):
    def test_evaluate_all_multiple_reasoning_results(self):
        rule = DecisionRule(name="has_matches", predicate=_has_any_matched_entities)
        self.engine.register_rule(rule)
        decision = self.engine.evaluate_all(
            (self.result_without_matches, self.result_with_matches), decision_type="batch_check"
        )
        self.assertEqual(decision.matched_rules, (rule,))
        self.assertEqual(decision.reasoning_results, (self.result_without_matches, self.result_with_matches))
        self.assertEqual(decision.metadata["reasoning_result_count"], 2)

    def test_evaluate_all_no_matches_across_all_results(self):
        rule = DecisionRule(name="has_matches", predicate=_has_any_matched_entities)
        self.engine.register_rule(rule)
        decision = self.engine.evaluate_all((self.result_without_matches,), decision_type="batch_check")
        self.assertEqual(decision.matched_rules, ())

    def test_evaluate_all_rejects_empty_sequence(self):
        with self.assertRaises(InvalidDecisionInputError):
            self.engine.evaluate_all((), decision_type="check")

    def test_evaluate_all_rejects_non_sequence(self):
        with self.assertRaises(InvalidDecisionInputError):
            self.engine.evaluate_all(self.result_with_matches, decision_type="check")

    def test_evaluate_all_rejects_non_reasoning_result_item(self):
        with self.assertRaises(InvalidDecisionInputError):
            self.engine.evaluate_all((self.result_with_matches, "not-a-result"), decision_type="check")

    def test_evaluate_delegates_to_evaluate_all(self):
        rule = DecisionRule(name="has_matches", predicate=_has_any_matched_entities)
        self.engine.register_rule(rule)
        via_evaluate = self.engine.evaluate(self.result_with_matches, decision_type="check")
        via_evaluate_all = self.engine.evaluate_all((self.result_with_matches,), decision_type="check")
        self.assertEqual(via_evaluate.matched_rules, via_evaluate_all.matched_rules)


class RuleEvaluationFailureTests(DecisionEngineTestCase):
    def test_raising_predicate_aborts_evaluation(self):
        bad_rule = DecisionRule(name="bad", predicate=_raises)
        self.engine.register_rule(bad_rule)
        with self.assertRaises(RuleEvaluationError):
            self.engine.evaluate(self.result_with_matches, decision_type="check")

    def test_raising_predicate_prevents_later_rules_from_running(self):
        ran = []

        def later(results):
            ran.append("later")
            return True

        bad_rule = DecisionRule(name="bad", predicate=_raises, priority=1)
        later_rule = DecisionRule(name="later", predicate=later, priority=2)
        self.engine.register_rule(bad_rule)
        self.engine.register_rule(later_rule)

        with self.assertRaises(RuleEvaluationError):
            self.engine.evaluate(self.result_with_matches, decision_type="check")
        self.assertEqual(ran, [])


# -- Decision summaries -------------------------------------------------------


class DecisionSummaryTests(DecisionEngineTestCase):
    def test_summary_reflects_registered_rules(self):
        rule = DecisionRule(name="r1", predicate=_matcher(True), priority=3)
        self.engine.register_rule(rule)
        summary = self.engine.decision_summary()
        self.assertEqual(summary["rule_count"], 1)
        self.assertEqual(summary["rules"][0]["id"], rule.id)
        self.assertEqual(summary["rules"][0]["name"], "r1")
        self.assertEqual(summary["rules"][0]["priority"], 3)

    def test_summary_empty_when_no_rules(self):
        summary = self.engine.decision_summary()
        self.assertEqual(summary["rule_count"], 0)
        self.assertEqual(summary["rules"], ())

    def test_summary_does_not_reflect_past_decisions(self):
        # No persistence of past Decisions - decision_summary()
        # describes the registered rule set only.
        rule = DecisionRule(name="r1", predicate=_matcher(True))
        self.engine.register_rule(rule)
        self.engine.evaluate(self.result_with_matches, decision_type="check")
        summary = self.engine.decision_summary()
        self.assertNotIn("decisions", summary)
        self.assertNotIn("last_decision", summary)


# -- Event publication --------------------------------------------------------


class EventPublicationTests(DecisionEngineTestCase):
    def test_successful_evaluation_publishes_evaluated_then_created(self):
        received = self._events(
            EventType.DECISION_EVALUATED, EventType.DECISION_CREATED, EventType.DECISION_FAILED
        )
        rule = DecisionRule(name="r1", predicate=_matcher(True))
        self.engine.register_rule(rule)
        self.engine.evaluate(self.result_with_matches, decision_type="check")
        self.assertEqual(
            [event.type for event in received], [EventType.DECISION_EVALUATED, EventType.DECISION_CREATED]
        )
        self.assertEqual(received[0].source, "decision_engine")
        self.assertEqual(received[0].payload["decision_type"], "check")
        self.assertEqual(received[1].payload["matched_rule_count"], 1)

    def test_failed_evaluation_publishes_failed_only(self):
        received = self._events(
            EventType.DECISION_EVALUATED, EventType.DECISION_CREATED, EventType.DECISION_FAILED
        )
        bad_rule = DecisionRule(name="bad", predicate=_raises)
        self.engine.register_rule(bad_rule)
        with self.assertRaises(RuleEvaluationError):
            self.engine.evaluate(self.result_with_matches, decision_type="check")
        self.assertEqual([event.type for event in received], [EventType.DECISION_FAILED])
        self.assertEqual(received[0].payload["rule_id"], bad_rule.id)
        self.assertIn("reason", received[0].payload)

    def test_register_and_remove_rule_publish_nothing(self):
        # This package's own Events section names exactly three
        # evaluation-lifecycle events - no rule-registration events
        # exist, per engine.py's own module docstring.
        received = self._events(
            EventType.DECISION_EVALUATED, EventType.DECISION_CREATED, EventType.DECISION_FAILED
        )
        rule = DecisionRule(name="r1", predicate=_matcher(True))
        self.engine.register_rule(rule)
        self.engine.remove_rule(rule.id)
        self.assertEqual(received, [])

    def test_invalid_input_publishes_nothing(self):
        # Validation failures occur before any rule is evaluated, so
        # no event fires at all - not even DECISION_FAILED, which is
        # reserved for failures during evaluation itself.
        received = self._events(
            EventType.DECISION_EVALUATED, EventType.DECISION_CREATED, EventType.DECISION_FAILED
        )
        with self.assertRaises(InvalidDecisionInputError):
            self.engine.evaluate(self.result_with_matches, decision_type="")
        self.assertEqual(received, [])


if __name__ == "__main__":
    unittest.main()
