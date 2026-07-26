"""
The Decision value object for the ArgusOS Decision Engine.

Purpose:
    Represent a single, immutable outcome of evaluating one or more
    ReasoningResult objects against the Decision Engine's registered
    DecisionRules - per factory/packages/021_DECISION_ENGINE.md. A
    Decision is pure data: it does not evaluate anything itself and
    holds no live reference back to the DecisionEngine that produced
    it. "Decision is immutable."

Responsibilities:
    - Decision: hold the outcome of one evaluate()/evaluate_all()
      call - which rules matched, what it was evaluated from, and
      descriptive metadata - as an immutable value object.

Non-Responsibilities:
    - Decision performs no evaluation, filtering, or rule matching
      itself - see argus.decision.engine.DecisionEngine for all
      evaluation logic.
    - This module depends only on argus.decision.rule.DecisionRule
      and argus.reasoning.result.ReasoningResult to type its two
      Sequence fields - it has no dependency on
      argus.decision.engine, matching the "pure, dependency-free
      leaf" precedent set by every other value object in this
      codebase.

Dependencies:
    argus.decision.rule (DecisionRule),
    argus.reasoning.result (ReasoningResult).
"""

import uuid
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from argus.decision.rule import DecisionRule
from argus.reasoning.result import ReasoningResult


@dataclass(frozen=True)
class Decision:
    """
    An immutable outcome of a single evaluate()/evaluate_all() call.
    See the module docstring for the full field semantics.

    Fields:
        decision_type: A caller-supplied classification label for
            what this evaluation call was deciding about (the
            Decision Engine itself has no domain knowledge of what
            any decision_type means - it is opaque, caller-defined
            data, per this package's own "deterministic
            infrastructure only" scope). Required, non-empty.
        decision_id: Unique identifier for this Decision. Defaults to
            a fresh uuid4 string.
        matched_rules: Every DecisionRule whose predicate returned
            True for this evaluation, in priority order. Defaults to
            an empty tuple.
        reasoning_results: The ReasoningResult objects this Decision
            was evaluated from. Defaults to an empty tuple.
        metadata: Additional descriptive data about the evaluation
            (for example, a full per-rule matched/not-matched trace,
            and rule/result counts). Defaults to an empty mapping.
    """

    decision_type: str
    decision_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    matched_rules: Sequence[DecisionRule] = field(default_factory=tuple)
    reasoning_results: Sequence[ReasoningResult] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "matched_rules", tuple(self.matched_rules))
        object.__setattr__(self, "reasoning_results", tuple(self.reasoning_results))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
