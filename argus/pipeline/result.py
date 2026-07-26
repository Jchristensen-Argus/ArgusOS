"""
The PipelineResult value object for the ArgusOS Cognitive Pipeline.

Purpose:
    Represent a single, immutable snapshot of one completed pass
    through the Cognitive Pipeline - the ConversationSession it
    concerned, the CognitiveContext and PlanningSession built along
    the way, the resulting Plan, and descriptive metadata - per
    factory/packages/025_COGNITIVE_PIPELINE.md. A PipelineResult is
    pure data: it performs no orchestration itself and holds no live
    reference back to the CognitivePipeline that produced it.

No Execution Results, No Runtime State:
    "No execution results. No runtime state." PipelineResult carries
    a `Plan` (Package 015) - a planning-only artifact that has not
    been executed - never an `Execution` (Package 016) or anything
    describing whether, or how, that Plan was ever run. Producing a
    PipelineResult never touches `argus.runtime` in any way; see
    pipeline.py's own module docstring.

Every Field Is Required - This Is Always A Complete Snapshot:
    Unlike `CognitiveContext`/`PlanningSession` (Packages 022/023),
    whose every field defaults to an empty/absent value so an "empty"
    instance is directly constructible, PipelineResult has no
    meaningful "empty" shape at all - it is always the record of one
    specific, completed orchestration, and `conversation`/
    `cognitive_context`/`planning_session`/`plan` are all required,
    with no sensible default for any of them (a PipelineResult
    without a Plan, for example, is not a result of anything). Only
    `pipeline_id` (defaults to a fresh uuid4 string) and `metadata`
    (defaults to an empty mapping) have defaults, mirroring
    `Decision`'s (Package 021) own "required domain fields, defaulted
    identity/metadata fields" shape.

No Validation Here - See pipeline.py:
    Like every other value object in this codebase, PipelineResult
    performs no validation of its own fields in __post_init__ beyond
    the standard mutable-to-immutable wrapping (dict ->
    MappingProxyType). `CognitivePipeline.run()` is the only component
    that constructs a PipelineResult during normal operation - see
    pipeline.py's own module docstring for the full orchestration
    sequence that produces one.

Responsibilities:
    - PipelineResult: hold the ConversationSession, CognitiveContext,
      PlanningSession, Plan, and descriptive metadata produced by one
      completed Cognitive Pipeline run as an immutable value object.

Non-Responsibilities:
    - PipelineResult performs no orchestration, reasoning, decision
      making, planning, or execution of any kind - see this package's
      own Objective and Constraints.
    - This module depends only on argus.conversation.session
      (ConversationSession), argus.context.context (CognitiveContext),
      argus.planning.session (PlanningSession), and argus.planner.plan
      (Plan) to type its own fields - it has no dependency on
      argus.pipeline.pipeline, matching the "pure, dependency-free
      leaf" precedent set by every other value object in this
      codebase.

Dependencies:
    argus.conversation.session (ConversationSession),
    argus.context.context (CognitiveContext),
    argus.planning.session (PlanningSession),
    argus.planner.plan (Plan).
"""

import uuid
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

from argus.context.context import CognitiveContext
from argus.conversation.session import ConversationSession
from argus.planner.plan import Plan
from argus.planning.session import PlanningSession


@dataclass(frozen=True)
class PipelineResult:
    """
    An immutable snapshot of one completed Cognitive Pipeline run.
    See the module docstring for the full field semantics.

    Fields:
        conversation: The ConversationSession this run concerned.
            Required.
        cognitive_context: The CognitiveContext built during this run.
            Required.
        planning_session: The PlanningSession built during this run.
            Required.
        plan: The Plan produced by Planner.plan_session(). Required.
        pipeline_id: Unique identifier for this PipelineResult.
            Defaults to a fresh uuid4 string.
        metadata: Additional descriptive data about this run (for
            example, the originating request's own id and metadata -
            see pipeline.py's own module docstring). Defaults to an
            empty mapping.
    """

    conversation: ConversationSession
    cognitive_context: CognitiveContext
    planning_session: PlanningSession
    plan: Plan
    pipeline_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
