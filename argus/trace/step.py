"""
The TraceStep value object for the ArgusOS Execution Trace.

Purpose:
    Represent one immutable record of a single stage of Argus
    activity having occurred - which component, what action, and
    when - per factory/packages/028_EXECUTION_TRACE.md. "The trace
    records that a stage occurred, not its internal reasoning." A
    TraceStep is deliberately shallow: it holds no reference to
    whatever data the component actually produced (no Plan, no
    Response, no ReasoningResult) - only that the stage happened.

component And action Are Open Strings, Not A Closed Enum:
    The work order gives "Example component values: AgentService,
    CognitivePipeline, Planner, ResponseEngine" - "Example," not an
    exhaustive list - so `component` (and `action`) are plain `str`
    fields, matching PlanStep.step_type's own open-string precedent,
    not a closed enum like PlanStatus/ConversationState.

Required Fields Precede Defaulted Fields:
    The work order's own listed field order is `step_id, component,
    action, timestamp, metadata`. `component` and `action` carry no
    sensible default (an empty placeholder string would misrepresent
    which stage occurred), so - per this codebase's established
    "field-ordering-deviation" precedent (Entity, ReasoningQuery,
    DecisionRule, PipelineRequest/Result, AgentSession/Request/
    Response, Response) - they are declared first in actual dataclass
    field order, ahead of the defaulted `step_id`/`timestamp`/
    `metadata`.

metadata Is A Plain Mapping, Not A Typed Value Object:
    Unlike ExecutionTrace itself (which holds a typed TraceMetadata),
    TraceStep.metadata mirrors PlanStep.metadata/AgentRequest.metadata's
    own "leaf item within a collection holds a plain, open mapping"
    precedent, not the "top-level session-shaped object holds a typed
    Metadata value object" precedent CognitiveContext/PlanningSession/
    Response use.

Responsibilities:
    - TraceStep: hold one immutable record of a single component's
      action having occurred, with a timestamp and open metadata.

Non-Responsibilities:
    - TraceStep performs no validation of its own - see builder.py's
      module docstring; TraceBuilder.with_step() validates before
      constructing one.
    - TraceStep never records a component's internal reasoning,
      output, or state - only that a named action occurred.

Dependencies:
    None.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True)
class TraceStep:
    """
    One immutable record of a single component action having
    occurred. See the module docstring for the full field semantics.

    Fields:
        component: The name of the component the step describes (e.g.
            "AgentService", "CognitivePipeline", "ResponseEngine").
            Required - no default.
        action: A short description of what occurred (e.g. "entry",
            "completed", "invoked"). Required - no default.
        step_id: A unique identifier for this step. Defaults to a
            fresh uuid4 string.
        timestamp: The UTC timestamp this step was recorded. Defaults
            to the current time.
        metadata: Any additional caller-supplied data about this step.
            Defaults to an empty mapping.
    """

    component: str
    action: str
    step_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
