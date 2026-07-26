"""
Public interface contract for the ArgusOS Cognitive Pipeline.

Purpose:
    Define ICognitivePipeline, the contract other modules depend on,
    per factory/packages/025_COGNITIVE_PIPELINE.md.

Architectural Note - Why ICognitivePipeline DOES Inherit IService:
    Unlike Packages 022/023's `ICognitiveContextBuilder`/
    `IPlanningSessionBuilder` (deliberate non-adopters - "This is not
    an IService"), this package's own work order is explicit the
    other way: "Register the Cognitive Pipeline as a core service.
    This is the first new runtime service since Package 021."
    Applying ADR-0002's criterion to `run()` independently, given this
    package's own instruction to adopt, would have reached the same
    conclusion on its own: `run()` is the one method that coordinates
    a genuinely effectful, multi-step orchestration - constructing a
    CognitiveContext, constructing a PlanningSession, and invoking the
    live Planner service - directly analogous to
    `ConversationManager.receive()` (Package 011), which is gated on
    that manager's own RUNNING state for the identical reason
    ("processing a message is exactly the kind of 'active work'
    IService's own docstring describes gating"). `run()` is gated on
    `CognitivePipeline`'s own RUNNING state for the same reason.
    This makes Package 025 the second case (after Package 019's
    Memory Integration) where an explicit adoption instruction AND
    ADR-0002's criterion, applied independently, agree - as opposed to
    Packages 018, 020, and 021, where an explicit instruction to
    adopt IService diverged from what the criterion alone would have
    concluded about gating. See
    design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md's newly
    appended Empirical Finding for this package. `CognitivePipeline`
    is registered with the Lifecycle Manager as
    `LifecycleState.REGISTERED` only (never started) by bootstrap.py,
    exactly like every other core service - gated or not.

Responsibilities:
    - ICognitivePipeline: run, plus the inherited IService contract
      (initialize / start / stop / status).

Non-Responsibilities:
    - This module implements no behavior; see
      argus.pipeline.pipeline.CognitivePipeline.
    - ICognitivePipeline does not perform reasoning, decision making,
      planning, or workflow execution itself - see this package's
      Objective and Constraints.

Dependencies:
    argus.pipeline.request (PipelineRequest), argus.pipeline.result
    (PipelineResult), argus.lifecycle.interfaces (IService).
"""

from abc import abstractmethod

from argus.lifecycle.interfaces import IService
from argus.pipeline.request import PipelineRequest
from argus.pipeline.result import PipelineResult


class ICognitivePipeline(IService):
    """
    Contract for the Cognitive Pipeline's orchestration service. See
    this module's docstring for why ICognitivePipeline inherits
    IService and why run() is gated on the RUNNING state.
    """

    @abstractmethod
    def run(self, request: PipelineRequest) -> PipelineResult:
        """Orchestrate one full pass through the cognitive pipeline
        for `request`: build a CognitiveContext from its conversation,
        build a PlanningSession around that context, invoke
        Planner.plan_session() with it, and return the resulting
        PipelineResult. Performs no reasoning, decision making, or
        planning itself - see pipeline.py's own module docstring for
        the exact orchestration sequence. Raises
        InvalidPipelineRequestError if `request` is not a
        PipelineRequest instance, or its `conversation` field is not a
        ConversationSession instance. Raises PipelineExecutionError,
        wrapping the underlying exception, if the delegated
        Planner.plan_session() call raises. Raises PipelineError if
        this pipeline's own IService state is not RUNNING."""
