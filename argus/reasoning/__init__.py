"""
Public re-exports for the ArgusOS Reasoning Engine package.

Purpose:
    Give callers a single, stable import surface
    (`from argus.reasoning import ...`) instead of reaching into
    individual submodules, matching the convention established by
    argus/memory_integration/__init__.py, argus/knowledge_graph/__init__.py,
    argus/connectors/__init__.py, argus/runtime/__init__.py,
    argus/planner/__init__.py, and argus/plugins/__init__.py.

Dependencies:
    argus.reasoning.engine, argus.reasoning.exceptions,
    argus.reasoning.interfaces, argus.reasoning.query,
    argus.reasoning.result.
"""

from argus.reasoning.engine import ReasoningEngine
from argus.reasoning.exceptions import (
    InvalidReasoningQueryError,
    ReasoningError,
    ReasoningTargetNotFoundError,
)
from argus.reasoning.interfaces import IReasoningEngine
from argus.reasoning.query import ReasoningQuery
from argus.reasoning.result import ReasoningResult

__all__ = [
    "IReasoningEngine",
    "ReasoningEngine",
    "ReasoningQuery",
    "ReasoningResult",
    "ReasoningError",
    "InvalidReasoningQueryError",
    "ReasoningTargetNotFoundError",
]
