"""
CognitivePipeline: in-memory orchestration for the ArgusOS Cognitive
Pipeline.

Purpose:
    Implement ICognitivePipeline: coordinate the existing cognitive
    architecture - a ConversationSession, a CognitiveContext, a
    PlanningSession, and the Planner - to turn one PipelineRequest
    into one PipelineResult, per
    factory/packages/025_COGNITIVE_PIPELINE.md. "The Cognitive
    Pipeline orchestrates the existing cognitive architecture. It
    does not introduce new reasoning. It does not introduce AI. It
    does not change planner behavior. Its responsibility is
    orchestration only."

Orchestration Sequence - run() Does Exactly Six Things:
    1. Accept a PipelineRequest (validated: must be a PipelineRequest
       instance whose `conversation` is a ConversationSession).
    2. Obtain the Conversation - simply `request.conversation` itself;
       the request already carries the existing ConversationSession
       (see request.py's own "Never Raw Text" note), so there is
       nothing further to fetch or construct here.
    3. Build a CognitiveContext - via a fresh, local `ContextBuilder`,
       calling `with_conversation(conversation.id)` and one
       `with_metadata()` call per `request.metadata` entry (plus
       `request_id`, for traceability - see "Metadata Propagation"
       below).
    4. Build a PlanningSession - via a fresh, local
       `PlanningSessionBuilder`, calling `with_context(cognitive_context)`
       and the same metadata propagation `with_metadata()` calls.
       Version 1 adds no goals and no constraints - this package
       "does not introduce new reasoning," and has no Reasoning Engine
       or Decision Engine dependency to derive any from (see
       "Dependency Boundary" below).
    5. Invoke `planner.plan_session(planning_session)` - the one live
       service call this method makes. Any exception it raises is
       caught and re-raised as PipelineExecutionError, wrapping the
       original (`raise ... from error`) - no partial PipelineResult
       is ever returned.
    6. Return a PipelineResult assembled from the conversation,
       cognitive_context, planning_session, and the Plan
       plan_session() returned, plus propagated metadata.

    Every event this produces (`PLAN_CREATED` once, `PLAN_UPDATED`
    once per goal - zero, in Version 1, since no goals are added) is
    published by `Planner.plan_session()`'s own delegated
    `create_plan()`/`add_step()` calls, exactly as documented in
    Package 024's own DEVLOG entry - `CognitivePipeline` itself
    publishes nothing at all. "No new EventTypes. Reuse existing
    planner behavior." "Pipeline shall not: ... perform direct event
    publication" - satisfied by construction: this class holds no
    IEventBus reference of any kind, since it has nothing to publish.

Dependency Boundary - Planner Only, Builders Only At Construction
Time:
    Per this package's own explicit Dependency Rules, `CognitivePipeline`'s
    constructor accepts exactly one dependency: an `IPlanner`. It
    holds no reference to `IKnowledgeGraph`, `IMemoryIntegration`,
    `IReasoningEngine`, `IDecisionEngine`, or `IConversationManager` -
    "It does not introduce new reasoning" is true by construction,
    not by restraint, since there is no live reasoning/decision/
    knowledge/memory service this class could call into even if it
    wanted to. `ContextBuilder`/`PlanningSessionBuilder` are
    constructed fresh, used, and discarded entirely within a single
    `run()` call - never stored as instance state, never accepted as
    constructor parameters - satisfying "Pipeline shall not: depend on
    builders outside of construction" by never holding one outside the
    single call that needs it.

Metadata Propagation:
    Every key/value pair in `request.metadata`, plus `request_id`
    itself, is passed through `with_metadata()` to both the
    CognitiveContext being built and the PlanningSession being built -
    so a caller's own metadata is genuinely observable at every layer
    of the result, not silently dropped at the pipeline boundary. The
    same data is also recorded directly in the returned
    `PipelineResult.metadata` itself. This is plain data propagation,
    not business logic - `CognitivePipeline` never inspects, branches
    on, or otherwise interprets any metadata value; it only forwards
    what it was given, per "The pipeline performs orchestration only.
    No business logic."

Why No Goals Or Constraints In Version 1:
    A `PlanningSession` built by this pipeline always has empty
    `goals`/`constraints` tuples - there is no Reasoning Engine or
    Decision Engine call anywhere in this package to derive either
    from, per the Dependency Rules above and this package's own
    Objective. The resulting `Plan` (via `Planner.plan_session()`,
    Package 024) therefore always has zero steps in Version 1 - "It
    does not change planner behavior," and `plan_session()`'s own
    behavior for a goal-less session (a Plan with no steps) is exactly
    what it already was before this package existed.

Responsibilities:
    - run(): orchestrate one full pipeline pass, per the sequence
      above.
    - initialize / start / stop / status, per the inherited IService
      contract. run() *is* gated on the pipeline's own lifecycle state
      being RUNNING - see interfaces.py's own Architectural Note.

Non-Responsibilities:
    - CognitivePipeline never implements reasoning, decision making,
      planning, or workflow execution itself - it only calls
      Planner.plan_session(), which itself performs no execution
      either (Package 015's own Objective).
    - CognitivePipeline never modifies any object it is given or
      constructs - `ConversationSession`, `CognitiveContext`,
      `PlanningSession`, and `Plan` are all already immutable value
      objects, so this is true by construction, not by anything this
      module does to enforce it.
    - No AI, no LLM, no persistence, no concurrency - Version 1 orchestrates
      entirely in-process, in memory, per this package's own explicit
      Constraints.

Dependencies:
    argus.pipeline (PipelineRequest, PipelineResult, ICognitivePipeline,
    and the pipeline exceptions), argus.planner.interfaces (IPlanner),
    argus.context.builder (ContextBuilder), argus.planning.builder
    (PlanningSessionBuilder).
"""

from typing import Any, Dict

from argus.context.builder import ContextBuilder
from argus.conversation.session import ConversationSession
from argus.lifecycle.lifecycle import LifecycleState
from argus.pipeline.exceptions import (
    InvalidPipelineRequestError,
    PipelineError,
    PipelineExecutionError,
)
from argus.pipeline.interfaces import ICognitivePipeline
from argus.pipeline.request import PipelineRequest
from argus.pipeline.result import PipelineResult
from argus.planner.interfaces import IPlanner
from argus.planning.builder import PlanningSessionBuilder


class CognitivePipeline(ICognitivePipeline):
    """
    In-memory implementation of ICognitivePipeline.

    Purpose:
        Be the sole place ArgusOS turns a PipelineRequest into a
        PipelineResult by orchestrating the existing CognitiveContext/
        PlanningSession/Planner components, as orchestration only - no
        new reasoning, no AI, no planner behavior change. See the
        module docstring for the full design rationale.

    Dependencies:
        An IPlanner implementation, injected by the caller
        (bootstrap.py). No other constructor dependency - see the
        module docstring's "Dependency Boundary" note.
    """

    def __init__(self, planner: IPlanner) -> None:
        self._planner = planner
        self._state: LifecycleState = LifecycleState.CREATED

    # -- IService (see interfaces.py's Architectural Note: run() is
    #    genuinely gated on RUNNING) -------------------------------

    def initialize(self) -> None:
        if self._state != LifecycleState.CREATED:
            raise PipelineError(
                f"Cannot initialize: CognitivePipeline is {self._state.name}, "
                f"expected CREATED."
            )
        self._state = LifecycleState.INITIALIZING

    def start(self) -> None:
        if self._state != LifecycleState.INITIALIZING:
            raise PipelineError(
                f"Cannot start: CognitivePipeline is {self._state.name}, "
                f"expected INITIALIZING."
            )
        self._state = LifecycleState.RUNNING

    def stop(self) -> None:
        if self._state != LifecycleState.RUNNING:
            raise PipelineError(
                f"Cannot stop: CognitivePipeline is {self._state.name}, expected RUNNING."
            )
        self._state = LifecycleState.STOPPING
        self._state = LifecycleState.STOPPED

    def status(self) -> LifecycleState:
        return self._state

    # -- ICognitivePipeline -------------------------------------------

    def run(self, request: PipelineRequest) -> PipelineResult:
        if self._state != LifecycleState.RUNNING:
            raise PipelineError(
                f"Cannot run: CognitivePipeline is {self._state.name}, expected RUNNING."
            )
        if not isinstance(request, PipelineRequest):
            raise InvalidPipelineRequestError(
                f"run() requires a PipelineRequest, got {request!r}."
            )
        if not isinstance(request.conversation, ConversationSession):
            raise InvalidPipelineRequestError(
                f"PipelineRequest.conversation must be a ConversationSession, "
                f"got {request.conversation!r}."
            )

        conversation = request.conversation
        propagated_metadata = self._propagated_metadata(request)

        context_builder = ContextBuilder().with_conversation(conversation.id)
        for key, value in propagated_metadata.items():
            context_builder = context_builder.with_metadata(key, value)
        cognitive_context = context_builder.build()

        session_builder = PlanningSessionBuilder().with_context(cognitive_context)
        for key, value in propagated_metadata.items():
            session_builder = session_builder.with_metadata(key, value)
        planning_session = session_builder.build()

        try:
            plan = self._planner.plan_session(planning_session)
        except Exception as error:
            raise PipelineExecutionError(
                f"plan_session() failed for planning_session.id={planning_session.session_id!r}: "
                f"{error}"
            ) from error

        return PipelineResult(
            conversation=conversation,
            cognitive_context=cognitive_context,
            planning_session=planning_session,
            plan=plan,
            metadata=propagated_metadata,
        )

    # -- internals ------------------------------------------------------

    def _propagated_metadata(self, request: PipelineRequest) -> Dict[str, Any]:
        metadata: Dict[str, Any] = {"request_id": request.request_id}
        metadata.update(dict(request.metadata))
        return metadata
