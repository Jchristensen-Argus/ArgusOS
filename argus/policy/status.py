"""
The PolicyStatus enumeration for the ArgusOS Policy Framework.

Purpose:
    Represent the closed set of states a Policy may carry, per
    factory/packages/040_POLICY_FRAMEWORK.md. "No transition logic" -
    this module defines only the enumeration itself; nothing in
    argus.policy moves a Policy from one PolicyStatus to another. A
    plain `Enum` (not a `str` subclass), lowercase string values
    matching each member's name, mirroring every prior status enum in
    this codebase.

ACTIVE Is The Default - Matching WorkspaceStatus, Not ProjectStatus/
GoalStatus:
    This package's own literal member list - "ACTIVE, INACTIVE,
    ARCHIVED" - is identical in shape to WorkspaceStatus's own
    three-member list (037), never naming a "not yet begun" state the
    way ProjectStatus.PLANNING/GoalStatus.PLANNING do. Continuing this
    codebase's own "the first-listed member is the default"
    convention, PolicyStatus's own default is ACTIVE - a Policy is
    presumed already in effect once created, the same reasoning
    WorkspaceStatus.ACTIVE (037) already established for a comparably
    unordered, non-"planning" member list.

No Transitions, No Behavior, No Enforcement:
    "Policy is a passive domain object only... no enforcement." No
    Version 1 code anywhere in argus.policy ever constructs a Policy
    with any status other than whatever a caller explicitly supplies
    via PolicyBuilder.with_status() - the default is
    PolicyStatus.ACTIVE, and nothing advances it, evaluates it, or
    enforces it further.

Responsibilities:
    - PolicyStatus: enumerate the three states a Policy's own
      `status` field may hold.

Non-Responsibilities:
    - This module implements no transition logic, no validation of
      whether a given transition is legal, and no behavior of any
      kind beyond the enumeration itself.

Dependencies:
    None.
"""

from enum import Enum


class PolicyStatus(Enum):
    """
    The closed set of states a Policy may be in. None of these states
    imply any transition logic - no Version 1 code in this codebase
    moves a Policy between them.

    ACTIVE: a Policy currently in effect. Default status for every
        Policy built via PolicyBuilder that never calls with_status().
    INACTIVE: a Policy temporarily not in effect, retained for
        possible future reactivation.
    ARCHIVED: a Policy retained for historical reference, no longer
        under active consideration.
    """

    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
