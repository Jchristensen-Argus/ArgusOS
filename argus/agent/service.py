"""
AgentService: in-memory orchestration for the ArgusOS Agent Session
package.

Purpose:
    Implement IAgentService: accept an AgentRequest, invoke
    CognitivePipeline.run() with a PipelineRequest built from it, pass
    the resulting Plan to ResponseEngine.build_response(), and return
    the resulting AgentResponse, wrapping the standardized Response -
    per factory/packages/026_AGENT_SESSION.md, as amended by
    factory/packages/027_RESPONSE_ENGINE.md's own explicit "Agent
    Integration" instruction. "An Agent Session represents an ongoing
    interaction between a user and Argus. It owns conversation
    continuity. It orchestrates the Cognitive Pipeline. It does not
    perform reasoning. It does not perform planning. It does not
    perform execution."

Package 027 Amendment - A Second Constructor Dependency, A Fifth
Interaction Step:
    Package 026's own `AgentService` depended on exactly one
    collaborator, `ICognitivePipeline`, and `run()` performed four
    steps ending in "Return an AgentResponse... wrapping the
    PipelineResult unmodified." Package 027's own explicit "Agent
    Integration" instruction amends both: "After pipeline.run()
    invoke response_engine.build_response(). Return AgentResponse now
    containing: Response instead of: PipelineResult. The Pipeline
    remains completely unchanged." `AgentService.__init__()` now also
    accepts `response_engine: IResponseEngine`; `run()` gains a fifth
    step between the prior steps 3 and 4 (see "Interaction Sequence"
    below). `CognitivePipeline` itself is genuinely unmodified by this
    package - confirmed via `git diff --stat -- argus/pipeline`
    showing zero lines changed - `AgentService` is the only component
    that changed to accommodate the new Response Engine stage.

File Naming Deviates From The Work Order's Own Listed File Names:
    This package's own "New Package" section (Package 026) lists
    exactly six files (`__init__.py`, `session.py`, `request.py`,
    `response.py`, `interfaces.py`, `exceptions.py`) for
    `argus/agent/`, with no seventh file for AgentService's own
    concrete implementation - unlike Package 025's own listing, which
    named `pipeline.py` explicitly alongside `request.py`/`result.py`/
    `interfaces.py`/`exceptions.py` for exactly this purpose. Two
    shapes were on the table: put the concrete AgentService inside
    `interfaces.py` alongside `IAgentService` (matching the work
    order's literal file count exactly), or add this one additional
    file, `service.py`, not named in the work order (matching this
    codebase's own interface/implementation separation, observed
    without exception in every prior package). Chose the second shape
    - see this file's own history in Package 026's DEVLOG.md entry and
    factory/packages/026_AGENT_SESSION.md for the full reasoning,
    unchanged by this package.

Interaction Sequence - run() Does Exactly Five Things:
    1. Accept an AgentRequest (validated: must be an AgentRequest
       instance whose `session` is an AgentSession and whose
       `conversation` is a ConversationSession).
    2. Build a PipelineRequest from it - `conversation=request.
       conversation` directly, and `metadata` carrying every key/value
       pair from `request.metadata` plus `agent_request_id` and
       `agent_session_id`, for traceability (see "Metadata
       Propagation" below).
    3. Invoke `cognitive_pipeline.run(pipeline_request)` - the first
       live service call this method makes. Any exception it raises is
       caught and re-raised as AgentExecutionError, wrapping the
       original (`raise ... from error`) - no partial AgentResponse is
       ever returned.
    4. Invoke `response_engine.build_response(pipeline_result.plan)` -
       the second live service call, made with the Plan the Cognitive
       Pipeline's own PipelineResult carries. Any exception it raises
       is caught and re-raised as AgentExecutionError the same way -
       "dependency failures" (this package's own Testing category,
       amended by Package 027) covers both this and step 3's own
       failure path with the identical exception type, since both are
       "a component AgentService delegates to raised during
       orchestration," per exceptions.py's own module docstring.
    5. Return an AgentResponse assembled from `request.session` and
       the Response `response_engine.build_response()` returned, plus
       propagated metadata.

    No new EventTypes are published anywhere in this sequence -
    "No event publication" - and every event either delegate's own
    orchestration produces still fires from inside
    `Planner.plan_session()`'s pre-existing delegated calls (Package
    025); `ResponseEngine` itself publishes nothing at all (see
    argus.response.engine's own module docstring), and `AgentService`
    itself holds no `IEventBus` reference at all, the same "nothing of
    its own to publish" shape `CognitivePipeline` (Package 025)
    already established two layers below.

Dependency Boundary - CognitivePipeline And ResponseEngine Only:
    Per Package 026's own explicit Dependency Rules, unchanged by
    Package 027, `AgentService`'s constructor accepts exactly two
    dependencies: an `ICognitivePipeline` and (as of this package) an
    `IResponseEngine`. It holds no reference to `IPlanner`,
    `IReasoningEngine`, `IDecisionEngine`, any builder, or any
    bootstrap internal - "All cognition flows through the Pipeline" is
    still true by construction, not by restraint, since there is no
    live Planner/Reasoning/Decision service or builder this class
    could call into even if it wanted to; the Response Engine
    dependency is new, but is itself equally restricted (per
    `ResponseEngine`'s own Dependency Rules) to depending on nothing
    but the Plan it is handed per call.

Metadata Propagation:
    Unchanged in mechanism from Package 026: every key/value pair in
    `request.metadata`, plus `agent_request_id` and `agent_session_id`,
    is passed through to the built `PipelineRequest.metadata` - which
    the Cognitive Pipeline itself then propagates further, into the
    built `CognitiveContext.metadata.extra`, the built
    `PlanningSession.metadata.extra`, and the returned
    `PipelineResult.metadata`. From there, `Planner.plan_session()`'s
    own `_session_plan_metadata()` (Package 024) carries
    `planning_session_id`/`cognitive_context_id`/`constraints` (not
    the full propagated mapping) onto `Plan.metadata` itself - which
    `ResponseEngine.build_response()` then copies into the returned
    `Response.metadata.extra` (see argus.response.engine's own module
    docstring's "Metadata Propagation" note). The original
    `agent_request_id`/`agent_session_id`/caller-supplied keys remain
    directly recorded in the returned `AgentResponse.metadata` itself,
    exactly as they were before this package - only the *nested*
    metadata now visible via `response.metadata.extra` reflects the
    Plan's own narrower `planning_session_id`/`cognitive_context_id`/
    `constraints` shape, not the original request's own keys, since
    `ResponseEngine` never sees the original request at all.

Responsibilities:
    - run(): orchestrate one full agent interaction, per the sequence
      above.
    - initialize / start / stop / status, per the inherited IService
      contract. run() *is* gated on the service's own lifecycle state
      being RUNNING - see interfaces.py's own Architectural Note,
      unchanged by this package.

Non-Responsibilities:
    - AgentService never implements reasoning, decision making,
      planning, or execution itself - it only calls
      CognitivePipeline.run() and ResponseEngine.build_response(),
      neither of which performs any of those either.
    - AgentService never modifies any object it is given or
      constructs - `AgentSession`, `AgentRequest`, `ConversationSession`,
      `PipelineResult`, and `Response` are all already immutable value
      objects, so this is true by construction, not by anything this
      module does to enforce it.
    - No AI, no LLM, no persistence, no concurrency, no natural-
      language response generation - Version 1 orchestrates entirely
      in-process, in memory, per this package's own explicit
      Constraints and Package 027's own identical Constraints.

Dependencies:
    argus.agent (AgentRequest, AgentResponse, AgentSession,
    IAgentService, and the agent exceptions), argus.pipeline.interfaces
    (ICognitivePipeline), argus.pipeline.request (PipelineRequest),
    argus.response.interfaces (IResponseEngine), argus.lifecycle.lifecycle
    (LifecycleState).
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
from argus.response.interfaces import IResponseEngine


class AgentService(IAgentService):
    """
    In-memory implementation of IAgentService.

    Purpose:
        Be the sole place ArgusOS turns an AgentRequest into an
        AgentResponse by orchestrating the existing CognitivePipeline
        and, as of Package 027, the Response Engine - as orchestration
        only - no reasoning, no planning, no execution, no natural-
        language response generation. See the module docstring for
        the full design rationale.

    Dependencies:
        An ICognitivePipeline implementation and an IResponseEngine
        implementation, both injected by the caller (bootstrap.py). No
        other constructor dependency - see the module docstring's
        "Dependency Boundary" note.
    """

    def __init__(
        self, cognitive_pipeline: ICognitivePipeline, response_engine: IResponseEngine
    ) -> None:
        self._cognitive_pipeline = cognitive_pipeline
        self._response_engine = response_engine
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

        try:
            response = self._response_engine.build_response(pipeline_result.plan)
        except Exception as error:
            raise AgentExecutionError(
                f"ResponseEngine.build_response() failed for "
                f"agent_request_id={request.request_id!r}: {error}"
            ) from error

        return AgentResponse(
            session=request.session,
            response=response,
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
