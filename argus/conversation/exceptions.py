"""
Exceptions raised by the ArgusOS Conversation Manager.

Purpose:
    Give callers explicit, catchable failure modes for session and
    message handling, per the coding standard's "explicit exceptions
    instead of silent failures" and
    factory/packages/011_CONVERSATION_MANAGER.md.

Responsibilities:
    - Provide a general conversation-subsystem error base, and more
      specific subtypes for "no active session", "not found",
      "duplicate/already active", and "invalid input" failures.

Non-Responsibilities:
    - These exceptions carry no behavior beyond a message; they do not
      log, retry, or recover.

Dependencies:
    None.
"""


class ConversationError(Exception):
    """Base exception for the conversation subsystem. Raised directly
    for failures that are not one of the more specific subtypes below,
    such as an illegal lifecycle transition, calling receive() while
    the manager's own IService state is not RUNNING, or receiving a
    message on a CLOSED session."""


class NoActiveSessionError(ConversationError):
    """Raised by receive(), end_session(), or history() (when called
    with no session_id) when there is no active session."""


class SessionNotFoundError(ConversationError):
    """Raised by history(session_id=...) when session_id does not
    match any session this manager has ever created."""


class ActiveSessionExistsError(ConversationError):
    """Raised by start_session() when a session is already active.
    Version 1 supports exactly one active session at a time - see
    factory/packages/011_CONVERSATION_MANAGER.md's Version 1
    Constraints."""


class InvalidMessageError(ConversationError):
    """Raised by receive() when given text that is not a non-empty
    string."""
