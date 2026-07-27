"""
Interfaces for the ArgusOS Project Framework package.

Purpose:
    Define IProjectBuilder, the contract for a mutable, fluent Project
    builder - per factory/packages/036_PROJECT_FRAMEWORK.md. This
    package introduces no new service; IProjectBuilder therefore does
    not inherit IService, exactly mirroring ICognitiveContextBuilder
    (022), IPlanningSessionBuilder (023), ITraceBuilder (028),
    ITaskBuilder (029), IRelationshipBuilder (031),
    IExecutionResultBuilder (032), ICapabilityExecutionResultBuilder
    (034), and ICapabilityContextBuilder (035), none of which inherit
    IService either - a builder has no meaningful start/stop lifecycle
    of its own; it is a short-lived, per-use accumulator.

Responsibilities:
    - IProjectBuilder: the contract implemented by ProjectBuilder.

Non-Responsibilities:
    - This module defines no concrete behavior - see builder.py.

Dependencies:
    argus.project.project (Project), argus.project.status
    (ProjectStatus).
"""

from abc import ABC, abstractmethod
from typing import Any

from argus.project.project import Project
from argus.project.status import ProjectStatus


class IProjectBuilder(ABC):
    """
    Contract for a mutable, fluent Project builder. See this module's
    docstring for why IProjectBuilder does not inherit IService.
    """

    @abstractmethod
    def with_name(self, name: str) -> "IProjectBuilder":
        """Set this builder's name. A later call overwrites an
        earlier one - the last call before build() wins. Raises
        InvalidProjectError if `name` is not a non-empty string."""

    @abstractmethod
    def with_description(self, description: str) -> "IProjectBuilder":
        """Set this builder's description. A later call overwrites an
        earlier one - the last call before build() wins. Raises
        InvalidProjectError if `description` is not a string."""

    @abstractmethod
    def with_status(self, status: ProjectStatus) -> "IProjectBuilder":
        """Set this builder's status. A later call overwrites an
        earlier one - the last call before build() wins. Raises
        InvalidProjectError if `status` is not a ProjectStatus
        instance."""

    @abstractmethod
    def with_metadata(self, key: str, value: Any) -> "IProjectBuilder":
        """Set one arbitrary metadata key/value pair on the eventual
        ProjectMetadata.extra mapping. Accumulates across multiple
        calls; the same key overwrites - last call wins. Raises
        InvalidProjectError if `key` is not a non-empty string."""

    @abstractmethod
    def build(self) -> Project:
        """Construct and return a fresh, immutable Project snapshot
        from this builder's current accumulated state."""
