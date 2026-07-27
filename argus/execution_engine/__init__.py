"""
argus.execution_engine - The ArgusOS Execution Engine package.

Re-exports the public surface of the Execution Engine: the immutable
value objects (ExecutionResult, ExecutionStatus, ExecutionMetadata),
the mutable builder (ExecutionResultBuilder) and its interface
(IExecutionResultBuilder), the engine itself (ExecutionEngine) and its
interface (IExecutionEngine), and this package's own exceptions. See
factory/packages/032_EXECUTION_ENGINE.md for the full architectural
rationale. "The Execution Engine accepts a Plan and produces an
immutable ExecutionResult. It does not execute tools. It does not
call APIs. It does not invoke AI. It simply establishes the execution
lifecycle."
"""

from argus.execution_engine.builder import ExecutionResultBuilder
from argus.execution_engine.engine import ExecutionEngine
from argus.execution_engine.exceptions import (
    ExecutionError,
    InvalidExecutionResultError,
    InvalidPlanReferenceError,
)
from argus.execution_engine.interfaces import IExecutionEngine, IExecutionResultBuilder
from argus.execution_engine.metadata import EXECUTION_METADATA_VERSION, ExecutionMetadata
from argus.execution_engine.result import ExecutionResult
from argus.execution_engine.status import ExecutionStatus

__all__ = [
    "ExecutionResult",
    "ExecutionStatus",
    "ExecutionMetadata",
    "EXECUTION_METADATA_VERSION",
    "ExecutionResultBuilder",
    "IExecutionResultBuilder",
    "ExecutionEngine",
    "IExecutionEngine",
    "ExecutionError",
    "InvalidPlanReferenceError",
    "InvalidExecutionResultError",
]
