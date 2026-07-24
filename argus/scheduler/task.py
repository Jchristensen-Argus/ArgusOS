"""
ScheduledTask for the ArgusOS Scheduler Service.

Purpose:
    Represent a single unit of deferred or recurring work known to the
    Scheduler, per factory/packages/008_SCHEDULER_SERVICE.md.

Responsibilities:
    - Hold a task's identity (id, name), the work to perform
      (callback), when to perform it (trigger, next_run), execution
      history (created_at, last_run), and its current disposition
      (priority, enabled).

Non-Responsibilities:
    - ScheduledTask does not decide when it is next due, or invoke its
      own callback. Both are Trigger's and Scheduler's responsibility,
      respectively; ScheduledTask is a pure value object, per the same
      "no business logic" convention established for KnowledgeRecord
      (Package 006) and MemoryRecord (Package 007).
    - ScheduledTask does not validate its own fields (for example, that
      `callback` is callable); that is Scheduler.schedule()'s
      responsibility, matching the validation precedent set by
      KnowledgeService.put() and MemoryService.put().
    - Like KnowledgeRecord and MemoryRecord, ScheduledTask does not
      deep-freeze `callback` or `trigger`; only the dataclass's own
      fields are immutable (frozen=True prevents reassigning them
      after construction).

Dependencies:
    argus.scheduler.triggers (Trigger), for the trigger field's type.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Callable, Optional

from argus.scheduler.triggers import Trigger


class TaskPriority(Enum):
    """Relative priority of a scheduled task. Used by Scheduler.tick()
    to order execution when more than one task is due in the same
    tick() call: higher-priority tasks run first, per this package's
    "deterministic and highly testable" scope. Distinct from
    argus.events.EventPriority - task priority and event priority are
    different concerns that happen to share a similar shape, and this
    package does not depend on argus.events.EventPriority."""

    LOW = auto()
    NORMAL = auto()
    HIGH = auto()
    CRITICAL = auto()


@dataclass(frozen=True)
class ScheduledTask:
    """
    An immutable record of one task known to the Scheduler.

    Purpose:
        Carry a task's identity, work, schedule, and history through
        the Scheduler without exposing any way to mutate it after
        construction. Updates (pause/resume, post-execution
        next_run/last_run changes) are performed by constructing a new
        ScheduledTask (see Scheduler, which uses dataclasses.replace).

    Responsibilities:
        - Store name, callback, trigger, id, priority, enabled,
          created_at, next_run, and last_run.
        - Auto-generate `id` and `created_at` when not supplied, and
          default `priority` to NORMAL, `enabled` to True, and
          `next_run`/`last_run` to None.

    Dependencies:
        argus.scheduler.triggers.Trigger.
    """

    name: str
    callback: Callable[[], Any]
    trigger: Trigger
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    priority: TaskPriority = TaskPriority.NORMAL
    enabled: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
