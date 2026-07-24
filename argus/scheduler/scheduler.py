"""
Scheduler: deterministic, tick-driven task orchestration for ArgusOS.

Purpose:
    Implement IScheduler: hold a registry of ScheduledTask objects,
    execute every due task when tick() is called, and publish task
    lifecycle events on the Event Bus, per
    factory/packages/008_SCHEDULER_SERVICE.md.

Responsibilities:
    - schedule / cancel / pause / resume / get_task / list_tasks /
      tick, per IScheduler.
    - initialize / start / stop / status, per the inherited IService
      contract - Scheduler is ArgusOS's first genuine IService
      adopter (see ADR-0002,
      design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md). start()
      and stop() have real, distinct meaning here even without a
      background thread: tick() only executes tasks while the
      Scheduler's own internal state is RUNNING, and raises
      SchedulerError otherwise. schedule/cancel/pause/resume/get_task/
      list_tasks are unaffected by lifecycle state - they are pure
      registry operations, not execution.
    - Protect every mutation (schedule, cancel, pause, resume, tick)
      with a threading.Lock, matching the read/write split established
      by KnowledgeService (Package 006) and MemoryService (Package
      007), even though this package does not itself spawn threads.
    - Publish EventType.TASK_SCHEDULED / TASK_STARTED / TASK_COMPLETED
      / TASK_FAILED / TASK_CANCELLED / TASK_PAUSED / TASK_RESUMED for
      the corresponding operation, and EventType.SCHEDULER_TICK once
      per tick() call as a heartbeat, regardless of how many tasks
      were due.

Non-Responsibilities:
    - No background threads, timers, or automatic ticking. Execution
      happens only when tick() is called, per this package's explicit
      v1 scope - see the module docstring's Non-Responsibilities in
      argus/scheduler/triggers.py for the corresponding trigger-level
      scope limits (no cron, no missed-schedule recovery, no time zone
      conversion).
    - No retry logic: a failing callback publishes TaskFailed and, for
      a recurring trigger, is still rescheduled for its normal next
      occurrence - there is no separate retry/backoff mechanism.
    - Scheduler does not write to Memory, directly or indirectly, and
      does not import argus.memory anywhere. Execution history is
      exposed only through the published events; per this package's
      explicit Non-Goal, Memory may subscribe to them in a future
      package, but Scheduler has no awareness that Memory exists.
    - Scheduler does not dispatch to Navigator. design/specifications/
      SCHEDULER.md lists Navigator as a Required Dependency, but
      Navigator does not exist yet (see
      factory/packages/008_SCHEDULER_SERVICE.md). A ScheduledTask's
      `callback` is a plain Python callable in this version; routing
      execution through Navigator instead is deferred until Navigator
      exists.

Dependencies:
    argus.events (Event, EventType, IEventBus), argus.lifecycle
    (LifecycleState), argus.scheduler (ScheduledTask, TaskPriority,
    Trigger, and the scheduler exceptions).
"""

import threading
import uuid
from dataclasses import replace
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Sequence

from argus.events.event import Event
from argus.events.event_types import EventType
from argus.events.interfaces import IEventBus
from argus.lifecycle.lifecycle import LifecycleState
from argus.scheduler.exceptions import (
    InvalidTrigger,
    SchedulerError,
    TaskAlreadyExists,
    TaskExecutionError,
    TaskNotFound,
)
from argus.scheduler.interfaces import IScheduler
from argus.scheduler.task import ScheduledTask, TaskPriority
from argus.scheduler.triggers import Trigger

# Execution order within a single tick() call when more than one task
# is due: higher priority first. Ties broken by next_run ascending
# (earliest-scheduled first), so ordering is fully deterministic for
# any given set of due tasks - required for this package's "highly
# testable" scope.
_PRIORITY_ORDER: Dict[TaskPriority, int] = {
    TaskPriority.CRITICAL: 0,
    TaskPriority.HIGH: 1,
    TaskPriority.NORMAL: 2,
    TaskPriority.LOW: 3,
}


class Scheduler(IScheduler):
    """
    In-memory, tick-driven implementation of IScheduler.

    Purpose:
        Let ArgusOS defer and repeat work without any subsystem having
        to manage timing itself.

    Responsibilities:
        - Own the task registry and keep it internally consistent.
        - Compute due tasks and execute them, in priority order, only
          when tick() is called.
        - Track its own IService lifecycle state and gate tick() on it.
        - Publish task and tick events on the Event Bus.

    Dependencies:
        An IEventBus implementation, injected by the caller
        (bootstrap.py).
    """

    def __init__(self, event_bus: IEventBus) -> None:
        self._event_bus = event_bus
        self._lock = threading.Lock()
        self._tasks: Dict[str, ScheduledTask] = {}
        # Scheduler's own IService-facing state. Deliberately separate
        # from (and, if this Scheduler is also registered with a
        # LifecycleManager by name, potentially divergent from) the
        # Lifecycle Manager's per-name tracking - this is the
        # duplicate-state question ADR-0002 asked Scheduler to be the
        # proving ground for. See
        # tests/test_scheduler.py::IServiceLifecycleDivergenceTests
        # for an empirical demonstration.
        self._state: LifecycleState = LifecycleState.CREATED

    # -- IService -----------------------------------------------------

    def initialize(self) -> None:
        if self._state != LifecycleState.CREATED:
            raise SchedulerError(
                f"Cannot initialize: Scheduler is {self._state.name}, expected CREATED."
            )
        self._state = LifecycleState.INITIALIZING

    def start(self) -> None:
        if self._state != LifecycleState.INITIALIZING:
            raise SchedulerError(
                f"Cannot start: Scheduler is {self._state.name}, expected INITIALIZING."
            )
        self._state = LifecycleState.RUNNING

    def stop(self) -> None:
        if self._state != LifecycleState.RUNNING:
            raise SchedulerError(
                f"Cannot stop: Scheduler is {self._state.name}, expected RUNNING."
            )
        self._state = LifecycleState.STOPPING
        self._state = LifecycleState.STOPPED

    def status(self) -> LifecycleState:
        return self._state

    # -- IScheduler: registry operations (unaffected by lifecycle state) --

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
        if not name:
            raise SchedulerError("ScheduledTask.name must not be empty.")
        if not callable(callback):
            raise SchedulerError(f"callback must be callable, got {callback!r}.")
        if not isinstance(trigger, Trigger):
            raise InvalidTrigger(f"trigger must be a Trigger instance, got {trigger!r}.")

        reference_time = now if now is not None else datetime.now(timezone.utc)

        with self._lock:
            resolved_id = task_id if task_id is not None else self._generate_task_id()
            if resolved_id in self._tasks:
                raise TaskAlreadyExists(f"Task id {resolved_id!r} already exists.")

            task = ScheduledTask(
                name=name,
                callback=callback,
                trigger=trigger,
                id=resolved_id,
                priority=priority,
                next_run=trigger.next_fire_time(after=reference_time),
            )
            self._tasks[resolved_id] = task

        self._publish(EventType.TASK_SCHEDULED, task)
        return task

    def cancel(self, task_id: str) -> None:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                raise TaskNotFound(f"No task for id {task_id!r}.")
            del self._tasks[task_id]

        self._publish(EventType.TASK_CANCELLED, task)

    def pause(self, task_id: str) -> None:
        with self._lock:
            task = self._require_task(task_id)
            paused = replace(task, enabled=False)
            self._tasks[task_id] = paused

        self._publish(EventType.TASK_PAUSED, paused)

    def resume(self, task_id: str, *, now: Optional[datetime] = None) -> None:
        reference_time = now if now is not None else datetime.now(timezone.utc)

        with self._lock:
            task = self._require_task(task_id)
            resumed = replace(
                task, enabled=True, next_run=task.trigger.next_fire_time(after=reference_time)
            )
            self._tasks[task_id] = resumed

        self._publish(EventType.TASK_RESUMED, resumed)

    def get_task(self, task_id: str) -> ScheduledTask:
        task = self._tasks.get(task_id)
        if task is None:
            raise TaskNotFound(f"No task for id {task_id!r}.")
        return task

    def list_tasks(self) -> Sequence[ScheduledTask]:
        return tuple(self._tasks.values())

    # -- IScheduler: execution (requires RUNNING) ----------------------

    def tick(self, *, now: Optional[datetime] = None) -> int:
        if self._state != LifecycleState.RUNNING:
            raise SchedulerError(
                f"Cannot tick: Scheduler is {self._state.name}, expected RUNNING "
                "(call initialize() then start() first)."
            )

        current_time = now if now is not None else datetime.now(timezone.utc)

        with self._lock:
            due_tasks = self._due_tasks(current_time)

        for task in due_tasks:
            self._run_one(task, current_time)

        self._event_bus.publish(
            Event(
                type=EventType.SCHEDULER_TICK,
                source="scheduler",
                payload={"now": current_time.isoformat(), "executed": len(due_tasks)},
            )
        )
        return len(due_tasks)

    # -- internals ------------------------------------------------------

    def _due_tasks(self, now: datetime) -> List[ScheduledTask]:
        # Must be called while holding self._lock.
        candidates = [
            task
            for task in self._tasks.values()
            if task.enabled and task.next_run is not None and task.next_run <= now
        ]
        candidates.sort(key=lambda task: (_PRIORITY_ORDER[task.priority], task.next_run))
        return candidates

    def _run_one(self, task: ScheduledTask, now: datetime) -> None:
        self._publish(EventType.TASK_STARTED, task)

        try:
            self._execute(task)
        except TaskExecutionError as error:
            self._finish(task, now, succeeded=False)
            self._publish(
                EventType.TASK_FAILED,
                task,
                extra_payload={"error": str(error), "error_type": type(error.__cause__).__name__},
            )
        else:
            self._finish(task, now, succeeded=True)
            self._publish(EventType.TASK_COMPLETED, task)

    @staticmethod
    def _execute(task: ScheduledTask) -> None:
        try:
            task.callback()
        except Exception as error:
            raise TaskExecutionError(
                f"Task {task.id!r} ({task.name!r}) failed: {error}"
            ) from error

    def _finish(self, task: ScheduledTask, now: datetime, *, succeeded: bool) -> None:
        # succeeded is currently unused in the rescheduling rule itself
        # (a recurring trigger reschedules on both success and
        # failure - see the module docstring's Non-Responsibilities on
        # why there is no separate retry path) but is threaded through
        # for clarity at call sites and potential future use.
        del succeeded
        with self._lock:
            current = self._tasks.get(task.id)
            if current is None:
                # Cancelled by another call between being selected as
                # due and finishing execution; nothing left to update.
                return
            updated = replace(
                current,
                last_run=now,
                next_run=current.trigger.next_fire_time(after=now),
            )
            self._tasks[task.id] = updated

    def _require_task(self, task_id: str) -> ScheduledTask:
        # Must be called while holding self._lock.
        task = self._tasks.get(task_id)
        if task is None:
            raise TaskNotFound(f"No task for id {task_id!r}.")
        return task

    @staticmethod
    def _generate_task_id() -> str:
        return str(uuid.uuid4())

    def _publish(
        self, event_type: EventType, task: ScheduledTask, *, extra_payload: Optional[dict] = None
    ) -> None:
        # Published after self._lock is released by every caller of
        # this method, so a handler that calls back into Scheduler can
        # never deadlock on self._lock, which is not reentrant.
        # Mirrors KnowledgeService._publish (Package 006) and
        # MemoryService._publish (Package 007).
        payload = {"task_id": task.id, "task_name": task.name}
        if extra_payload:
            payload.update(extra_payload)
        self._event_bus.publish(Event(type=event_type, source="scheduler", payload=payload))
