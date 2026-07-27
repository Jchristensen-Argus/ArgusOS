"""
Interfaces for the ArgusOS Task Model package.

Purpose:
    Define ITaskBuilder, the contract for a mutable, fluent Task
    builder - per factory/packages/029_TASK_MODEL.md. This package
    introduces no new service; ITaskBuilder therefore does not
    inherit IService, exactly mirroring ICognitiveContextBuilder
    (022), IPlanningSessionBuilder (023), and ITraceBuilder (028),
    none of which inherit IService either - a builder has no
    meaningful start/stop lifecycle of its own; it is a short-lived,
    per-use accumulator.

Responsibilities:
    - ITaskBuilder: the contract implemented by TaskBuilder.

Non-Responsibilities:
    - This module defines no concrete behavior - see builder.py.

Dependencies:
    argus.task.task (Task), argus.task.status (TaskStatus).
"""

from abc import ABC, abstractmethod
from typing import Any

from argus.task.status import TaskStatus
from argus.task.task import Task


class ITaskBuilder(ABC):
    """
    Contract for a mutable, fluent Task builder. See this module's
    docstring for why ITaskBuilder does not inherit IService.
    """

    @abstractmethod
    def with_name(self, name: str) -> "ITaskBuilder":
        """Set this builder's name. A later call overwrites an
        earlier one - the last call before build() wins. Raises
        InvalidTaskError if `name` is not a non-empty string."""

    @abstractmethod
    def with_description(self, description: str) -> "ITaskBuilder":
        """Set this builder's description. A later call overwrites an
        earlier one - the last call before build() wins. Raises
        InvalidTaskError if `description` is not a string."""

    @abstractmethod
    def with_status(self, status: TaskStatus) -> "ITaskBuilder":
        """Set this builder's status. A later call overwrites an
        earlier one - the last call before build() wins. Raises
        InvalidTaskError if `status` is not a TaskStatus instance."""

    @abstractmethod
    def with_metadata(self, key: str, value: Any) -> "ITaskBuilder":
        """Set one arbitrary metadata key/value pair on the eventual
        TaskMetadata.extra mapping. Accumulates across multiple
        calls; the same key overwrites - last call wins. Raises
        InvalidTaskError if `key` is not a non-empty string."""

    @abstractmethod
    def build(self) -> Task:
        """Construct and return a fresh, immutable Task snapshot from
        this builder's current accumulated state."""
