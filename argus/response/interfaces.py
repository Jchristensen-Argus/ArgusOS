"""
Public interface contract for the ArgusOS Response Engine.

Purpose:
    Define IResponseEngine, the contract other modules depend on, per
    factory/packages/027_RESPONSE_ENGINE.md.

Architectural Note - IResponseEngine Inherits IService, But No Method
Is Gated:
    "Register: ResponseEngine" (this package's own Bootstrap section)
    and this package's own Testing section naming "lifecycle" as an
    explicit verification category are read the same way
    `ICognitivePipeline`'s (Package 025) and `IAgentService`'s
    (Package 026) own "Register ... as a core service" instructions
    were read - "core service" is this codebase's own established
    shorthand for "adopts IService." Applying ADR-0002's criterion to
    this package's actual method independently, however, would not
    have suggested adoption: `build_response()` is a synchronous,
    in-memory transformation of a Plan the caller already supplies -
    no external call, no dispatch to another live service, and no
    phase distinction it could plausibly be gated on, since
    "ResponseEngine may depend only on: Plan" leaves it with no live
    collaborator to gate access to in the first place. This is
    architecturally the same shape as `KnowledgeGraph` (Package 018),
    `ReasoningEngine` (Package 020), and `DecisionEngine` (Package
    021) - each explicitly instructed to adopt IService, each with no
    method gated on the RUNNING state - and takes that shape one step
    further: unlike those three, which each hold at least one
    constructor-injected collaborator (an `IEventBus`, in every case)
    even though their own domain methods never call into it for
    gating purposes, `ResponseEngine.__init__()` takes no constructor
    dependency at all - the first core service in this codebase for
    which that is true. Per the explicit instruction, `IResponseEngine`
    DOES inherit `IService` and `ResponseEngine` implements the full
    initialize()/start()/stop()/status() lifecycle boilerplate - but
    `build_response()` is not gated on the RUNNING state, exactly
    mirroring `KnowledgeGraph`'s, `ReasoningEngine`'s, and
    `DecisionEngine`'s identical shape. This makes `ResponseEngine` the
    **fifth** such zero-gated adopter in this codebase (after
    IntentRouter, Package 009) and the **fourth** case where an
    explicit instruction to adopt IService diverges from what
    ADR-0002's own criterion would independently conclude (after
    Packages 018, 020, and 021) - see
    design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md's newly
    appended Empirical Finding for this package, which also notes this
    breaks the three-divergent/three-convergent tie Package 026's own
    finding established, back toward divergent (four to three).
    `ResponseEngine` is registered with the Lifecycle Manager as
    `LifecycleState.REGISTERED` only (never started) by bootstrap.py,
    exactly like every other core service - gated or not. Because
    `build_response()` is never gated, callers (including
    `AgentService`) may call it regardless of `ResponseEngine`'s own
    lifecycle state - the same calling convention already used
    throughout this codebase wherever one service calls into another
    zero-gated adopter (for example, `ReasoningEngine` calling
    `KnowledgeGraph`'s own ungated methods directly, with no lifecycle
    check of its own).

Responsibilities:
    - IResponseEngine: build_response, plus the inherited IService
      contract (initialize / start / stop / status).

Non-Responsibilities:
    - This module implements no behavior; see
      argus.response.engine.ResponseEngine.
    - IResponseEngine does not generate AI text, execute Plans, format
      output, or interact with any user interface - see this
      package's Objective and Constraints.

Dependencies:
    argus.planner.plan (Plan), argus.response.response (Response),
    argus.lifecycle.interfaces (IService).
"""

from abc import abstractmethod

from argus.lifecycle.interfaces import IService
from argus.planner.plan import Plan
from argus.response.response import Response


class IResponseEngine(IService):
    """
    Contract for the Response Engine's transformation service. See
    this module's docstring for why IResponseEngine inherits IService
    and why build_response() is never gated.
    """

    @abstractmethod
    def build_response(self, plan: Plan) -> Response:
        """Accept a validated `plan`, validate the Plan reference, and
        construct and return the resulting Response - a standardized,
        non-AI, non-rendered snapshot of `plan` and its own planning
        status. Performs no reasoning, planning, or execution itself -
        see engine.py's own module docstring for the exact
        construction sequence. Raises InvalidPlanReferenceError if
        `plan` is not a Plan instance."""
