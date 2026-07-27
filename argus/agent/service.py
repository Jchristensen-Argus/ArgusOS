"""
AgentService: in-memory orchestration for the ArgusOS Agent Session
package.

Purpose:
    Implement IAgentService: accept an AgentRequest, invoke
    CognitivePipeline.run() with a PipelineRequest built from it, and
    return the resulting AgentResponse, wrapping the PipelineResult
    unmodified - per factory/packages/026_AGENT_SESSION.md. "An Agent
    Session represents an ongoing interaction between a user and
    Argus. It owns conversation continuity. It orchestrates the
    Cognitive Pipeline. It does not perform reasoning. It does not
    perform planning. It does not perform execution."

File Naming Deviates From The Work Order's Own Listed File Names:
    This package's own "New Package" section lists exactly six files
    (`__init__.py`, `session.py`, `request.py`, `response.py`,
    `interfaces.py`, `exceptions.py`) for `argus/agent/`, with no
    seventh file for AgentService's own concrete implementation -
    unlike Package 025's own listing, which named `pipeline.py`
    explicitly alongside `request.py`/`result.py`/`interfaces.py`/
    `exceptions.py` for exactly this purpose. Two shapes were on the
    table: put the concrete AgentService inside `interfaces.py`
    alongside `IAgentService` (matching the work order's literal file
    count exactly), or add this one additional file, `service.py`, not
    named in the work order (matching this codebase's own
    interface/implementation separation, observed without exception
    in every prior package - `argus/pipeline/interfaces.py`,
    `argus/planner/interfaces.py`, `argus/decision/interfaces.py`,
    `argus/reasoning/interfaces.py`, `argus/memory_integration/
    interfaces.py`, `argus/knowledge_graph/interfaces.py`,
    `argus/connectors/interfaces.py`, `argus/runtime/interfaces.py`,
    `argus/context/interfaces.py`, and `argus/planning/interfaces.py`
    each hold an ABC only, never a concrete class). Chose the second
    shape: `interfaces.py` staying contract-only is the far more
    consistently-observed rule of the two, and is load-bearing
    elsewhere in this codebase's own conventions (a reviewer opening
    any `interfaces.py` in this repository can trust it never contains
    executable service logic) - one small, explicitly documented file
    deviation preserves a much larger and more consequential
    invariant. Flagged here, in factory/packages/026_AGENT_SESSION.md,
    and in DEVLOG.md as a genuine ambiguity this package's own file
    listing left open, resolved by engineering judgment rather than by
    guessing silently.

Interaction Sequence - run() Does Exactly Four Things:
    1. Accept an AgentRequest (validated: must be an AgentRequest
       instance whose `session` is an AgentSession and whose
       `conversation` is a ConversationSession).
    2. Build a PipelineRequest from it - `conversation=request.
       conversation` directly, and `metadata` carrying every key/value
       pair from `request.metadata` plus `agent_request_id` and
       `agent_session_id`, for traceability (see "Metadata
       Propagation" below).
    3. Invoke `cognitive_pipeline.run(pipeline_request)` - the one
       live service call this method makes. Any exception it raises is
       caught and re-raised as AgentExecutionError, wrapping the
       original (`raise ... from error`) - no partial AgentResponse is
       ever returned.
    4. Return an AgentResponse assembled from `request.session` and
       the PipelineResult `cognitive_pipeline.run()` returned, plus
       propagated metadata.

    No new EventTypes are published anywhere in this sequence -
    "No event publication" - and every event the *pipeline's* own
    orchestration produces still fires from inside
    `Planner.plan_session()`'s pre-existing delegated calls, exactly
    as documented in Package 025's own module docstring;
    `AgentService` itself holds no `IEventBus` reference at all, the
    same "nothing of its own to publish" shape `CognitivePipeline`
    (Package 025) already established one layer below.

Dependency Boundary - CognitivePipeline Only:
    Per this package's own explicit Dependency Rules, `AgentService`'s
    constructor accepts exactly one dependency: an `ICognitivePipeline`.
    It holds no reference to `IPlanner`, `IReasoningEngine`,
    `IDecisionEngine`, any builder, or any bootstrap internal - "All
    cognition flows through the Pipeline" is true by construction, not
    by restraint, since there is no live Planner/Reasoning/Decision
    service or builder this class could call into even if it wanted
    to.

Metadata Propagation:
    Every key/value pair in `request.metadata`, plus `agent_request_id`
    and `agent_session_id`, is passed through to the built
    `PipelineRequest.metadata` - which the Cognitive Pipeline itself
    then propagates further, into the built `CognitiveContext.metadata
    .extra`, the built `PlanningSession.metadata.extra`, and the
    returned `PipelineResult.metadata`, per Package 025's own already-
    established behavior. The same data is also recorded directly in
    the returned `AgentResponse.metadata` itself - a caller's own
    metadata is genuinely observable at every layer of the response,
    not silently dropped at the agent boundary. This is plain data
    propagation, not business logic - `AgentService` never inspects,
    branches on, or otherwise interprets any metadata value; it only
    forwards what it was given, per "Nothing more" (this package's own
    AgentService Responsibilities section).

Responsibilities:
    - run(): orchestrate one full agent interaction, per the sequence
      above.
    - initialize / start / stop / status, per the inherited IService
      contract. run() *is* gated on the service's own lifecycle state
      being RUNNING - see interfaces.py's own Architectural Note.

Non-Responsibilities:
    - AgentService never implements reasoning, decision making,
      planning, or execution itself - it only calls
      CognitivePipeline.run(), which itself performs none of those
      either (Package 025's own Objective).
    - AgentService never modifies any object it is given or
      constructs - `AgentSession`, `AgentRequest`, `ConversationSession`,
      and `PipelineResult` are all already immutable value objects, so
      this is true by construction, not by anything this module does
      to enforce it.
    - No AI, no LLM, no persistence, no concurrency, no natural-
      language response generation - Version 1 orchestrates entirely
      in-process, in memory, per this package's own explicit
      Constraints.

Dependencies:
    argus.agent (AgentRequest, AgentResponse, AgentSession,
    IAgentService, and the agent exceptions), argus.pipeline.interfaces
    (ICognitivePipeline), argus.pipeline.request (PipelineRequest),
    argus.lifecycle.lifecycle (LifecycleState).
"""

from typing import Any, Dict

from argus.agent.exceptions import (
    AgentError,
    AgentExecutionError,
    InvalidAgentRequestError,
)
from argus.agent.interfaces import IAgentService
from argus.agent.request import AgentRequest
from argus.agent.response import AgentResponse
from argus.agent.session import AgentSession
from argus.conversation.session import ConversationSession
from argus.lifecycle.lifecycle import LifecycleState
from argus.pipeline.interfaces import ICognitivePipeline
from argus.pipeline.request import PipelineRequest


class AgentService(IAgentService):
    """
    In-memory implementation of IAgentService.

    Purpose:
        Be the sole place ArgusOS turns an AgentRequest into an
        AgentResponse by orchestrating the existing CognitivePipeline,
        as orchestration only - no reasoning, no planning, no
        execution, no natural-language response generation. See the
        module docstring for the full design rationale.

    Dependencies:
        An ICognitivePipeline implementation, injected by the caller
        (bootstrap.py). No other constructor dependency - see the
        module docstring's "Dependency Boundary" note.
    """

    def __init__(self, cognitive_pipeline: ICognitivePipeline) -> None:
        self._cognitive_pipeline = cognitive_pipeline
        self._state: LifecycleState = LifecycleState.CREATED

    # -- IService (see interfaces.py's Architectural Note: run() is
    #    genuinely gated on RUNNING) -------------------------------

    def initialize(self) -> None:
        if self._state != LifecycleState.CREATED:
            raise AgentError(
                f"Cannot initialize: AgentService is {self._state.name}, "
                f"expected CREATED."
            )
        self._state = LifecycleState.INITIALIZING

    def start(self) -> None:
        if self._state != LifecycleState.INITIALIZING:
            raise AgentError(
                f"Cannot start: AgentService is {self._state.name}, "
                f"expected INITIALIZING."
            )
        self._state = LifecycleState.RUNNING

    def stop(self) -> None:
        if self._state != LifecycleState.RUNNING:
            raise AgentError(
                f"Cannot stop: AgentService is {self._state.name}, expected RUNNING."
            )
        self._state = LifecycleState.STOPPING
        self._state = LifecycleState.STOPPED

    def status(self) -> LifecycleState:
        return self._state

    # -- IAgentService --------------------------------------------------

    def run(self, request: AgentRequest) -> AgentResponse:
        if self._state != LifecycleState.RUNNING:
            raise AgentError(
                f"Cannot run: AgentService is {self._state.name}, expected RUNNING."
            )
        if not isinstance(request, AgentRequest):
            raise InvalidAgentRequestError(
                f"run() requires an AgentRequest, got {request!r}."
            )
        if not isinstance(request.session, AgentSession):
            raise InvalidAgentRequestError(
                f"AgentRequest.session must be an AgentSession, got "
                f"{request.session!r}."
            )
        if not isinstance(request.conversation, ConversationSession):
            raise InvalidAgentRequestError(
                f"AgentRequest.conversation must be a ConversationSession, "
                f"got {request.conversation!r}."
            )

        propagated_metadata = self._propagated_metadata(request)

        pipeline_request = PipelineRequest(
            conversation=request.conversation,
            metadata=propagated_metadata,
        )

        try:
            pipeline_result = self._cognitive_pipeline.run(pipeline_request)
        except Exception as error:
            raise AgentExecutionError(
                f"CognitivePipeline.run() failed for "
                f"agent_request_id={request.request_id!r}: {error}"
            ) from error

        return AgentResponse(
            session=request.session,
            pipeline_result=pipeline_result,
            metadata=propagated_metadata,
        )

    # -- internals ------------------------------------------------------

    def _propagated_metadata(self, request: AgentRequest) -> Dict[str, Any]:
        metadata: Dict[str, Any] = {
            "agent_request_id": request.request_id,
            "agent_session_id": request.session.session_id,
        }
        metadata.update(dict(request.metadata))
        return metadata
