"""
Exceptions for the ArgusOS Goal Framework package.

Purpose:
    Define the error types argus.goal itself can raise. Per
    factory/packages/038_GOAL_FRAMEWORK.md, "Goals are passive domain
    objects only" - this package's own errors are therefore limited
    to malformed builder input, never scheduling, execution, or
    ownership-relationship failures (this package implements none of
    those).

Responsibilities:
    - GoalError: the base exception for this package.
    - InvalidGoalError: raised by GoalBuilder's with_*() methods when
      given a malformed argument.

Non-Responsibilities:
    - This module performs no logic beyond defining exception types -
      it holds no state and makes no decisions about when to raise.

Dependencies:
    None.
"""


class GoalError(Exception):
    """Base exception for the argus.goal package."""


class InvalidGoalError(GoalError):
    """Raised when GoalBuilder's with_name()/with_description()/
    with_status()/with_priority()/with_metadata() is given a
    malformed argument."""
