"""
The AgentResponse value object for the ArgusOS Agent Session package.

Purpose:
    Represent a single, immutable snapshot of one completed
    AgentService.run() call - the AgentSession it concerned, the
    Response the Response Engine produced, an identity, and
    descriptive metadata - per
    factory/packages/026_AGENT_SESSION.md, as amended by
    factory/packages/027_RESPONSE_ENGINE.md's own explicit "Agent
    Integration" instruction. "Do not generate natural-language
    responses. Do not perform execution. Wrap the PipelineResult
    only" (Package 026) - superseded, per Package 027's own explicit
    instruction, by wrapping the standardized Response the Response
    Engine constructs from the Cognitive Pipeline's own Plan, instead
    of the PipelineResult directly. An AgentResponse is pure data: it
    performs no orchestration itself and holds no live reference back
    to the AgentService that produced it.

Package 027 Amendment - `response: Response` Replaces
`pipeline_result: PipelineResult`:
    Package 026 originally gave this field the name `pipeline_result`,
    typed `argus.pipeline.result.PipelineResult` - the object
    `CognitivePipeline.run()` itself returns directly. Package 027's
    own explicit "Agent Integration" instruction amends this: "After
    pipeline.run() invoke response_engine.build_response(). Return
    AgentResponse now containing: Response instead of: PipelineResult."
    This is a breaking field rename, not an additive change - the
    field is renamed `response`, retyped `argus.response.response
    .Response`, and `PipelineResult` is no longer held anywhere on
    AgentResponse at all. This directly mirrors the same field-name-
    matches-held-type style `PipelineResult.plan: Plan` (Package 025)
    already established - `AgentResponse.response: Response` is that
    same pattern applied here, even though the containing class is
    itself also named "AgentResponse"; the two names describe
    different things at different layers (this whole object is "the
    agent's response to one interaction," one field of which happens
    to be "the standardized Response the cognitive pipeline
    produced"). `service.py`'s own module docstring documents exactly
    how AgentService now obtains a `Response` to hold here - see its
    "Interaction Sequence" note.

Wraps The Response Only - No Natural Language, No Execution:
    `response` holds the actual, already-immutable `Response` (Package
    027) `ResponseEngine.build_response()` returned - unmodified,
    unsummarized, un-narrated. AgentResponse introduces no new field
    describing "what Argus said" or "what happened when the Plan ran"
    - neither concept exists anywhere in this package, per its own
    explicit Constraints ("Do NOT: implement AI, implement LLM
      integration, implement execution") and Package 027's own
    identical Constraints. A caller wanting either must build it from
    `response.plan` themselves, in a future package explicitly scoped
    to do so.

Both `session` And `response` Are Required:
    Mirrors `PipelineResult`'s (Package 025) own "every field is
    required - this is always a complete snapshot" reasoning: an
    AgentResponse with no session it belongs to, or no Response it
    wraps, is not a meaningful response to anything. Neither has a
    default; only `response_id` (a fresh uuid4) and `metadata` (an
    empty mapping) do.

Field Ordering Deviates From The Work Order's Own Listed Order:
    Package 026's own work order lists AgentResponse's fields as
    `response_id`, `session`, `pipeline_result` (now `response`),
    `metadata` - but `session` and `response` have no default while
    `response_id` does (a fresh uuid4). Python dataclass field
    ordering requires every non-default field to precede every
    defaulted field, so `session` and `response` are declared first
    in the actual code below - the same listed-order-vs-declared-order
    deviation already applied to `Entity`, `ReasoningQuery`,
    `DecisionRule`, `PipelineRequest`, `PipelineResult`,
    `AgentSession`, and `AgentRequest` whenever an identical tension
    arose.

No Validation Here - See service.py:
    Like every other value object in this codebase, AgentResponse
    performs no validation of its own fields in __post_init__ beyond
    the standard mutable-to-immutable wrapping (dict ->
    MappingProxyType). `AgentService.run()` is the only component that
    constructs an AgentResponse during normal operation - see
    service.py's own module docstring for the full orchestration
    sequence that produces one.

Responsibilities:
    - AgentResponse: hold the AgentSession, the wrapped Response, and
      descriptive metadata produced by one completed
      AgentService.run() call as an immutable value object.

Non-Responsibilities:
    - AgentResponse performs no orchestration, reasoning, decision
      making, planning, or execution of any kind - see this package's
      own Objective and Constraints.
    - This module depends only on argus.agent.session (AgentSession)
      and argus.response.response (Response) to type its own fields -
      it has no dependency on argus.agent.service or
      argus.pipeline.result, matching the "pure, dependency-free leaf"
      precedent set by every other value object in this codebase.

Dependencies:
    argus.agent.session (AgentSession), argus.response.response
    (Response).
"""

import uuid
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

from argus.agent.session import AgentSession
from argus.response.response import Response


@dataclass(frozen=True)
class AgentResponse:
    """
    An immutable snapshot of one completed AgentService.run() call.
    See the module docstring for the full field semantics.

    Fields:
        session: The AgentSession this response concerns. Required.
        response: The Response produced by
            ResponseEngine.build_response(). Required. Wrapped, never
            summarized or re-narrated - see the module docstring's
            "Wraps The Response Only" note.
        response_id: Unique identifier for this AgentResponse.
            Defaults to a fresh uuid4 string. Distinct from
            `response.response_id` - this identifies the AgentResponse
            itself, not the wrapped Response.
        metadata: Additional descriptive data about this run (for
            example, the originating request's own id and metadata -
            see service.py's own module docstring). Defaults to an
            empty mapping.
    """

    session: AgentSession
    response: Response
    response_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
