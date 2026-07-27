"""
The ExecutionTrace value object for the ArgusOS Execution Trace
package.

Purpose:
    Represent one immutable, ordered record of how a single request
    moved through Argus - per factory/packages/028_EXECUTION_TRACE.md.
    "The Execution Trace is an immutable record of how a request
    moved through Argus. It is not logging. It is not debugging. It
    is not telemetry. It is a first-class architectural object." The
    trace owns an ordered collection of immutable TraceStep objects
    and accompanies the request from beginning to end.

Ordered, Immutable, Never Constructed Directly By Application Code:
    ExecutionTrace itself performs no validation and no ordering logic
    - `steps` is stored exactly as given, wrapped in an immutable
    `tuple` by `__post_init__` (mirroring Plan.steps/PlanningSession.
    goals' own "wrap the given sequence in a tuple" precedent). The
    only supported way to accumulate steps in call order is
    TraceBuilder - see builder.py's own module docstring. An
    ExecutionTrace with zero steps is valid and meaningful (an empty
    trace, e.g. one never populated), matching this package's own
    Testing category "empty trace, populated trace."

All Fields Default - No Required Field:
    Unlike Response (whose `plan` field is required) or PlanningSession
    (whose builder-supplied fields are required), every ExecutionTrace
    field carries a sensible default: `trace_id` defaults to a fresh
    uuid4 string, `steps` defaults to an empty tuple, `metadata`
    defaults to a fresh TraceMetadata(). `ExecutionTrace()` with no
    arguments is therefore always valid, representing a fresh, empty
    trace.

Responsibilities:
    - ExecutionTrace: hold an immutable, ordered record of a
      request's flow through Argus as a first-class value object.

Non-Responsibilities:
    - ExecutionTrace never records reasoning, decisions, or any
      component's internal state - only that named stages occurred,
      via the TraceStep objects it holds.
    - ExecutionTrace performs no persistence, no logging, no
      telemetry, and no serialization of its own.
    - This module depends only on argus.trace.metadata (TraceMetadata)
      and argus.trace.step (TraceStep) - both immutable value objects.

Dependencies:
    argus.trace.metadata (TraceMetadata), argus.trace.step (TraceStep).
"""

import uuid
from dataclasses import dataclass, field
from typing import Sequence

from argus.trace.metadata import TraceMetadata
from argus.trace.step import TraceStep


@dataclass(frozen=True)
class ExecutionTrace:
    """
    One immutable, ordered record of how a single request moved
    through Argus. See the module docstring for the full field
    semantics.

    Fields:
        trace_id: A unique identifier for this trace. Defaults to a
            fresh uuid4 string.
        steps: The ordered TraceStep objects recorded for this trace.
            Defaults to an empty tuple. Always stored as a tuple,
            regardless of what sequence type is given.
        metadata: This trace's own TraceMetadata. Defaults to a fresh
            TraceMetadata().
    """

    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    steps: Sequence[TraceStep] = field(default_factory=tuple)
    metadata: TraceMetadata = field(default_factory=TraceMetadata)

    def __post_init__(self) -> None:
        object.__setattr__(self, "steps", tuple(self.steps))
