"""
CapabilityContextBuilder for the ArgusOS Capability Context package.

Purpose:
    The only mutable object in this package - assigns task, plan,
    execution_trace, and metadata, then builds an immutable
    CapabilityContext. Mirrors CapabilityExecutionResultBuilder (034)'s
    own shape exactly.

No with_context_id():
    This package's own Responsibilities list ("assign task, assign
    plan, assign execution_trace, assign metadata, build immutable
    CapabilityContext") does not name "assign context_id" - continuing
    the "no with_<id>() unless explicitly named" precedent already
    established by RelationshipBuilder (031), ExecutionResultBuilder
    (032), and CapabilityExecutionResultBuilder (034). `context_id`
    is left at its own fresh-uuid4 default for every CapabilityContext
    this builder produces.

with_execution_trace() Is Implemented But Never Called In Version 1:
    ExecutionEngine (the only caller of this builder in Version 1)
    never calls with_execution_trace() - see context.py's own module
    docstring for why no genuine ExecutionTrace exists at the point
    ExecutionEngine.execute() runs. The method itself is implemented
    and tested regardless, matching this interface's own complete
    Responsibilities list rather than leaving part of the surface
    unbuilt.

Responsibilities:
    - CapabilityContextBuilder: assign task, assign plan, assign
      execution_trace, assign metadata, build an immutable
      CapabilityContext.

Non-Responsibilities:
    - No validation beyond isinstance checks on with_task()/with_plan()/
      with_execution_trace() - mirrors every sibling builder's own
      validation depth.

Dependencies:
    argus.capability_context.context (CapabilityContext),
    argus.capability_context.metadata (CapabilityContextMetadata),
    argus.capability_context.interfaces (ICapabilityContextBuilder),
    argus.capability_context.exceptions, argus.task.task (Task),
    argus.planner.plan (Plan), argus.trace.trace (ExecutionTrace).
"""

from typing import Any, Dict, Optional

from argus.capability_context.context import CapabilityContext
from argus.capability_context.exceptions import InvalidCapabilityContextError
from argus.capability_context.interfaces import ICapabilityContextBuilder
from argus.capability_context.metadata import CapabilityContextMetadata
from argus.planner.plan import Plan
from argus.task.task import Task
from argus.trace.trace import ExecutionTrace


class CapabilityContextBuilder(ICapabilityContextBuilder):
    """Mutable fluent builder for CapabilityContext. The only mutable object in this package."""

    def __init__(self) -> None:
        self._task: Optional[Task] = None
        self._plan: Optional[Plan] = None
        self._execution_trace: Optional[ExecutionTrace] = None
        self._metadata_extra: Dict[str, Any] = {}

    def with_task(self, task: Task) -> "CapabilityContextBuilder":
        if not isinstance(task, Task):
            raise InvalidCapabilityContextError(
                f"with_task() requires a Task, got {task!r}."
            )
        self._task = task
        return self

    def with_plan(self, plan: Plan) -> "CapabilityContextBuilder":
        if not isinstance(plan, Plan):
            raise InvalidCapabilityContextError(
                f"with_plan() requires a Plan, got {plan!r}."
            )
        self._plan = plan
        return self

    def with_execution_trace(self, execution_trace: ExecutionTrace) -> "CapabilityContextBuilder":
        if not isinstance(execution_trace, ExecutionTrace):
            raise InvalidCapabilityContextError(
                f"with_execution_trace() requires an ExecutionTrace, got {execution_trace!r}."
            )
        self._execution_trace = execution_trace
        return self

    def with_metadata(self, key: str, value: Any) -> "CapabilityContextBuilder":
        self._metadata_extra[key] = value
        return self

    def build(self) -> CapabilityContext:
        return CapabilityContext(
            task=self._task,
            plan=self._plan,
            execution_trace=self._execution_trace,
            metadata=CapabilityContextMetadata(extra=dict(self._metadata_extra)),
        )
