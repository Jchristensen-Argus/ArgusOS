"""
The ProjectStatus enumeration for the ArgusOS Project Framework.

Purpose:
    Represent the closed set of states a Project may carry, per
    factory/packages/036_PROJECT_FRAMEWORK.md. This module defines
    only the enumeration itself; nothing in argus.project moves a
    Project from one ProjectStatus to another. Mirrors
    argus.task.status.TaskStatus's / argus.execution_engine.status.
    ExecutionStatus's own shape: a plain `Enum` (not a `str`
    subclass), lowercase string values matching each member's name.

No Transitions, No Behavior:
    "No runtime behavior yet... This package introduces the Project
    model only." No Version 1 code anywhere in argus.project ever
    constructs a Project with any status other than whatever a caller
    explicitly supplies via ProjectBuilder.with_status() - the default
    is ProjectStatus.PLANNING, and nothing advances it further.
    Transition rules (what follows PLANNING, what makes a Project
    ACTIVE, and so on) are explicitly out of scope for this package.

Responsibilities:
    - ProjectStatus: enumerate the five states a Project's own
      `status` field may hold.

Non-Responsibilities:
    - This module implements no transition logic, no validation of
      whether a given transition is legal, and no behavior of any
      kind beyond the enumeration itself.

Dependencies:
    None.
"""

from enum import Enum


class ProjectStatus(Enum):
    """
    The closed set of states a Project may be in. None of these
    states imply any transition logic - no Version 1 code in this
    codebase moves a Project between them.

    PLANNING: a Project's initial state - the organizational unit has
        been described but work under it has not yet begun. Default
        status for every Project built via ProjectBuilder that never
        calls with_status().
    ACTIVE: a Project currently underway. No Version 1 code ever
        produces this state automatically - it is only ever set by an
        explicit ProjectBuilder.with_status() call.
    PAUSED: a Project temporarily set aside, expected to resume.
    COMPLETED: a Project whose work has finished.
    ARCHIVED: a Project retained for historical reference only, no
        longer expected to receive further work.
    """

    PLANNING = "planning"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"
