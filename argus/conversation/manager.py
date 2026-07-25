"""
ConversationManager: deterministic session and message coordination
for the ArgusOS Conversation Manager.

Purpose:
    Implement IConversationManager: create and track a single active
    conversation session, record its message history, and coordinate
    two existing core services - the Intent Router (classification)
    and the Workflow Engine (execution) - to produce a response to
    each user message, per
    factory/packages/011_CONVERSATION_MANAGER.md.

Responsibilities:
    - start_session / end_session / active_session / history: an
      in-memory registry of every ConversationSession this manager has
      ever created, keyed by id, with at most one non-CLOSED
      ("active") session at a time. Registry operations are not
      affected by the manager's own IService lifecycle state, matching
      the precedent set by Scheduler's schedule/cancel/pause/resume
      (Package 008) and WorkflowEngine's register_workflow/cancel/
      get_workflow (Package 010).
    - receive: process one user message end-to-end. Delegates
      classification to IIntentRouter.parse() and, when a workflow_id
      is supplied and currently registered, delegates execution to
      IWorkflowEngine.execute(). ConversationManager never classifies
      text itself and never runs a workflow's steps itself - it only
      calls the two services' own public methods. Publishes, in order:
      MessageReceived (after the user message is appended),
      IntentResolved (after IIntentRouter.parse() returns),
      WorkflowExecuted (only if a workflow was actually delegated to),
      ResponseGenerated (after the assistant message is appended).
      Generates its response via a small, fixed, deterministic
      template keyed only on the resolved Intent's name - never via
      AI/LLM inference, per the work order's explicit Non-Goals.
    - initialize / start / stop / status, per the inherited IService
      contract. receive() *is* gated on the manager's own lifecycle
      state being RUNNING, mirroring Scheduler.tick() (Package 008)
      and WorkflowEngine.execute() (Package 010) - processing a
      message is exactly the kind of "active work" IService's own
      docstring describes gating. start_session/end_session/history/
      active_session remain ungated, matching the registry-operations
      precedent from both prior packages.

Non-Responsibilities:
    - ConversationManager contains no business logic belonging to
      another service: it never imports or references
      KnowledgeService, MemoryService, or Scheduler, and its only
      calls into IntentRouter/WorkflowEngine are through their own
      published interfaces (IIntentRouter.parse, IWorkflowEngine.
      execute). It does not call IIntentRouter.route() or
      register_handler() - broadcasting an Intent for *other*
      subscribers is a separate concern from this manager's own,
      synchronous use of the classification result. It does not call
      IWorkflowEngine.register_workflow() - workflows are assumed to
      already be registered elsewhere (e.g. during bootstrap or by
      another component); ConversationManager only ever executes a
      workflow_id the caller supplies.
    - No threading, no background execution, no persistence, no
      networking, no streaming, no plugins, no AI, no LLM, per the
      work order's explicit Version 1 Constraints. receive() runs
      entirely within the calling thread and returns only once a
      response has been generated.

Dependencies:
    argus.events (Event, EventType, IEventBus), argus.lifecycle
    (LifecycleState), argus.intent (IIntentRouter), argus.workflow
    (IWorkflowEngine, WorkflowError, WorkflowNotFoundError), and
    argus.conversation (ConversationSession, ConversationMessage,
    ConversationRole, ConversationState, and the conversation
    exceptions).
"""

from dataclasses import replace
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Optional, Sequence

from argus.conversation.exceptions import (
    ActiveSessionExistsError,
    ConversationError,
    InvalidMessageError,
    NoActiveSessionError,
    SessionNotFoundError,
)
from argus.conversation.interfaces import IConversationManager
from argus.conversation.message import ConversationMessage, ConversationRole
from argus.conversation.session import ConversationSession
from argus.conversation.state import ConversationState
from argus.events.event import Event
from argus.events.event_types import EventType
from argus.events.interfaces import IEventBus
from argus.intent.interfaces import IIntentRouter
from argus.lifecycle.lifecycle import LifecycleState
from argus.workflow.exceptions import WorkflowError, WorkflowNotFoundError
from argus.workflow.interfaces import IWorkflowEngine

# Fixed, deterministic response templates keyed by the resolved
# Intent's name (an IntentType value string, e.g. "question"). Never
# AI/LLM-generated - see the module docstring's Non-Responsibilities.
_RESPONSE_TEMPLATES: Mapping[str, str] = {
    "question": "I heard your question, but I have no way to answer it yet.",
    "command": "Acknowledged: I will not execute that automatically.",
    "memory": "Noted.",
    "schedule": "Understood; nothing has been scheduled automatically.",
    "unknown": "I'm not sure how to help with that yet.",
}
_DEFAULT_RESPONSE_TEMPLATE = "Received your message."


class ConversationManager(IConversationManager):
    """
    In-memory, synchronous implementation of IConversationManager.

    Purpose:
        Coordinate a single active conversation by delegating
        classification and execution to two existing core services,
        without the manager itself reasoning about either. See the
        module docstring for the full design rationale.

    Dependencies:
        An IEventBus, IIntentRouter, and IWorkflowEngine, all injected
        by the caller (bootstrap.py).
    """

    def __init__(
        self,
        event_bus: IEventBus,
        intent_router: IIntentRouter,
        workflow_engine: IWorkflowEngine,
    ) -> None:
        self._event_bus = event_bus
        self._intent_router = intent_router
        self._workflow_engine = workflow_engine
        self._state: LifecycleState = LifecycleState.CREATED
        self._sessions: Dict[str, ConversationSession] = {}
        self._active_session_id: Optional[str] = None

    # -- IService -----------------------------------------------------

    def initialize(self) -> None:
        if self._state != LifecycleState.CREATED:
            raise ConversationError(
                f"Cannot initialize: ConversationManager is {self._state.name}, expected CREATED."
            )
        self._state = LifecycleState.INITIALIZING

    def start(self) -> None:
        if self._state != LifecycleState.INITIALIZING:
            raise ConversationError(
                f"Cannot start: ConversationManager is {self._state.name}, expected INITIALIZING."
            )
        self._state = LifecycleState.RUNNING

    def stop(self) -> None:
        if self._state != LifecycleState.RUNNING:
            raise ConversationError(
                f"Cannot stop: ConversationManager is {self._state.name}, expected RUNNING."
            )
        self._state = LifecycleState.STOPPING
        self._state = LifecycleState.STOPPED

    def status(self) -> LifecycleState:
        return self._state

    # -- IConversationManager: registry operations (unaffected by lifecycle state) --

    def start_session(
        self, *, metadata: Optional[Mapping[str, Any]] = None
    ) -> ConversationSession:
        if self._active_session_id is not None:
            raise ActiveSessionExistsError(
                f"Session {self._active_session_id!r} is already active; "
                "Version 1 supports exactly one active session at a time."
            )

        session = ConversationSession(metadata=metadata or {})
        self._sessions[session.id] = session
        self._active_session_id = session.id
        self._publish(EventType.CONVERSATION_STARTED, {"session_id": session.id})
        return session

    def end_session(self) -> ConversationSession:
        session = self._require_active_session()

        closed = replace(
            session, state=ConversationState.CLOSED, updated_at=datetime.now(timezone.utc)
        )
        self._sessions[closed.id] = closed
        self._active_session_id = None
        self._publish(EventType.CONVERSATION_ENDED, {"session_id": closed.id})
        return closed

    def history(self, session_id: Optional[str] = None) -> Sequence[ConversationMessage]:
        if session_id is None:
            session = self._require_active_session()
        else:
            session = self._require_session(session_id)
        return session.messages

    def active_session(self) -> Optional[ConversationSession]:
        if self._active_session_id is None:
            return None
        return self._sessions[self._active_session_id]

    # -- IConversationManager: receive (gated on the manager's own RUNNING state) --

    def receive(
        self,
        text: str,
        *,
        workflow_id: Optional[str] = None,
        context: Optional[Mapping[str, Any]] = None,
    ) -> ConversationMessage:
        if self._state != LifecycleState.RUNNING:
            raise ConversationError(
                f"Cannot receive: ConversationManager is {self._state.name}, expected RUNNING."
            )
        if not isinstance(text, str) or not text:
            raise InvalidMessageError("receive() requires a non-empty string.")

        # _require_active_session() can never return a CLOSED session:
        # end_session() is the only path that sets ConversationState.
        # CLOSED, and it always clears _active_session_id in the same
        # call, so a CLOSED session is never the active one.
        session = self._require_active_session()
        session = self._transition(session, ConversationState.ACTIVE)

        user_message = ConversationMessage(role=ConversationRole.USER, content=text)
        session = self._append_message(session, user_message)
        self._publish(
            EventType.MESSAGE_RECEIVED,
            {"session_id": session.id, "message_id": user_message.id},
        )

        # Delegate classification to the Intent Router. This manager
        # never classifies text itself.
        intent = self._intent_router.parse(text)
        self._publish(
            EventType.INTENT_RESOLVED,
            {
                "session_id": session.id,
                "message_id": user_message.id,
                "intent_name": intent.name.value,
                "confidence": intent.confidence,
            },
        )

        # Delegate execution to the Workflow Engine, only if the
        # caller supplied a workflow_id and it is currently
        # registered and executable. This manager never executes a
        # workflow's steps itself.
        if workflow_id is not None:
            try:
                self._workflow_engine.execute(workflow_id, context=context)
            except (WorkflowNotFoundError, WorkflowError):
                pass
            else:
                self._publish(
                    EventType.WORKFLOW_EXECUTED,
                    {
                        "session_id": session.id,
                        "message_id": user_message.id,
                        "workflow_id": workflow_id,
                    },
                )

        response_content = _RESPONSE_TEMPLATES.get(
            intent.name.value, _DEFAULT_RESPONSE_TEMPLATE
        )
        assistant_message = ConversationMessage(
            role=ConversationRole.ASSISTANT, content=response_content
        )
        session = self._append_message(session, assistant_message)
        session = self._transition(session, ConversationState.WAITING)

        self._publish(
            EventType.RESPONSE_GENERATED,
            {"session_id": session.id, "message_id": assistant_message.id},
        )

        return assistant_message

    # -- internals ------------------------------------------------------

    def _require_active_session(self) -> ConversationSession:
        if self._active_session_id is None:
            raise NoActiveSessionError("There is no active session.")
        return self._sessions[self._active_session_id]

    def _require_session(self, session_id: str) -> ConversationSession:
        try:
            return self._sessions[session_id]
        except KeyError:
            raise SessionNotFoundError(
                f"No session found with id {session_id!r}."
            ) from None

    def _append_message(
        self, session: ConversationSession, message: ConversationMessage
    ) -> ConversationSession:
        updated = replace(
            session,
            messages=session.messages + (message,),
            updated_at=datetime.now(timezone.utc),
        )
        self._sessions[updated.id] = updated
        return updated

    def _transition(
        self, session: ConversationSession, state: ConversationState
    ) -> ConversationSession:
        updated = replace(session, state=state, updated_at=datetime.now(timezone.utc))
        self._sessions[updated.id] = updated
        return updated

    def _publish(self, event_type: EventType, payload: Dict[str, Any]) -> None:
        self._event_bus.publish(
            Event(type=event_type, source="conversation_manager", payload=payload)
        )
