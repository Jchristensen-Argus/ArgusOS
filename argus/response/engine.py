"""
ResponseEngine: in-memory transformation for the ArgusOS Response
Engine package.

Purpose:
    Implement IResponseEngine: convert a validated Plan into a
    structured Response, per
    factory/packages/027_RESPONSE_ENGINE.md. "The Response Engine
    converts a validated Plan into a structured response object. It
    does not generate AI text. It does not execute plans. It does not
    communicate with the user interface. Its responsibility is to
    transform cognitive output into a standardized response contract."

Construction Sequence - build_response() Does Exactly Three Things:
    1. Validate the Plan reference (must be a Plan instance) -
       "Validate the Plan reference" (Responsibility 2). Raises
       InvalidPlanReferenceError otherwise.
    2. Construct a Response - "Construct a Response" (Responsibility
       3). `status` is copied directly from `plan.status`; `metadata`
       is a fresh ResponseMetadata whose `extra` mapping is a plain
       copy of `plan.metadata` (see "Metadata Propagation" below).
    3. Return the Response - "Return the Response" (Responsibility 4).

    No AI, no formatting, no user interaction, no execution occurs
    anywhere in this sequence - `build_response()` never inspects
    `plan.steps`' own content beyond what `Response` itself already
    holds by reference (the whole `Plan`), never renders anything, and
    never calls any other service.

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
    (InvalidPlanReferenceError, ResponseError), argus.response.interfaces
    (IResponseEngine), argus.response.metadata (ResponseMetadata),
    argus.response.response (Response), argus.lifecycle.lifecycle
    (LifecycleState).
"""

from argus.lifecycle.lifecycle import LifecycleState
from argus.planner.plan import Plan
from argus.response.exceptions import InvalidPlanReferenceError, ResponseError
from argus.response.interfaces import IResponseEngine
from argus.response.metadata import ResponseMetadata
from argus.response.response import Response


class ResponseEngine(IResponseEngine):
    """
    In-memory implementation of IResponseEngine.

    Purpose:
        Be the sole place ArgusOS turns a validated Plan into a
        Response, as transformation only - no AI, no formatting, no
        execution, no user interaction. See the module docstring for
        the full design rationale.

    Dependencies:
        None. See the module docstring's "Dependency Boundary" note -
        `Plan` is a per-call argument to build_response(), not a
        constructor-injected collaborator.
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

    def build_response(self, plan: Plan) -> Response:
        if not isinstance(plan, Plan):
            raise InvalidPlanReferenceError(
                f"build_response() requires a Plan, got {plan!r}."
            )

        return Response(
            plan=plan,
            status=plan.status,
            metadata=ResponseMetadata(extra=dict(plan.metadata)),
        )
