"""
The WorkspaceStatus enumeration for the ArgusOS Workspace Framework.

Purpose:
    Represent the closed set of states a Workspace may carry, per
    factory/packages/037_WORKSPACE_FRAMEWORK.md. "No transition
    logic" - this module defines only the enumeration itself; nothing
    in argus.workspace moves a Workspace from one WorkspaceStatus to
    another. Mirrors argus.project.status.ProjectStatus's /
    argus.task.status.TaskStatus's own shape: a plain `Enum` (not a
    `str` subclass), lowercase string values matching each member's
    name.

ACTIVE Is The Default, Not The First Reserved State:
    Unlike ProjectStatus (029/036), whose own first-listed member,
    PLANNING, reflects that a Project typically begins as a described-
    but-not-yet-underway unit of work, this package's own literal
    member list - "ACTIVE, INACTIVE, ARCHIVED" - opens with ACTIVE.
    Continuing this codebase's own "the first-listed member is the
    default" convention (TaskStatus.PENDING, PlanStatus.CREATED,
    ProjectStatus.PLANNING all being their own respective first-listed
    members), WorkspaceStatus.ACTIVE is Workspace's own default status
    - a Workspace, once it exists at all, is presumed active by
    default, unlike a Project, which is presumed still in planning.
    This is a deliberate, literal reading of the work order's own
    ordering, not an inference from the member names' own meaning.

No Transitions, No Behavior:
    "This package introduces the Workspace model only." No Version 1
    code anywhere in argus.workspace ever constructs a Workspace with
    any status other than whatever a caller explicitly supplies via
    WorkspaceBuilder.with_status() - the default is
    WorkspaceStatus.ACTIVE, and nothing advances or demotes it
    further.

Responsibilities:
    - WorkspaceStatus: enumerate the three states a Workspace's own
      `status` field may hold.

Non-Responsibilities:
    - This module implements no transition logic, no validation of
      whether a given transition is legal, and no behavior of any
      kind beyond the enumeration itself.

Dependencies:
    None.
"""

from enum import Enum


class WorkspaceStatus(Enum):
    """
    The closed set of states a Workspace may be in. None of these
    states imply any transition logic - no Version 1 code in this
    codebase moves a Workspace between them.

    ACTIVE: a Workspace currently in use. Default status for every
        Workspace built via WorkspaceBuilder that never calls
        with_status() - see the module docstring for why this differs
        from ProjectStatus's own default.
    INACTIVE: a Workspace not currently in use, but not permanently
        retired.
    ARCHIVED: a Workspace retained for historical reference only, no
        longer expected to receive further work.
    """

    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
