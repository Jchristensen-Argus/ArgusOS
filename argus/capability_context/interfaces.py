"""
Interfaces for the ArgusOS Capability Context package.

Purpose:
    Define the abstract contract CapabilityContextBuilder implements.
    Mirrors argus.capability_executor.interfaces'
    ICapabilityExecutionResultBuilder shape exactly.

ICapabilityContextBuilder Is Not An IService:
    Like ICapabilityExecutionResultBuilder (034), IExecutionResultBuilder
    (032), ITaskRelationshipBuilder (031), and every other builder
    interface in this codebase's history, ICapabilityContextBuilder is a
    plain ABC, not an IService - builders are never registered as
    bootstrap-level services (confirmed by direct repository inspection:
    zero `container.register(...)` calls for any `*Builder(` construction
    exist anywhere in this codebase as of Package 035), so they carry no
    lifecycle state of their own. See build.py's/this package's own
    factory/packages/035_CAPABILITY_CONTEXT.md's Bootstrap section for
    the full reasoning.

Responsibilities:
    - ICapabilityContextBuilder: declare the fluent with_*()/build()
      surface CapabilityContextBuilder implements.

Non-Responsibilities:
    - This module contains no implementation - see builder.py.

Dependencies:
    argus.task.task (Task), argus.planner.plan (Plan), argus.trace.trace
    (ExecutionTrace), argus.capability_context.context (CapabilityContext).
"""

from abc import ABC, abstractmethod

from argus.capability_context.context import CapabilityContext
from argus.planner.plan import Plan
from argus.task.task import Task
from argus.trace.trace import ExecutionTrace


class ICapabilityContextBuilder(ABC):
    """Abstract fluent builder contract for CapabilityContext."""

    @abstractmethod
    def with_task(self, task: Task) -> "ICapabilityContextBuilder":
        """Assign the Task this CapabilityContext concerns. A later
        call overwrites an earlier one - the last call before build()
        wins. Raises InvalidCapabilityContextError if `task` is not a
        Task instance."""

    @abstractmethod
    def with_plan(self, plan: Plan) -> "ICapabilityContextBuilder":
        """Assign the Plan `task` belongs to. A later call overwrites
        an earlier one - the last call before build() wins. Raises
        InvalidCapabilityContextError if `plan` is not a Plan
        instance."""

    @abstractmethod
    def with_execution_trace(
        self, execution_trace: ExecutionTrace
    ) -> "ICapabilityContextBuilder":
        """Assign the ExecutionTrace recorded so far. A later call
        overwrites an earlier one - the last call before build() wins.
        Raises InvalidCapabilityContextError if `execution_trace` is
        not an ExecutionTrace instance. Never called by ExecutionEngine
        in Version 1 - see context.py's own module docstring."""

    @abstractmethod
    def with_metadata(self, key: str, value: object) -> "ICapabilityContextBuilder":
        """Set one arbitrary metadata key/value pair on the eventual
        CapabilityContextMetadata.extra mapping. Accumulates across
        multiple calls; the same key overwrites - last call wins."""

    @abstractmethod
    def build(self) -> CapabilityContext:
        """Construct and return a fresh, immutable CapabilityContext
        snapshot from this builder's current accumulated state."""
