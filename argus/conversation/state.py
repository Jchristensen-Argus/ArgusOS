"""
ConversationState for the ArgusOS Conversation Manager.

Purpose:
    Define the closed set of lifecycle states a single
    ConversationSession can occupy, per
    factory/packages/011_CONVERSATION_MANAGER.md. This is distinct
    from argus.lifecycle.LifecycleState, which tracks the
    ConversationManager *service's* own IService lifecycle -
    ConversationState tracks an individual *session's* progress.

Responsibilities:
    - Enumerate NEW, ACTIVE, WAITING, and CLOSED as the only valid
      states a ConversationSession may be in.

Non-Responsibilities:
    - This module implements no transition logic. Transitions are
      enforced by ConversationManager (argus/conversation/manager.py).

Dependencies:
    None (standard library only).
"""

from enum import Enum


class ConversationState(Enum):
    """The only valid states a single ConversationSession may occupy.

    NEW: created by start_session(), no message has been received yet.
    ACTIVE: currently processing a receive() call.
    WAITING: idle, waiting for the next user message (set at the end
        of a successful receive() call).
    CLOSED: ended by end_session(); terminal - no further messages may
        be received.
    """

    NEW = "new"
    ACTIVE = "active"
    WAITING = "waiting"
    CLOSED = "closed"
