"""
Public interface contract for the ArgusOS Agent Session package.

Purpose:
    Define IAgentService, the contract other modules depend on, per
    factory/packages/026_AGENT_SESSION.md, as amended by
    factory/packages/027_RESPONSE_ENGINE.md's own explicit "Agent
    Integration" instruction (run() now also invokes
    ResponseEngine.build_response(); AgentResponse now wraps a
    Response instead of a PipelineResult),
    factory/packages/028_EXECUTION_TRACE.md's own explicit
    "Integration" instruction (run() now also builds and records an
    ExecutionTrace as the request moves through the Cognitive Pipeline
    and the Response Engine), and
    factory/packages/032_EXECUTION_ENGINE.md's own explicit
    "Integration" instruction (run() now also invokes
    ExecutionEngine.execute() between the Cognitive Pipeline and the
    Response Engine stages, and records one more ExecutionTrace step
    for it - see response.py's and service.py's own module docstrings
    for the full amendment). This abstract method's own signature is
    unchanged by Packages 028 or 032 - it still accepts an
    AgentRequest and returns an AgentResponse - the trace is built and
    recorded, and the Execution Engine invoked, entirely inside the
    implementation.

Architectural Note - Why IAgentService DOES Inherit IService:
    "Register AgentService as the next core service" is the direct
    analogue, one layer up, of Package 025's own "Register the
    Cognitive Pipeline as a core service" instruction -
    ICognitivePipeline's own Architectural Note (argus/pipeline/
    interfaces.py) already established that "core service" is this
    codebase's own shorthand for "adopts IService," and this package's
    Testing section names "lifecycle behavior" as an explicit test
    category, confirming the same reading here. Applying ADR-0002's
    criterion to `run()` independently, given this package's own
    instruction to adopt, reaches the same conclusion on its own:
    `run()` is the one method that coordinates a genuinely effectful,
    multi-step orchestration - validating an AgentRequest, building a
    PipelineRequest, and invoking the live CognitivePipeline service -
    directly analogous to CognitivePipeline.run() itself (Package
    025), which is gated on that pipeline's own RUNNING state for the
    identical reason. `run()` is gated on `AgentService`'s own RUNNING
    state for the same reason. This makes Package 026 the **third**
    case (after Package 019's Memory Integration and Package 025's
    Cognitive Pipeline) where an explicit adoption instruction AND
    ADR-0002's criterion, applied independently, agree - as opposed to
    Packages 018, 020, and 021, where an explicit instruction to adopt
    IService diverged from what the criterion alone would have
    concluded about gating. See
    design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md's newly
    appended Empirical Finding for this package. `AgentService` is
    registered with the Lifecycle Manager as
    `LifecycleState.REGISTERED` only (never started) by bootstrap.py,
    exactly like every other core service - gated or not.

Responsibilities:
    - IAgentService: run, plus the inherited IService contract
      (initialize / start / stop / status).

Non-Responsibilities:
    - This module implements no behavior; see
      argus.agent.service.AgentService.
    - IAgentService does not perform reasoning, decision making,
      planning, or execution itself - see this package's Objective
      and Constraints.

Dependencies:
    argus.agent.request (AgentRequest), argus.agent.response
    (AgentResponse), argus.lifecycle.interfaces (IService).
"""

from abc import abstractmethod

from argus.agent.request import AgentRequest
from argus.agent.response import AgentResponse
from argus.lifecycle.interfaces import IService


class IAgentService(IService):
    """
    Contract for the Agent Session's orchestration service. See this
    module's docstring for why IAgentService inherits IService and why
    run() is gated on the RUNNING state.
    """

    @abstractmethod
    def run(self, request: AgentRequest) -> AgentResponse:
        """Accept `request`, invoke CognitivePipeline.run() with a
        PipelineRequest built from it, invoke ExecutionEngine.execute()
        with the resulting Plan (Package 032), build and record an
        ExecutionTrace across the Cognitive Pipeline, Execution Engine,
        and Response Engine stages (Packages 028 and 032), invoke
        ResponseEngine.build_response() with the resulting Plan, the
        ExecutionResult, and the finished ExecutionTrace, and return
        the resulting AgentResponse, wrapping the standardized
        Response unmodified (Package 027's own "Agent Integration"
        amendment to Package 026's original PipelineResult-wrapping
        behavior). Performs no reasoning, decision making, planning,
        or execution itself - see service.py's own module docstring
        for the exact orchestration sequence. Raises
        InvalidAgentRequestError if `request` is not an AgentRequest
        instance, its `session` field is not an AgentSession instance,
        or its `conversation` field is not a ConversationSession
        instance. Raises AgentExecutionError, wrapping the underlying
        exception, if the delegated CognitivePipeline.run() call, the
        delegated ExecutionEngine.execute() call, or the delegated
        ResponseEngine.build_response() call raises. Raises AgentError
        if this service's own IService state is not RUNNING."""
