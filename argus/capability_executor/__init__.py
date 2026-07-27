"""
argus.capability_executor - The ArgusOS Capability Executor package.

Re-exports the public surface of the Capability Executor: the
immutable value objects (CapabilityExecutionResult,
CapabilityExecutionStatus, CapabilityExecutionMetadata), the mutable
builder (CapabilityExecutionResultBuilder) and its interface
(ICapabilityExecutionResultBuilder), the executor itself
(CapabilityExecutor) and its interface (ICapabilityExecutor), and this
package's own exceptions. See
factory/packages/034_CAPABILITY_EXECUTOR.md for the full architectural
rationale. "The Capability Executor resolves a Capability for a Task
and produces an immutable CapabilityExecutionResult... It establishes
the execution contract only."
"""

from argus.capability_executor.builder import CapabilityExecutionResultBuilder
from argus.capability_executor.exceptions import (
    CapabilityExecutionError,
    InvalidCapabilityExecutionResultError,
    InvalidTaskReferenceError,
)
from argus.capability_executor.executor import CapabilityExecutor
from argus.capability_executor.interfaces import (
    ICapabilityExecutionResultBuilder,
    ICapabilityExecutor,
)
from argus.capability_executor.metadata import (
    CAPABILITY_EXECUTION_METADATA_VERSION,
    CapabilityExecutionMetadata,
)
from argus.capability_executor.result import CapabilityExecutionResult
from argus.capability_executor.status import CapabilityExecutionStatus

__all__ = [
    "CapabilityExecutionResult",
    "CapabilityExecutionStatus",
    "CapabilityExecutionMetadata",
    "CAPABILITY_EXECUTION_METADATA_VERSION",
    "CapabilityExecutionResultBuilder",
    "ICapabilityExecutionResultBuilder",
    "CapabilityExecutor",
    "ICapabilityExecutor",
    "CapabilityExecutionError",
    "InvalidTaskReferenceError",
    "InvalidCapabilityExecutionResultError",
]
