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

# ---------------------------------------------------------------------------
# argus.decision.decision_record - Package 039 additions
# ---------------------------------------------------------------------------
#
# Everything above is Package 021's own Decision Engine re-exports and is
# unmodified. The imports below add the new DecisionRecord domain object
# introduced by Package 039 - see argus/decision/decision_record.py's own
# module docstring for why this concept is named DecisionRecord rather than
# Decision, to avoid colliding with Decision/DecisionEngine/IDecisionEngine
# above.
from argus.decision.builder import DecisionRecordBuilder
from argus.decision.decision_record import DecisionRecord
from argus.decision.exceptions import (
    DecisionRecordError,
    InvalidDecisionRecordError,
)
from argus.decision.interfaces import IDecisionRecordBuilder
from argus.decision.metadata import (
    DECISION_RECORD_METADATA_VERSION,
    DecisionRecordMetadata,
)
from argus.decision.priority import DecisionRecordPriority
from argus.decision.status import DecisionRecordStatus

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
    # Package 039 additions - see the import section above.
    "DecisionRecord",
    "DecisionRecordStatus",
    "DecisionRecordPriority",
    "DecisionRecordMetadata",
    "DECISION_RECORD_METADATA_VERSION",
    "DecisionRecordBuilder",
    "IDecisionRecordBuilder",
    "DecisionRecordError",
    "InvalidDecisionRecordError",
]
