"""
The CapabilityContext value object for the ArgusOS Capability Context
package.

Purpose:
    Represent all information available to a capability when it
    eventually performs work - which Task it concerns, the Plan that
    Task belongs to, the ExecutionTrace recorded so far (when
    available), and descriptive metadata - per
    factory/packages/035_CAPABILITY_CONTEXT.md. "A CapabilityContext
    represents all information available to a capability when it
    eventually performs work... The context is simply created and
    passed through the execution pipeline." "The context owns
    references only. No behavior."

Every Field Defaults - CapabilityContext() Is Always Valid:
    CapabilityContext has its own dedicated CapabilityContextBuilder -
    the same "value object with a dedicated builder" shape
    CognitiveContext (022), PlanningSession (023), ExecutionTrace
    (028), Task (029), TaskRelationship (031), ExecutionResult (032),
    and CapabilityExecutionResult (034) all use, each of which lets
    every field default and leaves construction-time validation to the
    builder's own with_*() methods (see builder.py's own module
    docstring). `context_id` defaults to a fresh uuid4 string, `task`/
    `plan`/`execution_trace` all default to `None` (mirroring
    `ExecutionResult.plan`(032)/`CapabilityExecutionResult.task`(034)/
    `PlanningSession.cognitive_context`(022/023)'s own "optional
    object reference" precedent), `metadata` defaults to a fresh
    `CapabilityContextMetadata()`.

task/plan/execution_trace Hold The Objects Directly, Not Reference
Strings:
    Mirrors `ExecutionResult.plan` (032) and
    `CapabilityExecutionResult.task`/`.capability` (034)'s own
    "objects, not references" precedent - the work order's own field
    names ("task," "plan," "execution_trace," not "task_id," "plan_id,"
    "trace_id") already settle this the same way they did for those
    precedents.

execution_trace Is Always None In Version 1 - A Genuine Consequence Of
Construction Timing, Not An Oversight:
    This package's own Fields list names `execution_trace` as one of
    CapabilityContext's five fields, but nothing in this package's own
    Integration section changes `ExecutionEngine.execute(plan)`'s own
    signature to accept an ExecutionTrace, and no genuine ExecutionTrace
    exists at the point `execute()` runs in the first place: the trace
    is built by `AgentService.run()` (via `TraceBuilder.build()`) only
    *after* every step describing `execute()`'s own effects has already
    been recorded onto it (see argus.agent.service's own module
    docstring's "Package 032/034/035 Amendment" notes) - `execute()`
    itself never receives, holds, or constructs an ExecutionTrace of
    its own. Every `CapabilityContext` `ExecutionEngine` constructs in
    Version 1 therefore carries `execution_trace=None` - a deliberate,
    documented consequence of "every field defaults" being the only
    way to satisfy this package's own Requirements list when the
    referenced object does not exist yet at the point construction
    happens, not a bug or an unfinished wiring step. This mirrors
    `ExecutionStatus`'s/`CapabilityExecutionStatus`'s own "member
    reserved, never produced in Version 1" precedent, applied here to
    a field rather than an enum member - see this package's own Known
    Limitations for the fuller statement.

No Validation Here - See builder.py:
    Like every other value object in this codebase, CapabilityContext
    performs no validation of its own fields beyond `metadata`'s own
    typing (a CapabilityContextMetadata, not a bare mapping).
    CapabilityContextBuilder's own with_*() methods are where
    malformed input is rejected - see builder.py's own module
    docstring.

Responsibilities:
    - CapabilityContext: hold identity (`context_id`), the `task` a
      capability will eventually act on, the `plan` that Task belongs
      to, the `execution_trace` recorded so far (when available), and
      descriptive `CapabilityContextMetadata`, as an immutable value
      object.

Non-Responsibilities:
    - CapabilityContext performs no reasoning, dispatch, or execution
      of any kind - "No execution behavior. No AI. No tool invocation.
      No APIs... The context owns references only. No behavior." It is
      a passive data carrier, nothing more.
    - This module depends only on argus.task.task (Task),
      argus.planner.plan (Plan), argus.trace.trace (ExecutionTrace),
      and argus.capability_context.metadata (CapabilityContextMetadata)
      to type its own fields - it has no dependency on
      argus.capability_context.builder, matching the "pure,
      dependency-free leaf" precedent set by every other value object
      in this codebase.

Dependencies:
    argus.task.task (Task), argus.planner.plan (Plan),
    argus.trace.trace (ExecutionTrace), argus.capability_context.metadata
    (CapabilityContextMetadata).
"""

import uuid
from dataclasses import dataclass, field
from typing import Optional

from argus.capability_context.metadata import CapabilityContextMetadata
from argus.planner.plan import Plan
from argus.task.task import Task
from argus.trace.trace import ExecutionTrace


@dataclass(frozen=True)
class CapabilityContext:
    """
    An immutable snapshot of all information available to a capability
    when it eventually performs work. See the module docstring for the
    full field semantics.

    Fields:
        context_id: Unique identifier for this CapabilityContext.
            Defaults to a fresh uuid4 string.
        task: The Task this CapabilityContext concerns. Defaults to
            None.
        plan: The Plan `task` belongs to. Defaults to None.
        execution_trace: The ExecutionTrace recorded so far, when
            available. Always None in Version 1 - see the module
            docstring's own "execution_trace Is Always None" note.
        metadata: Descriptive bookkeeping about this CapabilityContext.
            Defaults to a fresh CapabilityContextMetadata.
    """

    context_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task: Optional[Task] = None
    plan: Optional[Plan] = None
    execution_trace: Optional[ExecutionTrace] = None
    metadata: CapabilityContextMetadata = field(default_factory=CapabilityContextMetadata)
