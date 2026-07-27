"""
argus.task - The ArgusOS Task Model package.

Re-exports the public surface of the Task Model: the immutable value
objects (Task, TaskStatus, TaskMetadata), the mutable builder
(TaskBuilder) and its interface (ITaskBuilder), and this package's own
exceptions. See factory/packages/029_TASK_MODEL.md for the full
architectural rationale. "A Task represents a single unit of work
produced by a Plan. This package introduces no execution. Only the
model."
"""

from argus.task.builder import TaskBuilder
from argus.task.exceptions import InvalidTaskError, TaskError
from argus.task.interfaces import ITaskBuilder
from argus.task.metadata import TASK_METADATA_VERSION, TaskMetadata
from argus.task.status import TaskStatus
from argus.task.task import Task

__all__ = [
    "Task",
    "TaskStatus",
    "TaskMetadata",
    "TASK_METADATA_VERSION",
    "TaskBuilder",
    "ITaskBuilder",
    "TaskError",
    "InvalidTaskError",
]
