"""
Interfaces for the ArgusOS Workspace Framework package.

Purpose:
    Define IWorkspaceBuilder, the contract for a mutable, fluent
    Workspace builder - per
    factory/packages/037_WORKSPACE_FRAMEWORK.md. This package
    introduces no new service; IWorkspaceBuilder therefore does not
    inherit IService, exactly mirroring ICognitiveContextBuilder
    (022), IPlanningSessionBuilder (023), ITraceBuilder (028),
    ITaskBuilder (029), IRelationshipBuilder (031),
    IExecutionResultBuilder (032), ICapabilityExecutionResultBuilder
    (034), ICapabilityContextBuilder (035), and IProjectBuilder (036),
    none of which inherit IService either - a builder has no
    meaningful start/stop lifecycle of its own; it is a short-lived,
    per-use accumulator.

Responsibilities:
    - IWorkspaceBuilder: the contract implemented by WorkspaceBuilder.

Non-Responsibilities:
    - This module defines no concrete behavior - see builder.py.

Dependencies:
    argus.workspace.workspace (Workspace), argus.workspace.status
    (WorkspaceStatus).
"""

from abc import ABC, abstractmethod
from typing import Any

from argus.workspace.status import WorkspaceStatus
from argus.workspace.workspace import Workspace


class IWorkspaceBuilder(ABC):
    """
    Contract for a mutable, fluent Workspace builder. See this
    module's docstring for why IWorkspaceBuilder does not inherit
    IService.
    """

    @abstractmethod
    def with_name(self, name: str) -> "IWorkspaceBuilder":
        """Set this builder's name. A later call overwrites an
        earlier one - the last call before build() wins. Raises
        InvalidWorkspaceError if `name` is not a non-empty string."""

    @abstractmethod
    def with_description(self, description: str) -> "IWorkspaceBuilder":
        """Set this builder's description. A later call overwrites an
        earlier one - the last call before build() wins. Raises
        InvalidWorkspaceError if `description` is not a string."""

    @abstractmethod
    def with_status(self, status: WorkspaceStatus) -> "IWorkspaceBuilder":
        """Set this builder's status. A later call overwrites an
        earlier one - the last call before build() wins. Raises
        InvalidWorkspaceError if `status` is not a WorkspaceStatus
        instance."""

    @abstractmethod
    def with_metadata(self, key: str, value: Any) -> "IWorkspaceBuilder":
        """Set one arbitrary metadata key/value pair on the eventual
        WorkspaceMetadata.extra mapping. Accumulates across multiple
        calls; the same key overwrites - last call wins. Raises
        InvalidWorkspaceError if `key` is not a non-empty string."""

    @abstractmethod
    def build(self) -> Workspace:
        """Construct and return a fresh, immutable Workspace snapshot
        from this builder's current accumulated state."""
