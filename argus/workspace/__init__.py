"""
argus.workspace - The ArgusOS Workspace Framework package.

Re-exports the public surface of the Workspace Framework: the
immutable value objects (Workspace, WorkspaceStatus,
WorkspaceMetadata), the mutable builder (WorkspaceBuilder) and its
interface (IWorkspaceBuilder), and this package's own exceptions. See
factory/packages/037_WORKSPACE_FRAMEWORK.md for the full architectural
rationale. "A Workspace represents the highest-level organizational
boundary within Argus... A Workspace owns Projects. Projects own
Goals. Goals own Plans. Plans own Tasks." This package introduces the
Workspace model only - no runtime behavior, no integration, no
bootstrap changes.
"""

from argus.workspace.builder import WorkspaceBuilder
from argus.workspace.exceptions import InvalidWorkspaceError, WorkspaceError
from argus.workspace.interfaces import IWorkspaceBuilder
from argus.workspace.metadata import WORKSPACE_METADATA_VERSION, WorkspaceMetadata
from argus.workspace.status import WorkspaceStatus
from argus.workspace.workspace import Workspace

__all__ = [
    "Workspace",
    "WorkspaceStatus",
    "WorkspaceMetadata",
    "WORKSPACE_METADATA_VERSION",
    "WorkspaceBuilder",
    "IWorkspaceBuilder",
    "WorkspaceError",
    "InvalidWorkspaceError",
]
