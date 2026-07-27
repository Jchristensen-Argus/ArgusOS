"""
Interfaces for the ArgusOS Task Model package.

Purpose:
    Define ITaskBuilder, the contract for a mutable, fluent Task
    builder - per factory/packages/029_TASK_MODEL.md, as amended by
    factory/packages/031_TASK_RELATIONSHIPS.md. This package
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
    argus.task.task (Task), argus.task.status (TaskStatus),
    argus.task_relationship.relationship (TaskRelationship) - Package
    031.
"""

from abc import ABC, abstractmethod
from typing import Any, Sequence

from argus.task.status import TaskStatus
from argus.task.task import Task
from argus.task_relationship.relationship import TaskRelationship


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
    def with_relationship(self, relationship: TaskRelationship) -> "ITaskBuilder":
        """Validate and append one TaskRelationship, in call order.
        Accumulates across multiple calls. Raises InvalidTaskError if
        `relationship` is not a TaskRelationship instance, or if its
        `relationship_id` duplicates one already accumulated."""

    @abstractmethod
    def with_relationships(
        self, relationships: Sequence[TaskRelationship]
    ) -> "ITaskBuilder":
        """Validate and append each item of `relationships`, in
        order, by delegating to with_relationship() once per item.
        Raises InvalidTaskError if `relationships` is not a list or
        tuple, or if any item is not a TaskRelationship instance, or
        if any item's `relationship_id` duplicates one already
        accumulated (within this call or a prior one)."""

    @abstractmethod
    def clear_relationships(self) -> "ITaskBuilder":
        """Reset this builder's accumulated relationships to empty."""

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
