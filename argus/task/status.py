"""
The TaskStatus enumeration for the ArgusOS Task Model.

Purpose:
    Represent the closed set of states a Task may carry, per
    factory/packages/029_TASK_MODEL.md. "Do not implement
    transitions" - this module defines only the enumeration itself;
    nothing in argus.task moves a Task from one TaskStatus to
    another. Mirrors argus.planner.plan.PlanStatus's own shape: a
    plain `Enum` (not a `str` subclass), lowercase string values
    matching each member's name.

No Transitions, No Behavior:
    Unlike PlanStatus (whose values are actually assigned by
    Planner.create_plan()/validate_plan()), no Version 1 code anywhere
    in argus.task ever constructs a Task with any status other than
    whatever a caller explicitly supplies via TaskBuilder.with_status()
    - the default is TaskStatus.PENDING, and nothing advances it
    further. Transition rules (what follows PENDING, what makes a
    Task READY, and so on) are explicitly out of scope for this
    package - "This package introduces no execution. Only the model."

Responsibilities:
    - TaskStatus: enumerate the five states a Task's own `status`
      field may hold.

Non-Responsibilities:
    - This module implements no transition logic, no validation of
      whether a given transition is legal, and no behavior of any
      kind beyond the enumeration itself.

Dependencies:
    None.
"""

from enum import Enum


class TaskStatus(Enum):
    """
    The closed set of states a Task may be in. None of these states
    imply execution has happened or will happen automatically - no
    Version 1 code in this codebase executes a Task.

    PENDING: the Task's initial state - work has been described but
        not yet made available to whatever future package introduces
        scheduling/dispatch.
    READY: reserved for a future package that determines a Task's
        prerequisites are satisfied and it may be picked up for
        execution - no Version 1 code ever produces this state.
    COMPLETED: reserved for a future package that reports execution
        outcomes back onto a Task - no Version 1 code ever produces
        this state.
    FAILED: reserved for a future package that reports an execution
        failure back onto a Task - no Version 1 code ever produces
        this state.
    CANCELLED: reserved for a future package that reports a Task was
        withdrawn before completion - no Version 1 code ever produces
        this state.
    """

    PENDING = "pending"
    READY = "ready"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
