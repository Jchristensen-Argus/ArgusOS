"""
argus.trace - The ArgusOS Execution Trace package.

Re-exports the public surface of the Execution Trace: the immutable
value objects (ExecutionTrace, TraceStep, TraceMetadata), the mutable
builder (TraceBuilder) and its interface (ITraceBuilder), and this
package's own exceptions. See factory/packages/028_EXECUTION_TRACE.md
for the full architectural rationale.
"""

from argus.trace.builder import TraceBuilder
from argus.trace.exceptions import InvalidTraceStepError, TraceError
from argus.trace.interfaces import ITraceBuilder
from argus.trace.metadata import TRACE_METADATA_VERSION, TraceMetadata
from argus.trace.step import TraceStep
from argus.trace.trace import ExecutionTrace

__all__ = [
    "ExecutionTrace",
    "TraceStep",
    "TraceMetadata",
    "TRACE_METADATA_VERSION",
    "TraceBuilder",
    "ITraceBuilder",
    "TraceError",
    "InvalidTraceStepError",
]
