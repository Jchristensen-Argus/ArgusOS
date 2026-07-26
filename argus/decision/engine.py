"""
DecisionEngine: deterministic rule-evaluation implementation of
IDecisionEngine for the ArgusOS Decision Engine.

Purpose:
    Implement IDecisionEngine: register/remove/list deterministic
    DecisionRules, and evaluate one or more ReasoningResult objects
    against all of them - in priority order - to produce a structured
    Decision, per factory/packages/021_DECISION_ENGINE.md. "It does
    not execute decisions. It does not invoke the Planner. It does
    not use AI or LLMs. Its responsibility is limited to deterministic
    decision evaluation." The Decision Engine never mutates memory or
    the Knowledge Graph, never invokes a Planner, Workflow, Connector,
    or LLM - every action it takes is either local rule-table
    bookkeeping or calling a caller-supplied, in-process predicate
    function.

Deterministic Evaluation, Not Short-Circuit:
    evaluate_all() runs every registered rule's predicate, in priority
    order, against the full set of ReasoningResult objects given -
    there is no "stop at first match." This directly serves "explain
    which rules matched" and "expose rule evaluation metadata": a
    Decision's own `matched_rules` reports every rule that matched
    (not just the first), and its `metadata["rule_evaluations"]`
    reports a complete matched/not-matched trace for every registered
    rule, whether it matched or not - useful for a future caller
    debugging why a rule they expected to match did not.

A Raising Predicate Aborts the Call - No Best-Effort Batch:
    Unlike MemoryIntegration.synchronize_all() (Package 019), which
    treats individual translation failures as expected and continues
    the batch, evaluate_all() treats a predicate raising an exception
    as exceptional - a bug in the caller-supplied rule, not a normal
    outcome to tolerate silently. The first rule whose predicate
    raises aborts the whole evaluation: DECISION_FAILED is published,
    the underlying exception is wrapped and re-raised as
    RuleEvaluationError, and no Decision is returned at all. A
    MemoryRecord's translation failing was foreseeable and common
    (Package 019's own reasoning); a deterministic rule predicate
    raising on well-formed ReasoningResult input is not - it indicates
    the predicate itself is broken, which is worth surfacing loudly
    rather than quietly excluding that one rule's vote from the
    result.

Responsibilities:
    - DecisionEngine: the sole implementation of IDecisionEngine.

Non-Responsibilities:
    - DecisionEngine never calls IReasoningEngine, IKnowledgeGraph, or
      IMemoryIntegration - see interfaces.py's own Architectural Note
      for why the injected IReasoningEngine is held but not called in
      Version 1.
    - DecisionEngine never invokes an LLM, performs machine learning
      or probabilistic reasoning, executes a Workflow, or invokes a
      Connector.
    - DecisionEngine never parses, evaluates, or dynamically
      generates rule logic of any kind - see rule.py's own "No
      Scripting" note.

Dependencies:
    argus.decision.decision (Decision), argus.decision.exceptions,
    argus.decision.interfaces (IDecisionEngine), argus.decision.rule
    (DecisionRule), argus.events (Event, EventType, IEventBus),
    argus.lifecycle.lifecycle (LifecycleState),
    argus.reasoning.interfaces (IReasoningEngine, for typing/injection
    only - see interfaces.py's own Architectural Note),
    argus.reasoning.result (ReasoningResult).
"""

from typing import Any, Dict, List, Mapping, Sequence

from argus.decision.decision import Decision
from argus.decision.exceptions import (
    DecisionError,
    DuplicateRuleError,
    InvalidDecisionInputError,
    InvalidDecisionRuleError,
    RuleEvaluationError,
    RuleNotFoundError,
)
from argus.decision.interfaces import IDecisionEngine
from argus.decision.rule import DecisionRule
from argus.events.event import Event
from argus.events.event_types import EventType
from argus.events.interfaces import IEventBus
from argus.lifecycle.lifecycle import LifecycleState
from argus.reasoning.interfaces import IReasoningEngine
from argus.reasoning.result import ReasoningResult


class DecisionEngine(IDecisionEngine):
    """
    Deterministic rule-evaluation implementation of IDecisionEngine.

    Purpose:
        Maintain a table of registered DecisionRules and evaluate
        caller-supplied ReasoningResult objects against all of them,
        in priority order, producing a structured Decision. See the
        module docstring for the full design rationale.

    Dependencies:
        An IReasoningEngine (injected per the explicit Bootstrap
        dependency instruction; not called in Version 1 - see
        interfaces.py's own Architectural Note) and an IEventBus, both
        injected by the caller (bootstrap.py).
    """

    def __init__(self, reasoning_engine: IReasoningEngine, event_bus: IEventBus) -> None:
        self._reasoning_engine = reasoning_engine
        self._event_bus = event_bus
        self._rules: Dict[str, DecisionRule] = {}
        self._registration_order: List[str] = []
        self._state: LifecycleState = LifecycleState.CREATED

    # -- IService (see interfaces.py's Architectural Note: adopted per
    #    explicit instruction; no method below is gated on RUNNING) --

    def initialize(self) -> None:
        if self._state != LifecycleState.CREATED:
            raise DecisionError(
                f"Cannot initialize: DecisionEngine is {self._state.name}, expected CREATED."
            )
        self._state = LifecycleState.INITIALIZING

    def start(self) -> None:
        if self._state != LifecycleState.INITIALIZING:
            raise DecisionError(
                f"Cannot start: DecisionEngine is {self._state.name}, expected INITIALIZING."
            )
        self._state = LifecycleState.RUNNING

    def stop(self) -> None:
        if self._state != LifecycleState.RUNNING:
            raise DecisionError(
                f"Cannot stop: DecisionEngine is {self._state.name}, expected RUNNING."
            )
        self._state = LifecycleState.STOPPING
        self._state = LifecycleState.STOPPED

    def status(self) -> LifecycleState:
        return self._state

    # -- IDecisionEngine: rule registry -----------------------------

    def register_rule(self, rule: DecisionRule) -> None:
        if not isinstance(rule, DecisionRule):
            raise InvalidDecisionRuleError(
                f"register_rule() requires a DecisionRule, got {rule!r}."
            )
        if not rule.id:
            raise InvalidDecisionRuleError("DecisionRule.id must be non-empty.")
        if not rule.name:
            raise InvalidDecisionRuleError("DecisionRule.name must be non-empty.")
        if isinstance(rule.priority, bool) or not isinstance(rule.priority, int):
            raise InvalidDecisionRuleError("DecisionRule.priority must be an int.")
        if not callable(rule.predicate):
            raise InvalidDecisionRuleError("DecisionRule.predicate must be callable.")
        if rule.id in self._rules:
            raise DuplicateRuleError(f"DecisionRule {rule.id!r} is already registered.")

        self._rules[rule.id] = rule
        self._registration_order.append(rule.id)

    def remove_rule(self, rule_id: str) -> None:
        self._require_rule(rule_id)
        del self._rules[rule_id]
        self._registration_order.remove(rule_id)

    def list_rules(self) -> Sequence[DecisionRule]:
        registration_index = {
            rule_id: index for index, rule_id in enumerate(self._registration_order)
        }
        ordered_ids = sorted(
            self._rules, key=lambda rule_id: (self._rules[rule_id].priority, registration_index[rule_id])
        )
        return tuple(self._rules[rule_id] for rule_id in ordered_ids)

    def decision_summary(self) -> Mapping[str, Any]:
        rules = self.list_rules()
        return {
            "rule_count": len(rules),
            "rules": tuple(
                {"id": rule.id, "name": rule.name, "priority": rule.priority} for rule in rules
            ),
        }

    # -- IDecisionEngine: evaluation ----------------------------------

    def evaluate(self, reasoning_result: ReasoningResult, *, decision_type: str) -> Decision:
        if not isinstance(reasoning_result, ReasoningResult):
            raise InvalidDecisionInputError(
                f"evaluate() requires a ReasoningResult, got {reasoning_result!r}."
            )
        return self.evaluate_all((reasoning_result,), decision_type=decision_type)

    def evaluate_all(
        self, reasoning_results: Sequence[ReasoningResult], *, decision_type: str
    ) -> Decision:
        self._require_non_empty_string(decision_type, "decision_type")
        self._require_reasoning_results(reasoning_results)

        rules = self.list_rules()
        matched_rules: List[DecisionRule] = []
        evaluations: List[Mapping[str, Any]] = []

        for rule in rules:
            try:
                matched = bool(rule.predicate(tuple(reasoning_results)))
            except Exception as error:
                self._publish(
                    EventType.DECISION_FAILED,
                    {
                        "decision_type": decision_type,
                        "rule_id": rule.id,
                        "reason": str(error),
                    },
                )
                raise RuleEvaluationError(
                    f"DecisionRule {rule.id!r} ({rule.name!r}) raised during evaluation: {error}"
                ) from error

            evaluations.append({"rule_id": rule.id, "name": rule.name, "matched": matched})
            if matched:
                matched_rules.append(rule)

        self._publish(
            EventType.DECISION_EVALUATED,
            {
                "decision_type": decision_type,
                "rule_count": len(rules),
                "matched_rule_count": len(matched_rules),
            },
        )

        metadata = {
            "rule_evaluations": tuple(evaluations),
            "matched_rule_count": len(matched_rules),
            "total_rule_count": len(rules),
            "reasoning_result_count": len(reasoning_results),
        }
        decision = Decision(
            decision_type=decision_type,
            matched_rules=tuple(matched_rules),
            reasoning_results=tuple(reasoning_results),
            metadata=metadata,
        )

        self._publish(
            EventType.DECISION_CREATED,
            {
                "decision_type": decision_type,
                "decision_id": decision.decision_id,
                "matched_rule_count": len(matched_rules),
            },
        )

        return decision

    # -- internal helpers -------------------------------------------------

    def _require_rule(self, rule_id: str) -> DecisionRule:
        if not isinstance(rule_id, str) or not rule_id:
            raise InvalidDecisionRuleError("rule_id must be a non-empty string.")
        try:
            return self._rules[rule_id]
        except KeyError:
            raise RuleNotFoundError(f"No rule registered under {rule_id!r}.")

    @staticmethod
    def _require_non_empty_string(value: Any, name: str) -> None:
        if not isinstance(value, str) or not value:
            raise InvalidDecisionInputError(f"{name} must be a non-empty string.")

    @staticmethod
    def _require_reasoning_results(reasoning_results: Any) -> None:
        if not isinstance(reasoning_results, (list, tuple)):
            raise InvalidDecisionInputError(
                "reasoning_results must be a sequence of ReasoningResult instances."
            )
        if not reasoning_results:
            raise InvalidDecisionInputError(
                "reasoning_results must contain at least one ReasoningResult."
            )
        for item in reasoning_results:
            if not isinstance(item, ReasoningResult):
                raise InvalidDecisionInputError(
                    f"reasoning_results must contain only ReasoningResult instances, got {item!r}."
                )

    def _publish(self, event_type: EventType, payload: dict) -> None:
        self._event_bus.publish(
            Event(type=event_type, source="decision_engine", payload=payload)
        )
