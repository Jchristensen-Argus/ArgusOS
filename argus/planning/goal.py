"""
The PlanningGoal value object for the ArgusOS Planning Session.

Purpose:
    Represent a single, immutable, descriptive planning goal a
    PlanningSession carries - a name, description, and priority - per
    factory/packages/023_PLANNING_SESSION.md. A PlanningGoal is pure
    data: it does not schedule itself, rank itself against other
    goals, or know which PlanningSession (if any) it belongs to.

Priority Is Descriptive Only:
    "Priority is descriptive only. No scheduling logic." Unlike
    `DecisionRule.priority` (Package 021), which `DecisionEngine`
    actively sorts by to determine evaluation order, `PlanningGoal
    .priority` is never read, compared, or sorted by anything in this
    package - `PlanningSession.goals` preserves exactly the order
    `PlanningSessionBuilder.with_goal()` was called in (see builder.py's
    own module docstring), never re-ordered by `priority`. A future
    package's Planner integration may choose to interpret `priority`
    once the Planner is instructed to consume PlanningSession
    (Version 1 explicitly does not); this package assigns it no
    behavior at all.

No Validation Here - See builder.py:
    Like every other value object in this codebase, PlanningGoal
    performs no validation of its own fields in __post_init__.
    PlanningSessionBuilder (builder.py) validates a PlanningGoal
    before accumulating it - see builder.py's own module docstring.

Field Ordering Note:
    The work order lists this model's fields in "goal_id, name,
    description, priority" order. `name` has no sensible default (an
    unnamed goal is not a meaningful goal), so it must precede the
    defaulted fields in this dataclass's own declaration order -
    reordered to "name, goal_id, description, priority" here, the
    same "required fields before defaulted fields" reordering already
    applied to `Entity`, `ReasoningQuery`, and `DecisionRule` before
    it. The work order's own listed order is preserved in this
    docstring's Fields list below, for readability.

Responsibilities:
    - PlanningGoal: hold goal identity, a human-readable name and
      description, and a descriptive priority as an immutable value
      object.

Non-Responsibilities:
    - PlanningGoal does not register, remove, schedule, or rank
      itself against other goals - see
      argus.planning.session.PlanningSession and
      argus.planning.builder.PlanningSessionBuilder.
    - This module has no dependency on any other argus.planning
      module, matching the "pure, dependency-free leaf" precedent set
      by every other value object in this codebase.

Dependencies:
    None.
"""

import uuid
from dataclasses import dataclass, field


@dataclass(frozen=True)
class PlanningGoal:
    """
    An immutable, descriptive planning goal. See the module docstring
    for the full field semantics.

    Fields:
        name: Human-readable name. Required, non-empty (not enforced
            here - see builder.py). Not enforced unique - lookup is
            always by `goal_id`, matching every other identity-bearing
            value object in this codebase.
        goal_id: Unique identifier for this PlanningGoal. Defaults to
            a fresh uuid4 string.
        description: Human-readable explanation of what this goal is.
            Defaults to an empty string.
        priority: A descriptive-only priority value. Defaults to 0.
            Never read or acted on by this package - see the module
            docstring's "Priority Is Descriptive Only" note.
    """

    name: str
    goal_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    priority: int = 0
