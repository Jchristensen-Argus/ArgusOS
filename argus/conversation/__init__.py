"""
Public re-exports for the ArgusOS Conversation Manager package.

Purpose:
    Give callers a single, stable import surface
    (`from argus.conversation import ...`) instead of reaching into
    individual submodules, matching the convention established by
    argus/scheduler/__init__.py, argus/intent/__init__.py, and
    argus/workflow/__init__.py.

Dependencies:
    argus.conversation.exceptions, argus.conversation.state,
    argus.conversation.message, argus.conversation.session,
    argus.conversation.interfaces, argus.conversation.manager.
"""

from argus.conversation.exceptions import (
    ActiveSessionExistsError,
    ConversationError,
    InvalidMessageError,
    NoActiveSessionError,
    SessionNotFoundError,
)
from argus.conversation.interfaces import IConversationManager
from argus.conversation.manager import ConversationManager
from argus.conversation.message import ConversationMessage, ConversationRole
from argus.conversation.session import ConversationSession
from argus.conversation.state import ConversationState

__all__ = [
    "ConversationSession",
    "ConversationMessage",
    "ConversationRole",
    "ConversationState",
    "IConversationManager",
    "ConversationManager",
    "ConversationError",
    "NoActiveSessionError",
    "SessionNotFoundError",
    "ActiveSessionExistsError",
    "InvalidMessageError",
]
