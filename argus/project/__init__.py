"""
argus.project - The ArgusOS Project Framework package.

Re-exports the public surface of the Project Framework: the immutable
value objects (Project, ProjectStatus, ProjectMetadata), the mutable
builder (ProjectBuilder) and its interface (IProjectBuilder), and this
package's own exceptions. See
factory/packages/036_PROJECT_FRAMEWORK.md for the full architectural
rationale. "A Project is the top-level organizational unit for
long-running work... Projects own Goals. Goals own Plans. Plans own
Tasks." This package introduces the Project model only - no runtime
behavior, no integration, no bootstrap changes.
"""

from argus.project.builder import ProjectBuilder
from argus.project.exceptions import InvalidProjectError, ProjectError
from argus.project.interfaces import IProjectBuilder
from argus.project.metadata import PROJECT_METADATA_VERSION, ProjectMetadata
from argus.project.project import Project
from argus.project.status import ProjectStatus

__all__ = [
    "Project",
    "ProjectStatus",
    "ProjectMetadata",
    "PROJECT_METADATA_VERSION",
    "ProjectBuilder",
    "IProjectBuilder",
    "ProjectError",
    "InvalidProjectError",
]
