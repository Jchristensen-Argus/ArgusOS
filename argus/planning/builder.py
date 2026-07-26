"""
The PlanningSessionBuilder for the ArgusOS Planning Session.

Purpose:
    Provide a mutable, fluent way to accumulate a PlanningSession's
    fields one at a time before producing a single immutable
    PlanningSession snapshot, per
    factory/packages/023_PLANNING_SESSION.md. "Builder is mutable.
    PlanningSession is immutable. Each call to build() returns an
    independent immutable snapshot." Every `with_*` method validates
    its own input, then mutates this builder's internal accumulator
    state and returns `self`, so calls chain:
    `PlanningSessionBuilder().with_context(ctx).with_goal(g1).build()`.
    Directly mirrors argus.context.builder.ContextBuilder's (Package
    022) own shape, accumulation rules, and validation discipline -
    the same builder pattern applied one layer further into the
    cognitive pipeline.

Accumulate, Except For Context:
    with_goal(), with_constraint(), and with_metadata() each
    accumulate - calling with_goal() three times with three different
    PlanningGoal objects produces a PlanningSession whose goals holds
    all three, in call order. with_context() is the one exception:
    cognitive_context is a single scalar field, not a collection, so
    calling it more than once simply overwrites the previous value -
    the last call before build() wins. This mirrors
    ContextBuilder.with_conversation()'s (022) identical
    "singular field is overwritten, collection field accumulates"
    distinction.

with_metadata() Only Ever Populates `extra`:
    PlanningMetadata's `created_at`, `version`, and `correlation_id`
    fields are system-assigned at PlanningSession construction time
    (see metadata.py's own module docstring) - PlanningSessionBuilder
    exposes no way to override them. with_metadata(key, value) adds
    one key/value pair to the eventual PlanningMetadata.extra mapping;
    calling it multiple times with different keys accumulates, and
    calling it twice with the same key overwrites that key's value -
    the last call wins, the same last-call-wins rule with_context
    uses.

Validation Lives Here, Not On PlanningSession/PlanningGoal/
PlanningConstraint:
    See session.py's own module docstring - PlanningSession performs
    no validation of its own; every `with_*` method below validates
    its argument before accumulating it, raising
    InvalidPlanningSessionError for malformed input. build() itself
    performs no additional validation - by the time build() runs,
    every accumulated value has already been validated at the point
    it was added.

Independent Snapshots:
    build() constructs a fresh PlanningSession (and a fresh
    PlanningMetadata) from this builder's current accumulated state
    every time it is called. Continuing to call `with_*` methods on
    the same builder after calling build() - or calling build() more
    than once - never mutates a PlanningSession already returned by an
    earlier build() call, since PlanningSession's own __post_init__
    copies every mutable sequence it is given (see session.py).

Responsibilities:
    - PlanningSessionBuilder: accumulate a PlanningSession's fields
      one at a time, with per-field validation, and produce an
      immutable PlanningSession snapshot on build().

Non-Responsibilities:
    - PlanningSessionBuilder performs no planning, goal validation
      (in the "is this goal achievable" sense), plan optimization, or
      workflow execution - it only validates and accumulates plain
      data. "shall NOT: validate goals" refers to this broader sense;
      the type-check performed on a `with_goal()` argument below is
      construction-time input validation only, the same category of
      check every other builder/registry in this codebase performs on
      its own inputs (for example,
      DecisionEngine.register_rule()'s own isinstance check on
      `rule`), not goal-content validation.
    - This module depends on argus.planning.session (PlanningSession),
      argus.planning.metadata (PlanningMetadata),
      argus.planning.exceptions (InvalidPlanningSessionError),
      argus.planning.interfaces (IPlanningSessionBuilder),
      argus.planning.goal (PlanningGoal),
      argus.planning.constraint (PlanningConstraint), and
      argus.context.context (CognitiveContext) for with_context()'s
      own type check.

Dependencies:
    argus.planning.session (PlanningSession),
    argus.planning.metadata (PlanningMetadata),
    argus.planning.exceptions (InvalidPlanningSessionError),
    argus.planning.interfaces (IPlanningSessionBuilder),
    argus.planning.goal (PlanningGoal),
    argus.planning.constraint (PlanningConstraint),
    argus.context.context (CognitiveContext).
"""

from typing import Any, Dict, List, Optional

from argus.context.context import CognitiveContext
from argus.planning.constraint import PlanningConstraint
from argus.planning.exceptions import InvalidPlanningSessionError
from argus.planning.goal import PlanningGoal
from argus.planning.interfaces import IPlanningSessionBuilder
from argus.planning.metadata import PlanningMetadata
from argus.planning.session import PlanningSession


def _require_non_empty_string(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise InvalidPlanningSessionError(f"{label} must be a non-empty string, got {value!r}.")
    return value


class PlanningSessionBuilder(IPlanningSessionBuilder):
    """
    A mutable, fluent builder for PlanningSession. See the module
    docstring for the full accumulation and validation semantics.
    """

    def __init__(self) -> None:
        self._cognitive_context: Optional[CognitiveContext] = None
        self._goals: List[PlanningGoal] = []
        self._constraints: List[PlanningConstraint] = []
        self._metadata_extra: Dict[str, Any] = {}

    def with_context(self, cognitive_context: CognitiveContext) -> "PlanningSessionBuilder":
        if not isinstance(cognitive_context, CognitiveContext):
            raise InvalidPlanningSessionError(
                f"cognitive_context must be a CognitiveContext instance, "
                f"got {cognitive_context!r}."
            )
        self._cognitive_context = cognitive_context
        return self

    def with_goal(self, goal: PlanningGoal) -> "PlanningSessionBuilder":
        if not isinstance(goal, PlanningGoal):
            raise InvalidPlanningSessionError(
                f"goal must be a PlanningGoal instance, got {goal!r}."
            )
        self._goals.append(goal)
        return self

    def with_constraint(self, constraint: PlanningConstraint) -> "PlanningSessionBuilder":
        if not isinstance(constraint, PlanningConstraint):
            raise InvalidPlanningSessionError(
                f"constraint must be a PlanningConstraint instance, got {constraint!r}."
            )
        self._constraints.append(constraint)
        return self

    def with_metadata(self, key: str, value: Any) -> "PlanningSessionBuilder":
        validated_key = _require_non_empty_string(key, label="metadata key")
        self._metadata_extra[validated_key] = value
        return self

    def build(self) -> PlanningSession:
        return PlanningSession(
            cognitive_context=self._cognitive_context,
            goals=tuple(self._goals),
            constraints=tuple(self._constraints),
            metadata=PlanningMetadata(extra=dict(self._metadata_extra)),
        )
