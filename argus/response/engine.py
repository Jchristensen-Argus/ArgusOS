"""
ResponseEngine: in-memory transformation for the ArgusOS Response
Engine package.

Purpose:
    Implement IResponseEngine: convert a validated Plan and the
    finished ExecutionTrace for its request into a structured
    Response, per factory/packages/027_RESPONSE_ENGINE.md, as amended
    by factory/packages/028_EXECUTION_TRACE.md. "The Response Engine
    converts a validated Plan into a structured response object. It
    does not generate AI text. It does not execute plans. It does not
    communicate with the user interface. Its responsibility is to
    transform cognitive output into a standardized response contract."

Package 028 Amendment - build_response() Also Receives The Finished
ExecutionTrace:
    "ResponseEngine shall not construct traces. It receives the
    finished trace." `build_response()`'s own signature gains a second
    parameter, `execution_trace: ExecutionTrace`, validated the same
    way `plan` already was and embedded into the returned `Response`
    unchanged. `ResponseEngine` never imports or calls
    `argus.trace.builder.TraceBuilder` - only `AgentService` does (see
    argus.agent.service's own module docstring) - so "ResponseEngine
    may depend only on: Plan" is extended, not broken: the
    `ExecutionTrace` it now also depends on is, like `Plan`, a
    per-call argument, not a constructor-injected collaborator or a
    service it calls into.

Package 032 Amendment - build_response() Also Receives The
ExecutionResult:
    "It receives ExecutionResult. It does not construct one."
    `build_response()`'s own signature gains a third parameter,
    `execution_result: ExecutionResult`, validated the same way `plan`
    and `execution_trace` already were and embedded into the returned
    `Response` unchanged. `ResponseEngine` never imports or calls
    `argus.execution_engine.engine.ExecutionEngine` - only
    `AgentService` does (see argus.agent.service's own module
    docstring) - continuing the identical "per-call argument, not a
    constructor-injected collaborator or a service it calls into"
    shape already established for `execution_trace` (028).

Construction Sequence - build_response() Does Exactly Five Things:
    1. Validate the Plan reference (must be a Plan instance) -
       "Validate the Plan reference" (Responsibility 2). Raises
       InvalidPlanReferenceError otherwise.
    2. Validate the ExecutionResult reference (must be an
       ExecutionResult instance) - added by Package 032, mirroring
       step 1's own validation shape. Raises
       InvalidExecutionResultError otherwise.
    3. Validate the ExecutionTrace reference (must be an ExecutionTrace
       instance) - added by Package 028, mirroring step 1's own
       validation shape. Raises InvalidExecutionTraceError otherwise.
    4. Construct a Response - "Construct a Response" (Responsibility
       3). `status` is copied directly from `plan.status`; `metadata`
       is a fresh ResponseMetadata whose `extra` mapping is a plain
       copy of `plan.metadata` (see "Metadata Propagation" below);
       `execution_result` and `execution_trace` are both embedded
       exactly as received, unmodified.
    5. Return the Response - "Return the Response" (Responsibility 4).

    No AI, no formatting, no user interaction, no execution occurs
    anywhere in this sequence - `build_response()` never inspects
    `plan.steps`' own content beyond what `Response` itself already
    holds by reference (the whole `Plan`), never inspects
    `execution_result.completed_tasks`'/`.failed_tasks`' own content
    or `execution_trace.steps`' own content either, never renders
    anything, and never calls any other service.

Dependency Boundary - Plan Only, Nothing Else, Not Even At
Construction:
    Per this package's own explicit Dependency Rules, "ResponseEngine
    may depend only on: Plan" - and `Plan` is not a live service to
    inject at construction time, but a per-call argument to
    `build_response()` itself. `ResponseEngine.__init__()` therefore
    takes no constructor dependency at all - no `IEventBus`, no
    `IPlanner`, no `ICognitivePipeline`, no `IAgentService`, nothing -
    the first core service in this codebase for which that is true.
    "ResponseEngine shall not depend on: Pipeline, Planner, Reasoning,
    Decision, Agent, Bootstrap internals" is true by construction, not
    by restraint, since there is no live service reference anywhere in
    this class for it to call into even if it wanted to.

Metadata Propagation:
    `ResponseEngine` has no access to whatever metadata an
    AgentRequest/PipelineRequest originally carried - that chain
    terminates at `PipelineResult.metadata` (Package 025), which
    `ResponseEngine` never sees. The one metadata source available to
    it is the `Plan` it is given directly: `plan.metadata`, already
    carrying `planning_session_id`, `cognitive_context_id`, and
    `constraints` forward from `Planner.plan_session()` (Package 024).
    `build_response()` copies `dict(plan.metadata)` into the returned
    `Response.metadata.extra` unchanged - plain data propagation, not
    business logic; `ResponseEngine` never inspects, branches on, or
    otherwise interprets any metadata value, matching
    `CognitivePipeline`'s (Package 025) and `AgentService`'s (Package
    026) own identical restraint one and two layers below.

Responsibilities:
    - build_response(): transform one Plan into one Response, per the
      sequence above.
    - initialize / start / stop / status, per the inherited IService
      contract. build_response() is *not* gated on the engine's own
      lifecycle state being RUNNING - see interfaces.py's own
      Architectural Note for the full reasoning.

Non-Responsibilities:
    - ResponseEngine never implements reasoning, decision making,
      planning, or execution itself - it only reads fields already
      present on the Plan it is given.
    - ResponseEngine never modifies any object it is given or
      constructs - `Plan` is already an immutable value object, so
      this is true by construction, not by anything this module does
      to enforce it.
    - No AI, no LLM, no formatting, no rendering, no user interaction,
      no persistence, no concurrency - Version 1 transforms entirely
      in-process, in memory, per this package's own explicit
      Constraints.

Dependencies:
    argus.planner.plan (Plan), argus.response.exceptions
    (InvalidExecutionResultError, InvalidExecutionTraceError,
    InvalidPlanReferenceError, ResponseError), argus.response.interfaces
    (IResponseEngine), argus.response.metadata (ResponseMetadata),
    argus.response.response (Response), argus.trace.trace
    (ExecutionTrace), argus.execution_engine.result (ExecutionResult) -
    Package 032, argus.lifecycle.lifecycle (LifecycleState).
"""

from argus.execution_engine.result import ExecutionResult
from argus.lifecycle.lifecycle import LifecycleState
from argus.planner.plan import Plan
from argus.response.exceptions import (
    InvalidExecutionResultError,
    InvalidExecutionTraceError,
    InvalidPlanReferenceError,
    ResponseError,
)
from argus.response.interfaces import IResponseEngine
from argus.response.metadata import ResponseMetadata
from argus.response.response import Response
from argus.trace.trace import ExecutionTrace


class ResponseEngine(IResponseEngine):
    """
    In-memory implementation of IResponseEngine.

    Purpose:
        Be the sole place ArgusOS turns a validated Plan into a
        Response, as transformation only - no AI, no formatting, no
        execution, no user interaction. See the module docstring for
        the full design rationale.

    Dependencies:
        None injected at construction. See the module docstring's
        "Dependency Boundary" note - `Plan` and (as of Package 028)
        `ExecutionTrace` are both per-call arguments to
        build_response(), not constructor-injected collaborators.
    """

    def __init__(self) -> None:
        self._state: LifecycleState = LifecycleState.CREATED

    # -- IService (see interfaces.py's Architectural Note:
    #    build_response() is never gated) -----------------------------

    def initialize(self) -> None:
        if self._state != LifecycleState.CREATED:
            raise ResponseError(
                f"Cannot initialize: ResponseEngine is {self._state.name}, "
                f"expected CREATED."
            )
        self._state = LifecycleState.INITIALIZING

    def start(self) -> None:
        if self._state != LifecycleState.INITIALIZING:
            raise ResponseError(
                f"Cannot start: ResponseEngine is {self._state.name}, "
                f"expected INITIALIZING."
            )
        self._state = LifecycleState.RUNNING

    def stop(self) -> None:
        if self._state != LifecycleState.RUNNING:
            raise ResponseError(
                f"Cannot stop: ResponseEngine is {self._state.name}, expected RUNNING."
            )
        self._state = LifecycleState.STOPPING
        self._state = LifecycleState.STOPPED

    def status(self) -> LifecycleState:
        return self._state

    # -- IResponseEngine --------------------------------------------------

    def build_response(
        self,
        plan: Plan,
        execution_result: ExecutionResult,
        execution_trace: ExecutionTrace,
    ) -> Response:
        if not isinstance(plan, Plan):
            raise InvalidPlanReferenceError(
                f"build_response() requires a Plan, got {plan!r}."
            )
        if not isinstance(execution_result, ExecutionResult):
            raise InvalidExecutionResultError(
                f"build_response() requires an ExecutionResult, got "
                f"{execution_result!r}."
            )
        if not isinstance(execution_trace, ExecutionTrace):
            raise InvalidExecutionTraceError(
                f"build_response() requires an ExecutionTrace, got "
                f"{execution_trace!r}."
            )

        return Response(
            plan=plan,
            execution_result=execution_result,
            execution_trace=execution_trace,
            status=plan.status,
            metadata=ResponseMetadata(extra=dict(plan.metadata)),
        )
