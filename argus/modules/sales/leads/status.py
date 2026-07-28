"""
The LeadStatus enumeration for the Argus Sales OS Lead Workspace.

Purpose:
    Represent the closed set of states a Lead may carry through the
    sales workflow, per ARGUS_SALES_OS_V1_ARCHITECTURE.md. Mirrors
    argus.task.status.TaskStatus's own shape: a plain `Enum` (not a
    `str` subclass), lowercase string values matching each member's
    name.

No Transitions, No Behavior:
    This module defines only the enumeration itself. Nothing in
    argus.modules.sales.leads moves a Lead from one LeadStatus to
    another automatically - a caller sets status explicitly via
    LeadBuilder.with_status(), the same "no automatic transitions"
    precedent argus.task.status.TaskStatus already establishes for
    this codebase.

Responsibilities:
    - LeadStatus: enumerate the states a Lead's own `status` field
      may hold.

Non-Responsibilities:
    - This module implements no transition logic and no validation of
      whether a given transition is legal.

Dependencies:
    None.
"""

from enum import Enum


class LeadStatus(Enum):
    """
    The closed set of states a Lead may be in.

    NEW: the Lead's initial state - sourced (from ZoomInfo, Dynamics,
        or manual entry) but not yet worked.
    CONTACTED: at least one outreach touch has been made.
    QUALIFIED: the Lead has been assessed as a genuine fit and is
        being actively worked.
    NURTURING: not currently ready to progress, being kept warm on a
        longer cadence.
    WON: the Lead converted.
    LOST: the Lead did not convert and is no longer being worked.
    DISQUALIFIED: determined to be a poor fit; removed from active
        work independent of whether outreach ever occurred.
    """

    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    NURTURING = "nurturing"
    WON = "won"
    LOST = "lost"
    DISQUALIFIED = "disqualified"
