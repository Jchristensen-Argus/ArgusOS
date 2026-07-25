"""Unit tests for argus.conversation.manager.ConversationManager."""

import logging
import unittest

from argus.conversation import (
    ActiveSessionExistsError,
    ConversationError,
    ConversationManager,
    ConversationRole,
    ConversationState,
    InvalidMessageError,
    NoActiveSessionError,
    SessionNotFoundError,
)
from argus.events import EventType, InMemoryEventBus
from argus.intent import IntentRouter
from argus.lifecycle import LifecycleState
from argus.workflow import WorkflowEngine, WorkflowStep


def _silent_logger() -> logging.Logger:
    logger = logging.getLogger("test_conversation_manager")
    logger.addHandler(logging.NullHandler())
    logger.propagate = False
    return logger


class ManagerTestCase(unittest.TestCase):
    """Common setup: a started ConversationManager wired to real
    IntentRouter and WorkflowEngine instances (also started), sharing
    one in-memory Event Bus that records every published event."""

    def setUp(self):
        self.event_bus = InMemoryEventBus(logger=_silent_logger())
        self.received = []
        for event_type in EventType:
            self.event_bus.subscribe(event_type, self._record)

        self.intent_router = IntentRouter(event_bus=self.event_bus)

        self.workflow_engine = WorkflowEngine(event_bus=self.event_bus)
        self.workflow_engine.initialize()
        self.workflow_engine.start()

        self.manager = ConversationManager(
            event_bus=self.event_bus,
            intent_router=self.intent_router,
            workflow_engine=self.workflow_engine,
        )
        self.manager.initialize()
        self.manager.start()

    def _record(self, event):
        self.received.append(event)

    def _events_of(self, event_type):
        return [event for event in self.received if event.type == event_type]


# -- IService lifecycle ---------------------------------------------------


class ConversationManagerIServiceTests(unittest.TestCase):
    def setUp(self):
        self.event_bus = InMemoryEventBus(logger=_silent_logger())
        self.intent_router = IntentRouter(event_bus=self.event_bus)
        self.workflow_engine = WorkflowEngine(event_bus=self.event_bus)
        self.manager = ConversationManager(
            event_bus=self.event_bus,
            intent_router=self.intent_router,
            workflow_engine=self.workflow_engine,
        )

    def test_initial_status_is_created(self):
        self.assertEqual(self.manager.status(), LifecycleState.CREATED)

    def test_full_happy_path(self):
        self.manager.initialize()
        self.assertEqual(self.manager.status(), LifecycleState.INITIALIZING)

        self.manager.start()
        self.assertEqual(self.manager.status(), LifecycleState.RUNNING)

        self.manager.stop()
        self.assertEqual(self.manager.status(), LifecycleState.STOPPED)

    def test_start_without_initialize_raises(self):
        with self.assertRaises(ConversationError):
            self.manager.start()

    def test_initialize_twice_raises(self):
        self.manager.initialize()

        with self.assertRaises(ConversationError):
            self.manager.initialize()

    def test_stop_without_start_raises(self):
        self.manager.initialize()

        with self.assertRaises(ConversationError):
            self.manager.stop()

    def test_registry_operations_work_before_start(self):
        session = self.manager.start_session()  # must not raise
        self.manager.active_session()
        self.manager.history()
        self.manager.end_session()
        self.assertIsNotNone(session)

    def test_receive_before_start_raises(self):
        self.manager.start_session()

        with self.assertRaises(ConversationError):
            self.manager.receive("hi")

    def test_receive_after_stop_raises(self):
        self.manager.start_session()
        self.manager.initialize()
        self.manager.start()
        self.manager.stop()

        with self.assertRaises(ConversationError):
            self.manager.receive("hi")


# -- start_session() / duplicate session handling --------------------------


class StartSessionTests(ManagerTestCase):
    def test_start_session_returns_new_session(self):
        session = self.manager.start_session()

        self.assertEqual(session.state, ConversationState.NEW)
        self.assertEqual(session.messages, ())

    def test_start_session_becomes_active_session(self):
        session = self.manager.start_session()

        self.assertEqual(self.manager.active_session().id, session.id)

    def test_start_session_honors_metadata(self):
        session = self.manager.start_session(metadata={"user": "joel"})

        self.assertEqual(session.metadata, {"user": "joel"})

    def test_start_session_publishes_conversation_started(self):
        session = self.manager.start_session()

        started = self._events_of(EventType.CONVERSATION_STARTED)
        self.assertEqual(len(started), 1)
        self.assertEqual(started[0].payload["session_id"], session.id)

    def test_start_session_while_active_raises(self):
        self.manager.start_session()

        with self.assertRaises(ActiveSessionExistsError):
            self.manager.start_session()

    def test_start_session_after_end_session_succeeds(self):
        self.manager.start_session()
        self.manager.end_session()

        second = self.manager.start_session()  # must not raise

        self.assertEqual(self.manager.active_session().id, second.id)


# -- end_session() -----------------------------------------------------


class EndSessionTests(ManagerTestCase):
    def test_end_session_closes_session(self):
        session = self.manager.start_session()

        closed = self.manager.end_session()

        self.assertEqual(closed.id, session.id)
        self.assertEqual(closed.state, ConversationState.CLOSED)

    def test_end_session_clears_active_session(self):
        self.manager.start_session()

        self.manager.end_session()

        self.assertIsNone(self.manager.active_session())

    def test_end_session_publishes_conversation_ended(self):
        session = self.manager.start_session()

        self.manager.end_session()

        ended = self._events_of(EventType.CONVERSATION_ENDED)
        self.assertEqual(len(ended), 1)
        self.assertEqual(ended[0].payload["session_id"], session.id)

    def test_end_session_without_active_session_raises(self):
        with self.assertRaises(NoActiveSessionError):
            self.manager.end_session()

    def test_end_session_twice_raises(self):
        self.manager.start_session()
        self.manager.end_session()

        with self.assertRaises(NoActiveSessionError):
            self.manager.end_session()


# -- receive(): message ordering, history, state transitions ---------------


class ReceiveTests(ManagerTestCase):
    def test_receive_without_active_session_raises(self):
        with self.assertRaises(NoActiveSessionError):
            self.manager.receive("hi")

    def test_receive_rejects_empty_string(self):
        self.manager.start_session()

        with self.assertRaises(InvalidMessageError):
            self.manager.receive("")

    def test_receive_rejects_non_string(self):
        self.manager.start_session()

        with self.assertRaises(InvalidMessageError):
            self.manager.receive(123)

    def test_receive_on_closed_session_raises(self):
        self.manager.start_session()
        self.manager.end_session()

        with self.assertRaises(NoActiveSessionError):
            self.manager.receive("hi")  # no active session at all now

    def test_receive_returns_assistant_message(self):
        self.manager.start_session()

        reply = self.manager.receive("What is corrugated board?")

        self.assertEqual(reply.role, ConversationRole.ASSISTANT)
        self.assertTrue(reply.content)

    def test_receive_appends_user_then_assistant_message_in_order(self):
        self.manager.start_session()

        self.manager.receive("hello")

        history = self.manager.history()
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].role, ConversationRole.USER)
        self.assertEqual(history[0].content, "hello")
        self.assertEqual(history[1].role, ConversationRole.ASSISTANT)

    def test_multiple_receive_calls_preserve_message_order(self):
        self.manager.start_session()

        self.manager.receive("first")
        self.manager.receive("second")

        history = self.manager.history()
        self.assertEqual(len(history), 4)
        self.assertEqual(
            [m.content for m in history],
            ["first", history[1].content, "second", history[3].content],
        )

    def test_receive_transitions_session_to_waiting_after_response(self):
        self.manager.start_session()

        self.manager.receive("hello")

        self.assertEqual(self.manager.active_session().state, ConversationState.WAITING)

    def test_receive_updates_session_updated_at(self):
        session = self.manager.start_session()

        self.manager.receive("hello")

        self.assertGreaterEqual(
            self.manager.active_session().updated_at, session.updated_at
        )

    def test_receive_publishes_message_received(self):
        self.manager.start_session()

        self.manager.receive("hello")

        received = self._events_of(EventType.MESSAGE_RECEIVED)
        self.assertEqual(len(received), 1)

    def test_receive_publishes_intent_resolved_with_delegated_classification(self):
        self.manager.start_session()

        self.manager.receive("Shutdown Argus")

        resolved = self._events_of(EventType.INTENT_RESOLVED)
        self.assertEqual(len(resolved), 1)
        self.assertEqual(resolved[0].payload["intent_name"], "command")

    def test_receive_publishes_response_generated(self):
        self.manager.start_session()

        self.manager.receive("hello")

        generated = self._events_of(EventType.RESPONSE_GENERATED)
        self.assertEqual(len(generated), 1)

    def test_receive_events_publish_in_order(self):
        self.manager.start_session()
        self.received.clear()

        self.manager.receive("hello")

        types_in_order = [e.type for e in self.received]
        # IIntentRouter.parse() itself publishes IntentParsed (its own
        # package's event, per Package 009) as a side effect of the
        # delegated call - that is expected, not a bug: this manager
        # only adds INTENT_RESOLVED as its own, additional record of
        # the same classification.
        self.assertEqual(
            types_in_order,
            [
                EventType.MESSAGE_RECEIVED,
                EventType.INTENT_PARSED,
                EventType.INTENT_RESOLVED,
                EventType.RESPONSE_GENERATED,
            ],
        )

    def test_response_content_varies_by_resolved_intent(self):
        self.manager.start_session()

        question_reply = self.manager.receive("What time is it?")
        self.manager.end_session()
        self.manager.start_session()
        command_reply = self.manager.receive("Shutdown Argus")

        self.assertNotEqual(question_reply.content, command_reply.content)


# -- delegation to Intent Router --------------------------------------------


class IntentRouterDelegationTests(ManagerTestCase):
    def test_manager_never_classifies_text_itself(self):
        # Delegation is proven structurally: the manager module must
        # not import anything from argus.intent.parser (the actual
        # classification logic), only the IIntentRouter interface it
        # calls.
        import argus.conversation.manager as manager_module

        source = __import__("inspect").getsource(manager_module)
        self.assertNotIn("argus.intent.parser", source)
        self.assertNotIn("parse_text", source)

    def test_receive_calls_intent_router_parse(self):
        calls = []
        original_parse = self.intent_router.parse

        def spy_parse(text):
            calls.append(text)
            return original_parse(text)

        self.intent_router.parse = spy_parse
        self.manager.start_session()

        self.manager.receive("Remember my dentist appointment")

        self.assertEqual(calls, ["Remember my dentist appointment"])


# -- delegation to Workflow Engine ------------------------------------------


class WorkflowEngineDelegationTests(ManagerTestCase):
    def _register_workflow(self):
        def step(ctx):
            return {**ctx, "ran": True}

        return self.workflow_engine.register_workflow(
            name="test-workflow", steps=[WorkflowStep("s", step)]
        )

    def test_receive_without_workflow_id_does_not_execute_anything(self):
        self.manager.start_session()

        self.manager.receive("hello")

        self.assertEqual(len(self._events_of(EventType.WORKFLOW_EXECUTED)), 0)

    def test_receive_with_workflow_id_delegates_execution(self):
        workflow = self._register_workflow()
        self.manager.start_session()

        self.manager.receive("do it", workflow_id=workflow.id)

        self.assertEqual(
            self.workflow_engine.get_workflow(workflow.id).state.name, "COMPLETED"
        )

    def test_receive_with_workflow_id_publishes_workflow_executed(self):
        workflow = self._register_workflow()
        self.manager.start_session()

        self.manager.receive("do it", workflow_id=workflow.id)

        executed = self._events_of(EventType.WORKFLOW_EXECUTED)
        self.assertEqual(len(executed), 1)
        self.assertEqual(executed[0].payload["workflow_id"], workflow.id)

    def test_receive_with_unknown_workflow_id_does_not_raise(self):
        self.manager.start_session()

        reply = self.manager.receive("do it", workflow_id="missing")  # must not raise

        self.assertEqual(reply.role, ConversationRole.ASSISTANT)

    def test_receive_with_unknown_workflow_id_does_not_publish_workflow_executed(self):
        self.manager.start_session()

        self.manager.receive("do it", workflow_id="missing")

        self.assertEqual(len(self._events_of(EventType.WORKFLOW_EXECUTED)), 0)

    def test_manager_never_imports_workflow_execution_internals(self):
        import argus.conversation.manager as manager_module

        source = __import__("inspect").getsource(manager_module)
        self.assertNotIn("argus.knowledge", source)
        self.assertNotIn("argus.memory", source)
        self.assertNotIn("argus.scheduler", source)


# -- history() / invalid session handling -----------------------------------


class HistoryTests(ManagerTestCase):
    def test_history_without_session_id_uses_active_session(self):
        self.manager.start_session()
        self.manager.receive("hi")

        history = self.manager.history()

        self.assertEqual(len(history), 2)

    def test_history_without_active_session_raises(self):
        with self.assertRaises(NoActiveSessionError):
            self.manager.history()

    def test_history_by_session_id_works_after_session_closed(self):
        session = self.manager.start_session()
        self.manager.receive("hi")
        self.manager.end_session()

        history = self.manager.history(session.id)

        self.assertEqual(len(history), 2)

    def test_history_with_unknown_session_id_raises(self):
        with self.assertRaises(SessionNotFoundError):
            self.manager.history("missing")

    def test_history_returns_messages_oldest_first(self):
        self.manager.start_session()
        self.manager.receive("first")
        self.manager.receive("second")

        history = self.manager.history()

        self.assertEqual(history[0].content, "first")
        self.assertEqual(history[2].content, "second")


# -- active_session() --------------------------------------------------


class ActiveSessionTests(ManagerTestCase):
    def test_active_session_none_when_no_session_started(self):
        self.assertIsNone(self.manager.active_session())

    def test_active_session_reflects_current_session(self):
        session = self.manager.start_session()

        self.assertEqual(self.manager.active_session().id, session.id)

    def test_active_session_none_after_end_session(self):
        self.manager.start_session()
        self.manager.end_session()

        self.assertIsNone(self.manager.active_session())


if __name__ == "__main__":
    unittest.main()
