"""
The LeadSyncState enumeration for the Argus Sales OS Lead Workspace.

Purpose:
    Represent whether a Lead's current state has been reconciled with
    Dynamics, per ARGUS_SALES_OS_V1_ARCHITECTURE.md's Sprint 1 scope:
    "design so the Dynamics Connector... can plug in later without
    modifying the Lead Workspace." This module lets the Lead Workspace
    track sync state as plain data now, before any real Dynamics
    Connector (argus/integrations/dynamics/, not yet built) exists to
    act on it.

No Sync Behavior Here:
    This module defines only the enumeration. Nothing in
    argus.modules.sales.leads performs a sync, calls Dynamics, or
    changes a Lead's sync_state automatically - a caller sets it
    explicitly via LeadBuilder.with_sync_state(). The Dynamics
    Connector, when built, is what advances this field.

Responsibilities:
    - LeadSyncState: enumerate the states a Lead's own `sync_state`
      field may hold.

Non-Responsibilities:
    - This module implements no synchronization logic of any kind.

Dependencies:
    None.
"""

from enum import Enum


class LeadSyncState(Enum):
    """
    The closed set of Dynamics-synchronization states a Lead may be
    in.

    NOT_SYNCED: this Lead has never been reconciled with Dynamics -
        the default for a freshly loaded or manually created Lead.
    PENDING_SYNC: a local change has been made that has not yet been
        pushed to Dynamics.
    SYNCED: this Lead's state matches Dynamics as of its last known
        sync.
    SYNC_FAILED: the most recent sync attempt did not succeed.
    """

    NOT_SYNCED = "not_synced"
    PENDING_SYNC = "pending_sync"
    SYNCED = "synced"
    SYNC_FAILED = "sync_failed"
