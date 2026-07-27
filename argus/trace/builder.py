"""
The TraceBuilder for the ArgusOS Execution Trace.

Purpose:
    Provide a mutable, fluent way to accumulate an ExecutionTrace's
    steps one at a time - as a request moves through AgentService,
    the Cognitive Pipeline, and the Response Engine - before producing
    a single immutable ExecutionTrace snapshot, per
    factory/packages/028_EXECUTION_TRACE.md. "The builder is the only
    mutable object." Directly mirrors argus.context.builder.
    ContextBuilder's (022) and argus.planning.builder.
    PlanningSessionBuilder's (023) own shape, accumulation rules, and
    validation discipline - the same builder pattern applied to the
    Execution Trace.

with_step() Accumulates, In Call Order:
    Each call to with_step(component, action, metadata=...) validates
    its arguments, constructs a fresh immutable TraceStep (with its
    own uuid4 step_id and a timestamp captured at the moment of the
    call), appends it, and returns self. Calling it three times
    produces an ExecutionTrace whose `steps` holds all three, in call
    order - there is no "overwrite" field on this builder, unlike
    ContextBuilder.with_conversation()/PlanningSessionBuilder.
    with_context()'s singular-field exception; every TraceBuilder
    field accumulates.

with_metadata() Only Ever Populates `extra`:
    TraceMetadata's `created_at`, `version`, and `correlation_id`
    fields are system-assigned at ExecutionTrace construction time
    (see metadata.py's own module docstring) - TraceBuilder exposes no
    way to override them. with_metadata(key, value) adds one key/value
    pair to the eventual TraceMetadata.extra mapping; calling it
    multiple times with different keys accumulates, and calling it
    twice with the same key overwrites that key's value - the last
    call wins, mirroring ContextBuilder/PlanningSessionBuilder's
    identical rule.

Validation Lives Here, Not On TraceStep/ExecutionTrace:
    See step.py's and trace.py's own module docstrings - neither
    performs validation of its own; with_step() validates `component`
    and `action` before constructing a TraceStep, raising
    InvalidTraceStepError for malformed input. build() itself performs
    no additional validation - by the time build() runs, every
    accumulated step has already been validated at the point it was
    added.

trace_id Is Fixed At Construction, Not Per build() Call:
    This builder assigns its own `trace_id` once, in __init__ - not a
    fresh one on every build() call - so that multiple build() calls
    against the same builder (as more steps are appended between
    them) all describe snapshots of the *same* logical trace, sharing
    one identity, rather than looking like unrelated traces.

Independent Snapshots:
    build() constructs a fresh ExecutionTrace (and a fresh
    TraceMetadata) from this builder's current accumulated state every
    time it is called. Continuing to call with_step()/with_metadata()
    on the same builder after calling build() - or calling build()
    more than once - never mutates an ExecutionTrace already returned
    by an earlier build() call, since ExecutionTrace's own
    __post_init__ copies the steps sequence it is given (see trace.py).

Responsibilities:
    - TraceBuilder: accumulate an ExecutionTrace's steps one at a
      time, with per-step validation, and produce an immutable
      ExecutionTrace snapshot on build().

Non-Responsibilities:
    - TraceBuilder performs no reasoning, decision-making, or service
      calls - it only validates and accumulates plain data.
    - TraceBuilder is not a service - see interfaces.py's own module
      docstring.

Dependencies:
    argus.trace.trace (ExecutionTrace), argus.trace.step (TraceStep),
    argus.trace.metadata (TraceMetadata), argus.trace.exceptions
    (InvalidTraceStepError), argus.trace.interfaces (ITraceBuilder).
"""

import uuid
from typing import Any, Dict, List, Mapping, Optional

from argus.trace.exceptions import InvalidTraceStepError
from argus.trace.interfaces import ITraceBuilder
from argus.trace.metadata import TraceMetadata
from argus.trace.step import TraceStep
from argus.trace.trace import ExecutionTrace


def _require_non_empty_string(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise InvalidTraceStepError(f"{label} must be a non-empty string, got {value!r}.")
    return value


class TraceBuilder(ITraceBuilder):
    """
    A mutable, fluent builder for ExecutionTrace. See the module
    docstring for the full accumulation and validation semantics.
    """

    def __init__(self) -> None:
        self._trace_id: str = str(uuid.uuid4())
        self._steps: List[TraceStep] = []
        self._metadata_extra: Dict[str, Any] = {}

    def with_step(
        self,
        component: str,
        action: str,
        *,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> "TraceBuilder":
        validated_component = _require_non_empty_string(component, label="component")
        validated_action = _require_non_empty_string(action, label="action")
        if metadata is not None and not isinstance(metadata, Mapping):
            raise InvalidTraceStepError(
                f"metadata must be a mapping or None, got {metadata!r}."
            )
        self._steps.append(
            TraceStep(
                component=validated_component,
                action=validated_action,
                metadata=dict(metadata) if metadata else {},
            )
        )
        return self

    def with_metadata(self, key: str, value: Any) -> "TraceBuilder":
        validated_key = _require_non_empty_string(key, label="metadata key")
        self._metadata_extra[validated_key] = value
        return self

    def build(self) -> ExecutionTrace:
        return ExecutionTrace(
            trace_id=self._trace_id,
            steps=tuple(self._steps),
            metadata=TraceMetadata(extra=dict(self._metadata_extra)),
        )
