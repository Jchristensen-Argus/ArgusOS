"""
AgentService: in-memory orchestration for the ArgusOS Agent Session
package.

Purpose:
    Implement IAgentService: accept an AgentRequest, build and record
    an ExecutionTrace as the request moves through the Cognitive
    Pipeline, the Execution Engine, and the Response Engine, and
    return the resulting AgentResponse, wrapping the standardized
    Response - per factory/packages/026_AGENT_SESSION.md, as amended
    by factory/packages/027_RESPONSE_ENGINE.md's own explicit "Agent
    Integration" instruction, factory/packages/028_EXECUTION_TRACE.md's
    own explicit "Integration" instruction, and
    factory/packages/032_EXECUTION_ENGINE.md's own explicit
    "Integration" instruction. "An Agent Session represents an ongoing
    interaction between a user and Argus. It owns conversation
    continuity. It orchestrates the Cognitive Pipeline. It does not
    perform reasoning. It does not perform planning. It does not
    perform execution." "The trace begins inside AgentService." Note:
    despite "It does not perform execution" - a Package 026 statement
    describing the Cognitive Pipeline layer AgentService orchestrates
    - AgentService (as of this package) does invoke the Execution
    Engine; "execution" there refers to reasoning/planning/tool
    execution, not the lifecycle-only bookkeeping ExecutionEngine
    itself performs - see argus.execution_engine's own module
    docstrings for why ExecutionEngine "does not invoke tools... does
    not call APIs... does not invoke AI," and is not the kind of
    "execution" that statement excludes.

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

Package 028 Amendment - AgentService Builds And Owns The
ExecutionTrace:
    Per this package's own explicit Integration section, "The trace
    begins inside AgentService," and "Only AgentService and Response
    objects change" - `Planner`, `Reasoning`, `Decision`, `Memory`, and
    `Knowledge` are all genuinely untouched by this package (confirmed
    via `git diff --stat` showing no changes outside `argus/trace/`,
    `argus/response/`, and this file). `run()` now creates a fresh
    `TraceBuilder` (not injected - constructed directly, since
    `TraceBuilder` is "not a service" and has no meaningful lifecycle
    of its own to inject around) at the start of every call, and
    records three steps onto it before handing the finished,
    already-built `ExecutionTrace` to `response_engine.build_response()`.
    (As of Package 032, one more step is recorded onto the same
    builder between the second and third - see the "Package 032
    Amendment" note below.)

Package 032 Amendment - A Third Constructor Dependency, One More
Interaction Step, One More Trace Step:
    Per this package's own explicit "Integration" instruction: "New
    flow: Pipeline -> Execution Engine -> Response Engine.
    ExecutionResult is passed into ResponseEngine." `AgentService.
    __init__()` now also accepts `execution_engine: IExecutionEngine`,
    declared between `cognitive_pipeline` and `response_engine` to
    mirror the flow's own ordering. `run()` gains one more step
    between the prior Pipeline and Response Engine steps: after
    `cognitive_pipeline.run()` completes, `execution_engine.execute
    (pipeline_result.plan)` is invoked, producing the `ExecutionResult`
    that `response_engine.build_response()` now also receives (see
    "Interaction Sequence" below). One more ExecutionTrace step is
    recorded to match - `("ExecutionEngine", "processed")` - per this
    package's own explicit "Add one new trace step: ExecutionEngine,
    action = processed." Unlike the `("ResponseEngine", "invoked")`
    step (028's own Engineering Decision, recorded *before* invocation
    since ResponseEngine is the last stage needing the finished
    trace), `("ExecutionEngine", "processed")` is recorded *after*
    `execute()` actually completes - "processed" is a completed-action
    word, like "completed" for `CognitivePipeline`, not an
    in-progress one like "invoked" - and nothing downstream of
    `ExecutionEngine` needs the trace to already be finished at that
    point, so there is no reason to record it early the way
    `ResponseEngine`'s own step must be.

Engineering Decision - Reconciling "record Response completion" With
"ResponseEngine... receives the finished trace":
    This package's own Integration section's arrow diagram lists steps
    in this literal order: create TraceBuilder -> record AgentService
    entry -> Pipeline -> record Pipeline completion -> Response Engine
    -> record Response completion -> build ExecutionTrace. Read with
    total literalness, this would have the trace finished (built)
    *after* Response Engine has already been invoked - which directly
    conflicts with this same package's own Dependency Rule, "ResponseEngine
    shall not construct traces. It receives the finished trace," since
    a trace ResponseEngine "receives" cannot simultaneously still be
    unbuilt at the point it receives it. The Dependency Rule is phrased
    as a "shall/shall not" constraint - this codebase's strongest form
    of instruction - so it takes precedence over the diagram's own
    literal arrow ordering, which (like every prior package's own
    "Architectural Position" diagram) is read as a narrative summary of
    the stages involved, not a strict line-by-line call sequence.
    Concretely: the step this package's own diagram labels "record
    Response completion" is recorded *before* `response_engine.
    build_response()` is invoked, not after - worded as `("ResponseEngine",
    "invoked")` rather than "completed," an honest description of what
    has actually happened at the moment it is recorded (per "the trace
    records that a stage occurred, not its internal reasoning" -
    recording a stage as "completed" before it has actually completed
    would misrepresent what occurred). This keeps the trace genuinely
    finished and immutable at the moment ResponseEngine receives it,
    honors the Dependency Rule literally, and still records all three
    example component values this package's own step.py module
    docstring names (AgentService, CognitivePipeline, ResponseEngine)
    in the finished trace `Response.execution_trace` ultimately
    exposes.

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

Interaction Sequence - run() Does Exactly Nine Things:
    1. Accept an AgentRequest (validated: must be an AgentRequest
       instance whose `session` is an AgentSession and whose
       `conversation` is a ConversationSession).
    2. Build a PipelineRequest from it - `conversation=request.
       conversation` directly, and `metadata` carrying every key/value
       pair from `request.metadata` plus `agent_request_id` and
       `agent_session_id`, for traceability (see "Metadata
       Propagation" below).
    3. Create a fresh `TraceBuilder` and record its first step -
       `("AgentService", "entry")` - before any other component is
       invoked.
    4. Invoke `cognitive_pipeline.run(pipeline_request)` - the first
       live service call this method makes. Any exception it raises is
       caught and re-raised as AgentExecutionError, wrapping the
       original (`raise ... from error`) - no partial AgentResponse is
       ever returned, and no trace step is recorded for a Pipeline
       call that never completed.
    5. Record one step onto the builder - `("CognitivePipeline",
       "completed")`.
    6. Invoke `execution_engine.execute(pipeline_result.plan)` - the
       second live service call this method makes (Package 032). Any
       exception it raises is caught and re-raised as
       AgentExecutionError the same way step 4's failures are.
    7. Record four more steps onto the same builder -
       `("ExecutionEngine", "processed")`, then `("CapabilityContext",
       "created")` (Package 035), then `("CapabilityExecutor",
       "resolved")` (Package 034), then `("ResponseEngine", "invoked")`
       - and call `.build()` to produce the finished, immutable
       `ExecutionTrace` - see the "Engineering Decision" note above for
       why the "ResponseEngine" step is recorded here, before
       invocation, and the "Package 032"/"Package 034"/"Package 035"
       Amendment notes above for why the "ExecutionEngine",
       "CapabilityContext", and "CapabilityExecutor" steps are instead
       recorded after the work they each describe has already
       happened.
    8. Invoke `response_engine.build_response(pipeline_result.plan,
       execution_result, execution_trace)` - the third live service
       call, made with the Plan the Cognitive Pipeline's own
       PipelineResult carries, the ExecutionResult the Execution
       Engine just produced, and the just-finished ExecutionTrace. Any
       exception it raises is caught and re-raised as
       AgentExecutionError the same way - "dependency failures" (this
       package's own Testing category, amended by Packages 027 and
       032) covers this and steps 4 and 6's own failure paths with the
       identical exception type, since all three are "a component
       AgentService delegates to raised during orchestration," per
       exceptions.py's own module docstring.
    9. Return an AgentResponse assembled from `request.session` and
       the Response `response_engine.build_response()` returned
       (itself now carrying the ExecutionResult and ExecutionTrace via
       `Response.execution_result`/`.execution_trace`), plus
       propagated metadata.

    No new EventTypes are published anywhere in this sequence -
    "No event publication" - and every event either delegate's own
    orchestration produces still fires from inside
    `Planner.plan_session()`'s pre-existing delegated calls (Package
    025); `ResponseEngine` and `ExecutionEngine` both publish nothing
    at all (see argus.response.engine's and
    argus.execution_engine.engine's own module docstrings), and
    `AgentService` itself holds no `IEventBus` reference at all, the
    same "nothing of its own to publish" shape `CognitivePipeline`
    (Package 025) already established two layers below.

Package 034 Amendment - One More Trace Step, No New Constructor
Dependency, No New Interaction Step:
    Per this package's own explicit Execution Trace instruction: "Add
    one new trace entry: CapabilityExecutor, action = resolved. No
    other trace changes." Unlike Packages 027 and 032, this package
    adds no new constructor dependency to `AgentService` and no new
    interaction step to `run()`'s own sequence - `CapabilityExecutor`
    is owned by `ExecutionEngine`, not by `AgentService` (see
    argus.execution_engine.engine's own module docstring), and is
    already called, once per Task, inside step 6's own
    `execution_engine.execute()` call, before that call returns.
    `("CapabilityExecutor", "resolved")` is recorded honestly, after
    the fact - by the time `trace_builder.with_step("ExecutionEngine",
    "processed")` runs, every Task in the Plan has already been sent
    through `CapabilityExecutor.resolve()` - positioned between
    `("ExecutionEngine", "processed")` and `("ResponseEngine",
    "invoked")`, mirroring `("ExecutionEngine", "processed")`'s own
    Package 032 placement immediately after the call it describes
    actually completed.

Package 035 Amendment - One More Trace Step, No New Constructor
Dependency, No New Interaction Step:
    Per this package's own explicit Execution Trace instruction: "Add
    one trace step: CapabilityContext, action = created. No other
    trace changes." Like Package 034 before it, this package adds no
    new constructor dependency to `AgentService` and no new
    interaction step to `run()`'s own sequence - `CapabilityContext`
    is constructed by `ExecutionEngine`, not by `AgentService` (see
    argus.execution_engine.engine's own module docstring's "Package
    035 Amendment" note), and is already created, once per Task,
    inside step 6's own `execution_engine.execute()` call, before that
    call returns. `("CapabilityContext", "created")` is recorded
    honestly, after the fact, positioned between `("ExecutionEngine",
    "processed")` and `("CapabilityExecutor", "resolved")` -
    matching the Architectural Position diagram's own literal ordering
    (`Execution Engine -> Capability Context -> Capability Executor`)
    and mirroring `("CapabilityExecutor", "resolved")`'s own Package
    034 placement immediately after the work it describes actually
    happened.

Dependency Boundary - CognitivePipeline, ExecutionEngine, And
ResponseEngine Only, Plus TraceBuilder:
    Per Package 026's own explicit Dependency Rules, unchanged by
    Packages 027 and 032, `AgentService`'s constructor accepts exactly
    three injected dependencies: an `ICognitivePipeline`, (as of
    Package 032) an `IExecutionEngine`, and (as of Package 027) an
    `IResponseEngine`. It holds no reference to `IPlanner`,
    `IReasoningEngine`, `IDecisionEngine`, or any bootstrap internal -
    "All cognition flows through the Pipeline" is still true by
    construction, not by restraint, since there is no live
    Planner/Reasoning/Decision service this class could call into even
    if it wanted to; both the Execution Engine and Response Engine
    dependencies are themselves equally restricted (per each engine's
    own Dependency Rules) to depending on nothing but the Plan (and,
    for ResponseEngine, the ExecutionResult and ExecutionTrace) it is
    handed per call. Package 028's own explicit Dependency Rules add
    exactly one more permitted dependency - "AgentService may depend
    on: TraceBuilder" - which `run()` constructs directly (not
    injected via `__init__`, since a `TraceBuilder` is a short-lived,
    per-call accumulator, not a long-lived collaborator; see argus.
    trace.interfaces's own module docstring for why `TraceBuilder` is
    not a service in the first place).

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
      CognitivePipeline.run(), ExecutionEngine.execute(), and
      ResponseEngine.build_response(), none of which performs any of
      those either.
    - AgentService never modifies any object it is given or
      constructs - `AgentSession`, `AgentRequest`, `ConversationSession`,
      `PipelineResult`, `Response`, and `ExecutionTrace` are all
      already immutable value objects, so this is true by
      construction, not by anything this module does to enforce it.
      `TraceBuilder` is the one genuinely mutable object this class
      touches - see the module docstring's "Package 028 Amendment"
      note - and it is always local to a single `run()` call, never
      shared or retained across calls.
    - No AI, no LLM, no persistence, no concurrency, no natural-
      language response generation - Version 1 orchestrates entirely
      in-process, in memory, per this package's own explicit
      Constraints and Package 027's own identical Constraints.

Dependencies:
    argus.agent (AgentRequest, AgentResponse, AgentSession,
    IAgentService, and the agent exceptions), argus.pipeline.interfaces
    (ICognitivePipeline), argus.pipeline.request (PipelineRequest),
    argus.execution_engine.interfaces (IExecutionEngine) - Package 032,
    argus.response.interfaces (IResponseEngine), argus.trace.builder
    (TraceBuilder), argus.lifecycle.lifecycle (LifecycleState).
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
from argus.execution_engine.interfaces import IExecutionEngine
from argus.lifecycle.lifecycle import LifecycleState
from argus.pipeline.interfaces import ICognitivePipeline
from argus.pipeline.request import PipelineRequest
from argus.response.interfaces import IResponseEngine
from argus.trace.builder import TraceBuilder


class AgentService(IAgentService):
    """
    In-memory implementation of IAgentService.

    Purpose:
        Be the sole place ArgusOS turns an AgentRequest into an
        AgentResponse by orchestrating the existing CognitivePipeline,
        the Execution Engine (as of Package 032), and the Response
        Engine (as of Package 027) - as orchestration only - no
        reasoning, no planning, no execution, no natural-language
        response generation. See the module docstring for the full
        design rationale.

    Dependencies:
        An ICognitivePipeline implementation, an IExecutionEngine
        implementation, and an IResponseEngine implementation, all
        injected by the caller (bootstrap.py). No other constructor
        dependency - see the module docstring's "Dependency Boundary"
        note. Constructs a fresh TraceBuilder directly inside every
        run() call - not injected, since TraceBuilder is a
        short-lived, per-call accumulator, not a long-lived
        collaborator.
    """

    def __init__(
        self,
        cognitive_pipeline: ICognitivePipeline,
        execution_engine: IExecutionEngine,
        response_engine: IResponseEngine,
    ) -> None:
        self._cognitive_pipeline = cognitive_pipeline
        self._execution_engine = execution_engine
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

        trace_builder = TraceBuilder()
        trace_builder.with_step("AgentService", "entry")

        try:
            pipeline_result = self._cognitive_pipeline.run(pipeline_request)
        except Exception as error:
            raise AgentExecutionError(
                f"CognitivePipeline.run() failed for "
                f"agent_request_id={request.request_id!r}: {error}"
            ) from error

        trace_builder.with_step("CognitivePipeline", "completed")

        try:
            execution_result = self._execution_engine.execute(pipeline_result.plan)
        except Exception as error:
            raise AgentExecutionError(
                f"ExecutionEngine.execute() failed for "
                f"agent_request_id={request.request_id!r}: {error}"
            ) from error

        trace_builder.with_step("ExecutionEngine", "processed")
        trace_builder.with_step("CapabilityContext", "created")
        trace_builder.with_step("CapabilityExecutor", "resolved")
        trace_builder.with_step("ResponseEngine", "invoked")
        execution_trace = trace_builder.build()

        try:
            response = self._response_engine.build_response(
                pipeline_result.plan, execution_result, execution_trace
            )
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
