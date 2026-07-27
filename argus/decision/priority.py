"""
The DecisionRecordPriority enumeration for the ArgusOS Decision
Framework.

Purpose:
    Represent the closed set of priority levels a DecisionRecord may
    carry, per factory/packages/039_DECISION_FRAMEWORK.md. "Default
    should follow the same convention established in the Goal
    framework." A plain `Enum` (not a `str` subclass, and critically
    not an `IntEnum` or any other ordered variant), mirroring
    argus.goal.priority.GoalPriority's own identical shape.

Naming Note - DecisionRecordPriority, Not DecisionPriority:
    See status.py's own module docstring for the full reasoning: this
    package's own model is named DecisionRecord throughout, to avoid
    colliding with Package 021's own pre-existing, unrelated Decision
    Engine concept, whose own bare `Decision` name remains canonical
    within argus.decision per explicit Founder direction.

No Ordering Behavior - Mirrors GoalPriority Exactly:
    LOW, NORMAL, HIGH, CRITICAL read as an intuitively ordered scale,
    the kind of enum a caller might reasonably expect to support
    `<`/`>` comparison or sorting by severity. DecisionRecordPriority
    is implemented as a plain `Enum`, not `IntEnum` or any subclass
    that would grant ordering "for free" through inherited comparison
    operators - members compare only for equality/identity, exactly
    like GoalPriority (038) and every other enum in this codebase.

NORMAL Is The Default, Not LOW - Explicitly Instructed To Match
GoalPriority:
    This package's own work order states outright: "Default should
    follow the same convention established in the Goal framework."
    GoalPriority's own default is NORMAL, not LOW - the first genuine
    exception to this codebase's "first-listed member is the default"
    convention (038), adopted there because defaulting an unprioritized
    Goal to LOW would misrepresent "priority never specified" as
    "known to be low priority." That same reasoning applies identically
    to an unprioritized DecisionRecord, and this package's own
    instruction makes following it explicit rather than inferred.
    DecisionRecordPriority therefore also defaults to NORMAL.

Responsibilities:
    - DecisionRecordPriority: enumerate the four priority levels a
      DecisionRecord's own `priority` field may hold.

Non-Responsibilities:
    - This module implements no ordering, comparison, sorting, or
      numeric weighting of any kind - "No ordering behavior."
    - This module implements no transition logic.

Dependencies:
    None.
"""

from enum import Enum


class DecisionRecordPriority(Enum):
    """
    The closed set of priority levels a DecisionRecord may be
    assigned. None of these members support ordering, comparison, or
    sorting against each other - "No ordering behavior." See the
    module docstring for why this is a plain Enum, not an IntEnum or
    other ordered variant, despite the member names' own intuitively
    ordered reading.

    LOW: the lowest priority level.
    NORMAL: the baseline priority level - default for every
        DecisionRecord built via DecisionRecordBuilder that never
        calls with_priority(). See the module docstring for why this,
        not LOW, is the default.
    HIGH: an elevated priority level.
    CRITICAL: the highest priority level.
    """

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"
