"""
Exceptions raised by the ArgusOS Scheduler Service.

Purpose:
    Give callers explicit, catchable failure modes for scheduling
    operations, per the coding standard's "explicit exceptions instead
    of silent failures" and factory/packages/008_SCHEDULER_SERVICE.md.

Responsibilities:
    - Provide a general scheduler-subsystem error base, and more
      specific subtypes for "already exists", "not found", "invalid
      trigger", and "execution failed" failures, so callers can catch
      either the broad or the precise failure mode.

Non-Responsibilities:
    - These exceptions carry no behavior beyond a message; they do not
      log, retry, or recover.

Dependencies:
    None.
"""


class SchedulerError(Exception):
    """Base exception for the scheduler subsystem. Raised directly for
    failures that are not one of the more specific subtypes below,
    such as an empty task name, a non-callable callback, or an
    illegal lifecycle transition (e.g. calling tick() before start())."""


class TaskAlreadyExists(SchedulerError):
    """Raised when schedule() is called with a task_id that is already
    present in the scheduler."""


class TaskNotFound(SchedulerError):
    """Raised when an operation references a task_id with no
    corresponding scheduled task."""


class InvalidTrigger(SchedulerError):
    """Raised when a trigger's own field values are out of range (for
    example, a negative interval or an hour outside 0-23), or when a
    non-Trigger object is supplied where a Trigger is required."""


class TaskExecutionError(SchedulerError):
    """Raised internally by Scheduler when a task's callback raises
    during tick(). Wraps the callback's original exception (via
    `raise ... from error`, preserving the traceback chain). This
    exception is caught within tick() itself and never propagates to
    tick()'s caller: one task's failure must never prevent the
    remaining due tasks in the same tick() call from running. See
    Scheduler._execute_task and the TaskFailed event it publishes."""
