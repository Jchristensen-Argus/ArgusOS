"""
The GoalPriority enumeration for the ArgusOS Goal Framework.

Purpose:
    Represent the closed set of priority levels a Goal may carry, per
    factory/packages/038_GOAL_FRAMEWORK.md. "No ordering behavior" -
    this module defines only the enumeration itself, with no
    comparison operators and no numeric weighting of any kind; nothing
    in argus.goal ranks, sorts, or compares two GoalPriority members
    against each other. A plain `Enum` (not a `str` subclass, and
    critically not an `IntEnum` or any other ordered variant),
    mirroring every other enumeration in this codebase's own shape.

No Ordering Behavior - A Deliberate, Literal Constraint:
    Unlike GoalStatus/ProjectStatus/WorkspaceStatus (whose own members
    are unordered but also never invite ordering, since "state" is not
    naturally comparable), GoalPriority's own member names - LOW,
    NORMAL, HIGH, CRITICAL - read as an intuitively ordered scale, the
    kind of enum a caller might reasonably expect to support `<`/`>`
    comparison or sorting by severity. This package's own explicit
    instruction, "No ordering behavior," forecloses that: GoalPriority
    is implemented as a plain `Enum`, not `IntEnum` or any subclass
    that would grant ordering "for free" through inherited comparison
    operators. Members compare only for equality/identity, exactly
    like every other enum in this codebase. A future package wanting
    genuine priority-based sorting would need to add that behavior
    explicitly - it does not exist implicitly here, regardless of how
    naturally ordered the member names may read.

NORMAL Is The Default, Not LOW:
    Continuing this codebase's own "the first-listed member is the
    default" convention would make LOW the default - but "the first
    listed member is the default" is itself only ever an
    *implementation consequence* of Python's own dataclass field
    default mechanism (whichever member a field's own default
    expression names), not a rule this codebase deliberately imposes
    apart from that. For GoalPriority specifically, defaulting a new
    Goal's own priority to LOW would misrepresent what an
    unspecified priority actually means - the absence of an explicit
    priority is not evidence of low importance, it is simply
    unstated. NORMAL - the second-listed member, and the intuitive
    "no strong signal either way" baseline - is the more honest
    default for a Goal no caller has explicitly prioritized. See
    goal.py's own module docstring for the fuller reasoning; this is
    the first genuine exception to the "first-listed member is the
    default" convention anywhere in this codebase's history.

Responsibilities:
    - GoalPriority: enumerate the four priority levels a Goal's own
      `priority` field may hold.

Non-Responsibilities:
    - This module implements no ordering, comparison, sorting, or
      numeric weighting of any kind - "No ordering behavior."
    - This module implements no transition logic - priority, unlike
      status, was never described as something that transitions in
      the first place, but for the avoidance of doubt: nothing in
      argus.goal ever changes a Goal's own priority automatically.

Dependencies:
    None.
"""

from enum import Enum


class GoalPriority(Enum):
    """
    The closed set of priority levels a Goal may be assigned. None of
    these members support ordering, comparison, or sorting against
    each other - "No ordering behavior." See the module docstring for
    why this is a plain Enum, not an IntEnum or other ordered variant,
    despite the member names' own intuitively ordered reading.

    LOW: the lowest priority level.
    NORMAL: the baseline priority level - default for every Goal built
        via GoalBuilder that never calls with_priority(). See the
        module docstring for why this, not LOW, is the default.
    HIGH: an elevated priority level.
    CRITICAL: the highest priority level.
    """

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"
