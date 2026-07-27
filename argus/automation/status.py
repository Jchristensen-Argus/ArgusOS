"""
The AutomationStatus enumeration for the ArgusOS Automation Framework.

Purpose:
    Represent the closed set of states an Automation may carry, per
    factory/packages/041_AUTOMATION_FRAMEWORK.md. "No transition
    logic" - this module defines only the enumeration itself; nothing
    in argus.automation moves an Automation from one AutomationStatus
    to another. A plain `Enum` (not a `str` subclass), lowercase
    string values matching each member's name, mirroring every prior
    status enum in this codebase.

ACTIVE Is The Default - Matching PolicyStatus/WorkspaceStatus, Not
ProjectStatus/GoalStatus:
    This package's own literal member list - "ACTIVE, PAUSED,
    DISABLED, ARCHIVED" - never names a "not yet begun" state the way
    ProjectStatus.PLANNING/GoalStatus.PLANNING do, the same shape
    PolicyStatus (040) and WorkspaceStatus (037) already established
    for their own comparably unordered member lists. Continuing this
    codebase's own "the first-listed member is the default"
    convention, AutomationStatus's own default is ACTIVE - an
    Automation is presumed already in effect once created, matching
    PolicyStatus's own identical reasoning.

No Transitions, No Behavior, No Scheduling, No Execution:
    "An Automation defines what should run, when it should run, and
    under what conditions. It is a passive definition only." No
    Version 1 code anywhere in argus.automation ever constructs an
    Automation with any status other than whatever a caller explicitly
    supplies via AutomationBuilder.with_status() - the default is
    AutomationStatus.ACTIVE, and nothing advances it, schedules it, or
    executes it further.

Responsibilities:
    - AutomationStatus: enumerate the four states an Automation's own
      `status` field may hold.

Non-Responsibilities:
    - This module implements no transition logic, no validation of
      whether a given transition is legal, and no behavior of any
      kind beyond the enumeration itself.

Dependencies:
    None.
"""

from enum import Enum


class AutomationStatus(Enum):
    """
    The closed set of states an Automation may be in. None of these
    states imply any transition logic - no Version 1 code in this
    codebase moves an Automation between them.

    ACTIVE: an Automation currently in effect. Default status for
        every Automation built via AutomationBuilder that never calls
        with_status().
    PAUSED: an Automation temporarily not running, expected to resume.
    DISABLED: an Automation turned off, not expected to resume without
        an explicit re-enable.
    ARCHIVED: an Automation retained for historical reference, no
        longer under active consideration.
    """

    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"
    ARCHIVED = "archived"
