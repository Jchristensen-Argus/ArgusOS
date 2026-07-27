"""
Interfaces for the ArgusOS Goal Framework package.

Purpose:
    Define IGoalBuilder, the contract for a mutable, fluent Goal
    builder - per factory/packages/038_GOAL_FRAMEWORK.md. This package
    introduces no new service; IGoalBuilder therefore does not inherit
    IService, exactly mirroring ICognitiveContextBuilder (022),
    IPlanningSessionBuilder (023), ITraceBuilder (028), ITaskBuilder
    (029), IRelationshipBuilder (031), IExecutionResultBuilder (032),
    ICapabilityExecutionResultBuilder (034),
    ICapabilityContextBuilder (035), IProjectBuilder (036), and
    IWorkspaceBuilder (037), none of which inherit IService either - a
    builder has no meaningful start/stop lifecycle of its own; it is a
    short-lived, per-use accumulator.

Responsibilities:
    - IGoalBuilder: the contract implemented by GoalBuilder.

Non-Responsibilities:
    - This module defines no concrete behavior - see builder.py.

Dependencies:
    argus.goal.goal (Goal), argus.goal.status (GoalStatus),
    argus.goal.priority (GoalPriority).
"""

from abc import ABC, abstractmethod
from typing import Any

from argus.goal.goal import Goal
from argus.goal.priority import GoalPriority
from argus.goal.status import GoalStatus


class IGoalBuilder(ABC):
    """
    Contract for a mutable, fluent Goal builder. See this module's
    docstring for why IGoalBuilder does not inherit IService.
    """

    @abstractmethod
    def with_name(self, name: str) -> "IGoalBuilder":
        """Set this builder's name. A later call overwrites an
        earlier one - the last call before build() wins. Raises
        InvalidGoalError if `name` is not a non-empty string."""

    @abstractmethod
    def with_description(self, description: str) -> "IGoalBuilder":
        """Set this builder's description. A later call overwrites an
        earlier one - the last call before build() wins. Raises
        InvalidGoalError if `description` is not a string."""

    @abstractmethod
    def with_status(self, status: GoalStatus) -> "IGoalBuilder":
        """Set this builder's status. A later call overwrites an
        earlier one - the last call before build() wins. Raises
        InvalidGoalError if `status` is not a GoalStatus instance."""

    @abstractmethod
    def with_priority(self, priority: GoalPriority) -> "IGoalBuilder":
        """Set this builder's priority. A later call overwrites an
        earlier one - the last call before build() wins. Raises
        InvalidGoalError if `priority` is not a GoalPriority
        instance."""

    @abstractmethod
    def with_metadata(self, key: str, value: Any) -> "IGoalBuilder":
        """Set one arbitrary metadata key/value pair on the eventual
        GoalMetadata.extra mapping. Accumulates across multiple calls;
        the same key overwrites - last call wins. Raises
        InvalidGoalError if `key` is not a non-empty string."""

    @abstractmethod
    def build(self) -> Goal:
        """Construct and return a fresh, immutable Goal snapshot from
        this builder's current accumulated state."""
