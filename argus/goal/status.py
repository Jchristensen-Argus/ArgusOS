"""
The GoalStatus enumeration for the ArgusOS Goal Framework.

Purpose:
    Represent the closed set of states a Goal may carry, per
    factory/packages/038_GOAL_FRAMEWORK.md. "No transition logic" -
    this module defines only the enumeration itself; nothing in
    argus.goal moves a Goal from one GoalStatus to another. Mirrors
    argus.project.status.ProjectStatus's / argus.workspace.status.
    WorkspaceStatus's own shape: a plain `Enum` (not a `str`
    subclass), lowercase string values matching each member's name.

PLANNING Is The Default - Matching ProjectStatus, Not WorkspaceStatus:
    This package's own literal member list - "PLANNING, ACTIVE,
    PAUSED, COMPLETED, ABANDONED" - is identical in shape to
    ProjectStatus's own five-member list (029/036: PLANNING, ACTIVE,
    PAUSED, COMPLETED, ARCHIVED), differing only in its final member
    (ABANDONED instead of ARCHIVED). Continuing this codebase's own
    "the first-listed member is the default" convention, GoalStatus's
    own default is PLANNING - the same "not yet begun" meaning
    ProjectStatus.PLANNING carries, and a genuine difference from
    WorkspaceStatus.ACTIVE's own default (037), whose own member list
    never named a "not yet begun" state at all. A Goal, like a
    Project, is presumed still in planning until a caller explicitly
    says otherwise; a Workspace is presumed already active.

ABANDONED, Not ARCHIVED - A Deliberate Difference From ProjectStatus:
    Where ProjectStatus's own final member is ARCHIVED (a Project
    retained for historical reference, its work having presumably
    finished or been formally closed out), GoalStatus's own final
    member is ABANDONED - a Goal that was given up on, not
    necessarily because its work concluded. This is a deliberate,
    literal reading of the work order's own distinct member name, not
    an interpretive substitution - a Goal's own final state carries a
    different connotation than a Project's own final state, and this
    module preserves that distinction rather than reusing ARCHIVED for
    consistency's own sake.

No Transitions, No Behavior:
    "Goals are passive domain objects only." No Version 1 code
    anywhere in argus.goal ever constructs a Goal with any status
    other than whatever a caller explicitly supplies via
    GoalBuilder.with_status() - the default is GoalStatus.PLANNING,
    and nothing advances it further.

Responsibilities:
    - GoalStatus: enumerate the five states a Goal's own `status`
      field may hold.

Non-Responsibilities:
    - This module implements no transition logic, no validation of
      whether a given transition is legal, and no behavior of any
      kind beyond the enumeration itself.

Dependencies:
    None.
"""

from enum import Enum


class GoalStatus(Enum):
    """
    The closed set of states a Goal may be in. None of these states
    imply any transition logic - no Version 1 code in this codebase
    moves a Goal between them.

    PLANNING: a Goal's initial state - the desired outcome has been
        described but work under it has not yet begun. Default status
        for every Goal built via GoalBuilder that never calls
        with_status().
    ACTIVE: a Goal currently being pursued.
    PAUSED: a Goal temporarily set aside, expected to resume.
    COMPLETED: a Goal whose desired outcome has been achieved.
    ABANDONED: a Goal given up on before completion - see the module
        docstring for why this differs from ProjectStatus.ARCHIVED.
    """

    PLANNING = "planning"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
