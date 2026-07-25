"""
Public interface contract for the ArgusOS Conversation Manager.

Purpose:
    Define the Conversation Manager's public contract independently of
    any concrete implementation, per
    design/specifications/INTERFACES.md's "no subsystem may bypass
    another engine's published interface" and
    factory/packages/011_CONVERSATION_MANAGER.md.

Responsibilities:
    - Declare start_session, end_session, receive, history, and
      active_session as the Conversation Manager's surface, plus the
      inherited IService lifecycle (initialize/start/stop/status).

Non-Responsibilities:
    - This module implements nothing.

Dependencies:
    argus.lifecycle.interfaces (IService), argus.conversation.session
    (ConversationSession), argus.conversation.message
    (ConversationMessage).
"""

from abc import abstractmethod
from typing import Any, Mapping, Optional, Sequence

from argus.conversation.message import ConversationMessage
from argus.conversation.session import ConversationSession
from argus.lifecycle.interfaces import IService


class IConversationManager(IService):
    """
    Conversation coordination contract for ArgusOS.

    Purpose:
        Let a caller start a session, feed it user messages, and get
        back deterministic responses - without the manager performing
        any AI reasoning, parsing intents itself, or executing
        workflows itself. It coordinates IIntentRouter and
        IWorkflowEngine; see argus/conversation/manager.py's module
        docstring for exactly how those two delegations work.

    Version 1 scope:
        Exactly one session may be active at a time (see
        ActiveSessionExistsError). Sessions are held only in memory;
        nothing persists across process restarts.
    """

    @abstractmethod
    def start_session(
        self, *, metadata: Optional[Mapping[str, Any]] = None
    ) -> ConversationSession:
        """
        Start a new ConversationSession in the NEW state and make it
        the active session.

        Raises ActiveSessionExistsError if a session is already
        active (Version 1 supports exactly one active session).
        Publishes ConversationStarted on success. Not affected by the
        manager's own IService lifecycle state - this is a registry
        operation, like Scheduler.schedule() or
        WorkflowEngine.register_workflow().
        """
        raise NotImplementedError

    @abstractmethod
    def end_session(self) -> ConversationSession:
        """
        End the active session: transition it to CLOSED, publish
        ConversationEnded, and clear it as the active session.

        Raises NoActiveSessionError if there is no active session.
        Returns the final, CLOSED session snapshot. Not affected by
        the manager's own IService lifecycle state, for the same
        reason as start_session().
        """
        raise NotImplementedError

    @abstractmethod
    def receive(
        self,
        text: str,
        *,
        workflow_id: Optional[str] = None,
        context: Optional[Mapping[str, Any]] = None,
    ) -> ConversationMessage:
        """
        Receive a user message on the active session and return the
        assistant's response message.

        Raises NoActiveSessionError if there is no active session (this
        also covers the case of a just-ended session: end_session()
        always clears the active session in the same call that closes
        it, so a CLOSED session is never reachable as "the active
        session"). Raises InvalidMessageError if `text` is not a
        non-empty string.
        Raises ConversationError if the manager's own IService state
        is not RUNNING (see manager.py's module docstring for why
        receive(), specifically, is gated on lifecycle state the same
        way Scheduler.tick() and WorkflowEngine.execute() are).

        Delegates intent classification to IIntentRouter.parse() -
        never classifies text itself. If `workflow_id` is given and
        currently registered in the Workflow Engine, delegates
        execution to IWorkflowEngine.execute() - never executes
        anything itself. See manager.py's module docstring for the
        full sequence of events published during one receive() call.
        """
        raise NotImplementedError

    @abstractmethod
    def history(
        self, session_id: Optional[str] = None
    ) -> Sequence[ConversationMessage]:
        """
        Return the message history for a session, oldest first.

        If session_id is omitted, returns the active session's
        history; raises NoActiveSessionError if there is none. If
        session_id is given, raises SessionNotFoundError if it does
        not match any session this manager has ever created (active
        or already CLOSED). Not affected by the manager's own
        IService lifecycle state.
        """
        raise NotImplementedError

    @abstractmethod
    def active_session(self) -> Optional[ConversationSession]:
        """
        Return the current active session's snapshot, or None if no
        session is active. Not affected by the manager's own IService
        lifecycle state.
        """
        raise NotImplementedError
