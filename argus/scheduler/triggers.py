"""
Trigger contract and implementations for the ArgusOS Scheduler Service.

Purpose:
    Define when a ScheduledTask should next run, per
    factory/packages/008_SCHEDULER_SERVICE.md. A Trigger answers
    exactly one question - "given the last relevant instant (`after`),
    when should this task next fire?" - and nothing else: it does not
    invoke anything, does not know about ScheduledTask or Scheduler,
    and does not read the system clock itself (the caller always
    supplies `after` explicitly), which is what keeps Scheduler
    deterministic and testable without real sleeps.

Responsibilities:
    - Trigger: the common contract, `next_fire_time(after) -> Optional[datetime]`.
    - OneShotTrigger: fire exactly once, at a fixed instant.
    - IntervalTrigger: fire repeatedly, a fixed delay apart.
    - DailyTrigger: fire once per day, at a fixed time of day.

Non-Responsibilities:
    - No cron expression support (explicitly out of scope for this
      package - see factory/packages/008_SCHEDULER_SERVICE.md).
    - No time zone conversion: DailyTrigger operates directly on
      whatever `after` is expressed in (ArgusOS uses UTC everywhere;
      see design/specifications/SCHEDULER.md's Future Enhancements,
      which lists "Time-zone awareness" as explicitly deferred, not
      required now).
    - No "missed schedule" catch-up/recovery logic (also a
      design/specifications/SCHEDULER.md Future Enhancement, not
      required now). A trigger whose fire time has already passed
      before it is ever queried simply never fires - see each
      implementation's docstring for the precise rule.

Dependencies:
    None (standard library only).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from argus.scheduler.exceptions import InvalidTrigger


class Trigger(ABC):
    """
    Common contract every Scheduler trigger implements.

    Purpose:
        Let Scheduler compute "when is this task next due" uniformly,
        regardless of whether the underlying schedule is a one-time
        instant, a fixed interval, or a daily time of day.
    """

    @abstractmethod
    def next_fire_time(self, *, after: datetime) -> Optional[datetime]:
        """
        Return the next instant, strictly after `after`, at which this
        trigger should fire, or None if it will never fire again.

        Every implementation in this module uses strict "greater than"
        semantics uniformly: a candidate fire time equal to `after` is
        treated as already elapsed, not as still due. This is what
        prevents OneShotTrigger from refiring on the tick immediately
        after its one execution (see OneShotTrigger's docstring).
        """
        raise NotImplementedError


@dataclass(frozen=True)
class OneShotTrigger(Trigger):
    """
    Fires exactly once, at `run_at`.

    Purpose:
        Model a single, non-repeating deferred task.

    Behavior:
        next_fire_time(after) returns `run_at` if `run_at > after`,
        else None. Because every call site (both the initial
        schedule() call and every post-execution recomputation) uses
        this same strict-`>` rule, a OneShotTrigger naturally stops
        firing after its one execution: once `after` reaches or passes
        `run_at`, None is returned forever after.

        A OneShotTrigger whose `run_at` is already in the past at the
        moment it is first scheduled will never fire at all (no
        automatic catch-up); see this module's Non-Responsibilities.
    """

    run_at: datetime

    def next_fire_time(self, *, after: datetime) -> Optional[datetime]:
        return self.run_at if self.run_at > after else None


@dataclass(frozen=True)
class IntervalTrigger(Trigger):
    """
    Fires repeatedly, `interval_seconds` apart.

    Purpose:
        Model a recurring task on a fixed cadence.

    Behavior:
        next_fire_time(after) returns `after + interval_seconds`,
        unless `start_at` is set and still in the future relative to
        `after`, in which case `start_at` is returned instead (the
        first fire waits until `start_at`).

        This is fixed-delay scheduling (each next fire time is
        computed from the actual last check-in, `after`), not
        fixed-rate scheduling against a grid: if a tick() call is late,
        later fires drift later with it rather than trying to catch up
        to where a grid-aligned schedule "should" be. This is
        deliberately simpler than grid alignment and cannot produce a
        catch-up storm of overdue fires. `start_at` only ever delays
        the first fire; once it has passed (or if it was never given
        at all, or was already in the past when the trigger was first
        used), every subsequent fire is `after + interval_seconds`.

    Raises:
        InvalidTrigger: if interval_seconds is not strictly positive.
    """

    interval_seconds: float
    start_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if self.interval_seconds <= 0:
            raise InvalidTrigger(
                f"IntervalTrigger.interval_seconds must be > 0, got {self.interval_seconds!r}."
            )

    def next_fire_time(self, *, after: datetime) -> Optional[datetime]:
        if self.start_at is not None and self.start_at > after:
            return self.start_at
        return after + timedelta(seconds=self.interval_seconds)


@dataclass(frozen=True)
class DailyTrigger(Trigger):
    """
    Fires once a day, at `hour`:`minute`:`second`.

    Purpose:
        Model a task that should run at the same time every day.

    Behavior:
        next_fire_time(after) returns today's occurrence of
        hour:minute:second if that instant is still strictly after
        `after`; otherwise it returns tomorrow's occurrence. Operates
        directly on `after`'s own clock/time zone with no conversion -
        see this module's Non-Responsibilities.

    Raises:
        InvalidTrigger: if hour, minute, or second is out of range
            (0-23, 0-59, 0-59 respectively).
    """

    hour: int
    minute: int = 0
    second: int = 0

    def __post_init__(self) -> None:
        if not (0 <= self.hour <= 23):
            raise InvalidTrigger(f"DailyTrigger.hour must be 0-23, got {self.hour!r}.")
        if not (0 <= self.minute <= 59):
            raise InvalidTrigger(f"DailyTrigger.minute must be 0-59, got {self.minute!r}.")
        if not (0 <= self.second <= 59):
            raise InvalidTrigger(f"DailyTrigger.second must be 0-59, got {self.second!r}.")

    def next_fire_time(self, *, after: datetime) -> Optional[datetime]:
        candidate = after.replace(
            hour=self.hour, minute=self.minute, second=self.second, microsecond=0
        )
        if candidate <= after:
            candidate += timedelta(days=1)
        return candidate
