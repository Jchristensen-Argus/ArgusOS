"""
argus.goal - The ArgusOS Goal Framework package.

Re-exports the public surface of the Goal Framework: the immutable
value objects (Goal, GoalStatus, GoalPriority, GoalMetadata), the
mutable builder (GoalBuilder) and its interface (IGoalBuilder), and
this package's own exceptions. See
factory/packages/038_GOAL_FRAMEWORK.md for the full architectural
rationale. "A Goal represents a desired outcome within a Project.
Projects own Goals. Goals own Plans. Plans own Tasks." This package
introduces the Goal model only - no runtime behavior, no integration,
no bootstrap changes.
"""

from argus.goal.builder import GoalBuilder
from argus.goal.exceptions import GoalError, InvalidGoalError
from argus.goal.goal import Goal
from argus.goal.interfaces import IGoalBuilder
from argus.goal.metadata import GOAL_METADATA_VERSION, GoalMetadata
from argus.goal.priority import GoalPriority
from argus.goal.status import GoalStatus

__all__ = [
    "Goal",
    "GoalStatus",
    "GoalPriority",
    "GoalMetadata",
    "GOAL_METADATA_VERSION",
    "GoalBuilder",
    "IGoalBuilder",
    "GoalError",
    "InvalidGoalError",
]
