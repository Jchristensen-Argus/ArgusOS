"""
Public re-exports for the ArgusOS Agent Runtime package.

Purpose:
    Give callers a single, stable import surface
    (`from argus.runtime import ...`) instead of reaching into
    individual submodules, matching the convention established by
    argus/planner/__init__.py, argus/plugins/__init__.py, and
    argus/capability/__init__.py.

Dependencies:
    argus.runtime.execution, argus.runtime.exceptions,
    argus.runtime.interfaces, argus.runtime.runtime.
"""

from argus.runtime.exceptions import (
    AgentRuntimeError,
    ExecutionNotFoundError,
    InvalidExecutionError,
    InvalidExecutionStateError,
    StepExecutionError,
)
from argus.runtime.execution import Execution, ExecutionStatus
from argus.runtime.interfaces import IAgentRuntime
from argus.runtime.runtime import AgentRuntime

__all__ = [
    "Execution",
    "ExecutionStatus",
    "IAgentRuntime",
    "AgentRuntime",
    "AgentRuntimeError",
    "InvalidExecutionError",
    "ExecutionNotFoundError",
    "InvalidExecutionStateError",
    "StepExecutionError",
]
