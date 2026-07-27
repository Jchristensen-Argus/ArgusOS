"""
Interfaces for the ArgusOS Task Relationships package.

Purpose:
    Define IRelationshipBuilder, the contract for a mutable, fluent
    TaskRelationship builder - per
    factory/packages/031_TASK_RELATIONSHIPS.md. This package
    introduces no new service; IRelationshipBuilder therefore does
    not inherit IService, exactly mirroring ICognitiveContextBuilder
    (022), IPlanningSessionBuilder (023), ITraceBuilder (028), and
    ITaskBuilder (029), none of which inherit IService either - a
    builder has no meaningful start/stop lifecycle of its own; it is
    a short-lived, per-use accumulator.

Responsibilities:
    - IRelationshipBuilder: the contract implemented by
      RelationshipBuilder.

Non-Responsibilities:
    - This module defines no concrete behavior - see builder.py.

Dependencies:
    argus.task.task (Task), argus.task_relationship.relationship
    (TaskRelationship), argus.task_relationship.relationship_type
    (RelationshipType).
"""

from abc import ABC, abstractmethod
from typing import Any

from argus.task.task import Task
from argus.task_relationship.relationship import TaskRelationship
from argus.task_relationship.relationship_type import RelationshipType


class IRelationshipBuilder(ABC):
    """
    Contract for a mutable, fluent TaskRelationship builder. See this
    module's docstring for why IRelationshipBuilder does not inherit
    IService.
    """

    @abstractmethod
    def with_source_task(self, task: Task) -> "IRelationshipBuilder":
        """Set this builder's source_task. A later call overwrites an
        earlier one - the last call before build() wins. Raises
        InvalidTaskRelationshipError if `task` is not a Task
        instance."""

    @abstractmethod
    def with_target_task(self, task: Task) -> "IRelationshipBuilder":
        """Set this builder's target_task. A later call overwrites an
        earlier one - the last call before build() wins. Raises
        InvalidTaskRelationshipError if `task` is not a Task
        instance."""

    @abstractmethod
    def with_type(self, relationship_type: RelationshipType) -> "IRelationshipBuilder":
        """Set this builder's relationship_type. A later call
        overwrites an earlier one - the last call before build()
        wins. Raises InvalidTaskRelationshipError if
        `relationship_type` is not a RelationshipType instance."""

    @abstractmethod
    def with_metadata(self, key: str, value: Any) -> "IRelationshipBuilder":
        """Set one arbitrary metadata key/value pair on the eventual
        RelationshipMetadata.extra mapping. Accumulates across
        multiple calls; the same key overwrites - last call wins.
        Raises InvalidTaskRelationshipError if `key` is not a
        non-empty string."""

    @abstractmethod
    def build(self) -> TaskRelationship:
        """Construct and return a fresh, immutable TaskRelationship
        snapshot from this builder's current accumulated state."""
