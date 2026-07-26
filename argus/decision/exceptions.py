"""
Exceptions raised by the ArgusOS Decision Engine.

Purpose:
    Give callers explicit, catchable failure modes for rule
    registration and decision evaluation failures, per the coding
    standard's "raise meaningful exceptions... never silently ignore
    errors" and factory/packages/021_DECISION_ENGINE.md. Mirrors the
    exception hierarchy shape already established by
    argus.reasoning.exceptions (Package 020) and
    argus.knowledge_graph.exceptions (Package 018).

Responsibilities:
    - Provide a general decision-subsystem error base, and more
      specific subtypes for "invalid rule," "duplicate rule," "rule
      not found," "invalid evaluation input," and "a rule's own
      predicate raised" failures.

Non-Responsibilities:
    - These exceptions carry no behavior beyond a message; they do
      not log, retry, or recover.
    - No dedicated lifecycle-state exception exists here - unlike
      Memory Integration (Package 019), none of the Decision Engine's
      public methods are gated on the RUNNING state, so no method can
      ever raise for that reason. DecisionError is used directly for
      the Decision Engine's own IService lifecycle transition
      failures, exactly mirroring KnowledgeGraphError's (018) and
      ReasoningError's (020) identical role - see
      argus/decision/interfaces.py's Architectural Note for why.

Dependencies:
    None.
"""


class DecisionError(Exception):
    """Base exception for the Decision Engine subsystem. Raised
    directly for failures that are not one of the more specific
    subtypes below (for example, an invalid IService lifecycle
    transition)."""


class InvalidDecisionRuleError(DecisionError):
    """Raised when register_rule() is given something that is not a
    DecisionRule instance, or a DecisionRule with an empty rule_id or
    name, a non-integer priority, or a non-callable predicate - or
    when remove_rule() is given a non-string or empty rule_id."""


class DuplicateRuleError(DecisionError):
    """Raised when register_rule() is called with a rule_id that is
    already registered. Callers must call remove_rule() first to
    replace an existing DecisionRule."""


class RuleNotFoundError(DecisionError):
    """Raised when remove_rule() references a rule_id with no
    corresponding registered DecisionRule."""


class InvalidDecisionInputError(DecisionError):
    """Raised when evaluate()/evaluate_all() is given an empty or
    non-string decision_type, or a reasoning_result(s) argument that
    is not a ReasoningResult (evaluate()) or a non-empty sequence of
    ReasoningResult instances (evaluate_all())."""


class RuleEvaluationError(DecisionError):
    """Raised when a registered DecisionRule's own predicate raises
    while being evaluated. Wraps the underlying exception; the
    triggering failure is published as DECISION_FAILED before this is
    raised, and the whole evaluate_all() call is aborted - no partial
    Decision is returned. See argus/decision/engine.py's own
    Architectural Decision for why a raising predicate aborts the
    call rather than being treated as an expected, best-effort
    failure."""
