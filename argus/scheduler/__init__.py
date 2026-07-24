"""
ArgusOS Scheduler Service package.

Purpose:
    Public entry point for the Scheduler subsystem. Re-exports the
    symbols other modules need (ScheduledTask, TaskPriority, the
    Trigger contract and its implementations, the IScheduler contract,
    the Scheduler implementation, and the scheduler exceptions) so
    callers can depend on `argus.scheduler` rather than reaching into
    individual submodules.

Dependencies:
    None beyond the submodules it re-exports.
"""

from argus.scheduler.exceptions import (
    InvalidTrigger,
    SchedulerError,
    TaskAlreadyExists,
    TaskExecutionError,
    TaskNotFound,
)
from argus.scheduler.interfaces import IScheduler
from argus.scheduler.scheduler import Scheduler
from argus.scheduler.task import ScheduledTask, TaskPriority
from argus.scheduler.triggers import DailyTrigger, IntervalTrigger, OneShotTrigger, Trigger

__all__ = [
    "ScheduledTask",
    "TaskPriority",
    "Trigger",
    "OneShotTrigger",
    "IntervalTrigger",
    "DailyTrigger",
    "IScheduler",
    "Scheduler",
    "SchedulerError",
    "TaskAlreadyExists",
    "TaskNotFound",
    "InvalidTrigger",
    "TaskExecutionError",
]
