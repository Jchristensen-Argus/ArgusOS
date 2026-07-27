"""
The AgentResponse value object for the ArgusOS Agent Session package.

Purpose:
    Represent a single, immutable snapshot of one completed
    AgentService.run() call - the AgentSession it concerned, the
    PipelineResult the Cognitive Pipeline produced, an identity, and
    descriptive metadata - per
    factory/packages/026_AGENT_SESSION.md. "Do not generate
    natural-language responses. Do not perform execution. Wrap the
    PipelineResult only." An AgentResponse is pure data: it performs
    no orchestration itself and holds no live reference back to the
    AgentService that produced it.

Wraps The PipelineResult Only - No Natural Language, No Execution:
    `pipeline_result` holds the actual, already-immutable
    `PipelineResult` (Package 025) `CognitivePipeline.run()` returned
    - unmodified, unsummarized, un-narrated. AgentResponse introduces
    no new field describing "what Argus said" or "what happened when
    the Plan ran" - neither concept exists anywhere in this package,
    per its own explicit Constraints ("Do NOT: implement AI, implement
    LLM integration, implement execution"). A caller wanting either
    must build it from `pipeline_result` themselves, in a future
    package explicitly scoped to do so.

Both `session` And `pipeline_result` Are Required:
    Mirrors `PipelineResult`'s (Package 025) own "every field is
    required - this is always a complete snapshot" reasoning: an
    AgentResponse with no session it belongs to, or no PipelineResult
    it wraps, is not a meaningful response to anything. Neither has a
    default; only `response_id` (a fresh uuid4) and `metadata` (an
    empty mapping) do.

Field Ordering Deviates From The Work Order's Own Listed Order:
    The work order lists AgentResponse's fields as `response_id`,
    `session`, `pipeline_result`, `metadata` - but `session` and
    `pipeline_result` have no default while `response_id` does (a
    fresh uuid4). Python dataclass field ordering requires every
    non-default field to precede every defaulted field, so `session`
    and `pipeline_result` are declared first in the actual code below
    - the same listed-order-vs-declared-order deviation already
    applied to `Entity`, `ReasoningQuery`, `DecisionRule`,
    `PipelineRequest`, `PipelineResult`, `AgentSession`, and
    `AgentRequest` (this package) whenever an identical tension arose.

No Validation Here - See service.py:
    Like every other value object in this codebase, AgentResponse
    performs no validation of its own fields in __post_init__ beyond
    the standard mutable-to-immutable wrapping (dict ->
    MappingProxyType). `AgentService.run()` is the only component that
    constructs an AgentResponse during normal operation - see
    service.py's own module docstring for the full orchestration
    sequence that produces one.

Responsibilities:
    - AgentResponse: hold the AgentSession, the wrapped PipelineResult,
      and descriptive metadata produced by one completed
      AgentService.run() call as an immutable value object.

Non-Responsibilities:
    - AgentResponse performs no orchestration, reasoning, decision
      making, planning, or execution of any kind - see this package's
      own Objective and Constraints.
    - This module depends only on argus.agent.session (AgentSession)
      and argus.pipeline.result (PipelineResult) to type its own
      fields - it has no dependency on argus.agent.service, matching
      the "pure, dependency-free leaf" precedent set by every other
      value object in this codebase.

Dependencies:
    argus.agent.session (AgentSession), argus.pipeline.result
    (PipelineResult).
"""

import uuid
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

from argus.agent.session import AgentSession
from argus.pipeline.result import PipelineResult


@dataclass(frozen=True)
class AgentResponse:
    """
    An immutable snapshot of one completed AgentService.run() call.
    See the module docstring for the full field semantics.

    Fields:
        session: The AgentSession this response concerns. Required.
        pipeline_result: The PipelineResult produced by
            CognitivePipeline.run(). Required. Wrapped, never
            summarized or re-narrated - see the module docstring's
            "Wraps The PipelineResult Only" note.
        response_id: Unique identifier for this AgentResponse.
            Defaults to a fresh uuid4 string.
        metadata: Additional descriptive data about this run (for
            example, the originating request's own id and metadata -
            see service.py's own module docstring). Defaults to an
            empty mapping.
    """

    session: AgentSession
    pipeline_result: PipelineResult
    response_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
