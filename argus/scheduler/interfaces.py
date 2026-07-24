"""
Public interface contract for the ArgusOS Scheduler Service.

Purpose:
    Define IScheduler, the contract other modules depend on, per
    factory/packages/008_SCHEDULER_SERVICE.md. IScheduler inherits
    IService: per Package 005's own docstring ("Let every future
    ArgusOS service (Memory, Scheduler, Cortex, Atlas, Hermes, etc.)
    be initialized, started, stopped..."), Scheduler was always the
    anticipated first real adopter. See ADR-0002
    (design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md) for the
    architectural reasoning behind treating Scheduler as that adopter,
    and this package's IMPLEMENTATION_REPORT.md for the empirical
    finding that resulted.

Responsibilities:
    - IScheduler: schedule / cancel / pause / resume / get_task /
      list_tasks / tick, plus the inherited initialize / start / stop
      / status from IService.

Non-Responsibilities:
    - This module implements no behavior; see
      argus.scheduler.scheduler.Scheduler.

Dependencies:
    argus.lifecycle.interfaces (IService), argus.scheduler.task
    (ScheduledTask, TaskPriority), argus.scheduler.triggers (Trigger).
"""

from abc import abstractmethod
from datetime import datetime
from typing import Any, Callable, Optional, Sequence

from argus.lifecycle.interfaces import IService
from argus.scheduler.task import ScheduledTask, TaskPriority
from argus.scheduler.triggers import Trigger


class IScheduler(IService):
    """
    Scheduling contract for ArgusOS's time orchestration service.

    Purpose:
        Let ArgusOS subsystems schedule deferred and recurring work,
        and let the Scheduler itself be initialized, started, and
        stopped like every other ArgusOS service, per IService.
    """

    @abstractmethod
    def schedule(
        self,
        *,
        name: str,
        callback: Callable[[], Any],
        trigger: Trigger,
        task_id: Optional[str] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        now: Optional[datetime] = None,
    ) -> ScheduledTask:
        """Register a new task, computing its initial next_run via
        trigger.next_fire_time(after=now). `now` defaults to the
        current time if not given; passing it explicitly is what
        keeps schedule() deterministic under test, matching tick()'s
        own `now` parameter. If task_id is not given, one is
        generated. Raises TaskAlreadyExists if task_id (given or
        generated) is already in use, InvalidTrigger if `trigger` is
        not a Trigger instance, or SchedulerError if `name` is empty
        or `callback` is not callable."""

    @abstractmethod
    def cancel(self, task_id: str) -> None:
        """Permanently remove a task. Raises TaskNotFound if no such
        task exists. Unlike pause(), a cancelled task cannot be
        resumed; task_id becomes available for reuse."""

    @abstractmethod
    def pause(self, task_id: str) -> None:
        """Temporarily disable a task without removing it; tick()
        will skip it until resume() is called. Raises TaskNotFound if
        no such task exists."""

    @abstractmethod
    def resume(self, task_id: str, *, now: Optional[datetime] = None) -> None:
        """Re-enable a paused task and recompute its next_run from
        `now` (default: the current time), not from whatever was
        pending before pause(). Raises TaskNotFound if no such task
        exists."""

    @abstractmethod
    def get_task(self, task_id: str) -> ScheduledTask:
        """Return the current state of one task. Raises TaskNotFound
        if no such task exists."""

    @abstractmethod
    def list_tasks(self) -> Sequence[ScheduledTask]:
        """Return every currently-tracked task (enabled or paused; not
        cancelled ones), in the order they were scheduled."""

    @abstractmethod
    def tick(self, *, now: Optional[datetime] = None) -> int:
        """Execute every enabled, due task (next_run <= now). `now`
        defaults to the current time if not given; passing it
        explicitly is what keeps tick() deterministic under test.
        Returns the number of tasks executed. Raises SchedulerError if
        the scheduler has not been started (see IService.start) or has
        since been stopped."""
