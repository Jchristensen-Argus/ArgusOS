"""
Public re-exports for the ArgusOS Decision Engine package.

Purpose:
    Give callers a single, stable import surface
    (`from argus.decision import ...`) instead of reaching into
    individual submodules, matching the convention established by
    argus/reasoning/__init__.py, argus/memory_integration/__init__.py,
    argus/knowledge_graph/__init__.py, argus/connectors/__init__.py,
    argus/runtime/__init__.py, argus/planner/__init__.py, and
    argus/plugins/__init__.py.

Dependencies:
    argus.decision.decision, argus.decision.engine,
    argus.decision.exceptions, argus.decision.interfaces,
    argus.decision.rule.
"""

from argus.decision.decision import Decision
from argus.decision.engine import DecisionEngine
from argus.decision.exceptions import (
    DecisionError,
    DuplicateRuleError,
    InvalidDecisionInputError,
    InvalidDecisionRuleError,
    RuleEvaluationError,
    RuleNotFoundError,
)
from argus.decision.interfaces import IDecisionEngine
from argus.decision.rule import DecisionPredicate, DecisionRule

__all__ = [
    "IDecisionEngine",
    "DecisionEngine",
    "Decision",
    "DecisionRule",
    "DecisionPredicate",
    "DecisionError",
    "InvalidDecisionRuleError",
    "DuplicateRuleError",
    "RuleNotFoundError",
    "InvalidDecisionInputError",
    "RuleEvaluationError",
]
