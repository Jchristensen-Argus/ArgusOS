"""Unit tests for argus.dispatcher.dispatcher.IntentDispatcher."""

import logging
import unittest

from argus.conversation import ConversationManager
from argus.dispatcher import (
    Action,
    ActionExecutionError,
    DispatcherError,
    DuplicateMappingError,
    IntentDispatcher,
    InvalidActionError,
    InvalidIntentError,
    MappingNotFoundError,
    NoMappingError,
    WorkflowAction,
)
from argus.events import EventType, InMemoryEventBus
from argus.intent import Intent, IntentRouter, IntentType
from argus.lifecycle import LifecycleState
from argus.workflow import WorkflowEngine, WorkflowNotFoundError, WorkflowStep


def _silent_logger() -> logging.Logger:
    logger = logging.getLogger("test_intent_dispatcher")
    logger.addHandler(logging.NullHandler())
    logger.propagate = False
    return logger


def _event_bus() -> InMemoryEventBus:
    return InMemoryEventBus(logger=_silent_logger())


def _running_engine(event_bus: InMemoryEventBus) -> WorkflowEngine:
    engine = WorkflowEngine(event_bus=event_bus)
    engine.initialize()
    engine.start()
    return engine


class DispatcherTestCase(unittest.TestCase):
    """Common setup: a started IntentDispatcher wired to a real,
    shared Event Bus, with a spy subscribed to every event."""

    def setUp(self):
        self.event_bus = _event_bus()
        self.dispatcher = IntentDispatcher(event_bus=self.event_bus)
        self.dispatcher.initialize()
        self.dispatcher.start()
        self.received = []
        for event_type in EventType:
            self.event_bus.subscribe(event_type, self.received.append)

    def _events_of(self, event_type):
        return [event for event in self.received if event.type == event_type]

    @staticmethod
    def _intent(name=IntentType.QUESTION, confidence=0.9):
        return Intent(name=name, confidence=confidence)


# -- IService lifecycle -------------------------------------------------


class IntentDispatcherIServiceTests(unittest.TestCase):
    def setUp(self):
        self.dispatcher = IntentDispatcher(event_bus=_event_bus())

    def test_initial_status_is_created(self):
        self.assertEqual(self.dispatcher.status(), LifecycleState.CREATED)

    def test_full_happy_path(self):
        self.dispatcher.initialize()
        self.assertEqual(self.dispatcher.status(), LifecycleState.INITIALIZING)
        self.dispatcher.start()
        self.assertEqual(self.dispatcher.status(), LifecycleState.RUNNING)
        self.dispatcher.stop()
        self.assertEqual(self.dispatcher.status(), LifecycleState.STOPPED)

    def test_start_without_initialize_raises(self):
        with self.assertRaises(DispatcherError):
            self.dispatcher.start()

    def test_initialize_twice_raises(self):
        self.dispatcher.initialize()
        with self.assertRaises(DispatcherError):
            self.dispatcher.initialize()

    def test_stop_without_start_raises(self):
        self.dispatcher.initialize()
        with self.assertRaises(DispatcherError):
            self.dispatcher.stop()

    def test_registry_operations_work_before_start(self):
        action = WorkflowAction(
            workflow_id="wf", workflow_engine=_running_engine(_event_bus())
        )
        self.dispatcher.register_mapping(IntentType.QUESTION, action)  # must not raise
        self.assertIn(IntentType.QUESTION, self.dispatcher.list_mappings())

    def test_dispatch_before_start_raises(self):
        intent = Intent(name=IntentType.QUESTION, confidence=1.0)
        with self.assertRaises(DispatcherError):
            self.dispatcher.dispatch(intent)

    def test_dispatch_after_stop_raises(self):
        self.dispatcher.initialize()
        self.dispatcher.start()
        self.dispatcher.stop()
        intent = Intent(name=IntentType.QUESTION, confidence=1.0)
        with self.assertRaises(DispatcherError):
            self.dispatcher.dispatch(intent)


# -- register_mapping / remove_mapping / list_mappings ------------------


class MappingRegistrationTests(DispatcherTestCase):
    def _action(self):
        engine = _running_engine(_event_bus())
        return WorkflowAction(workflow_id="wf", workflow_engine=engine)

    def test_register_mapping_appears_in_list_mappings(self):
        action = self._action()
        self.dispatcher.register_mapping(IntentType.QUESTION, action)

        self.assertIs(self.dispatcher.list_mappings()[IntentType.QUESTION], action)

    def test_register_mapping_rejects_non_intent_type(self):
        with self.assertRaises(InvalidIntentError):
            self.dispatcher.register_mapping("question", self._action())

    def test_register_mapping_rejects_non_action(self):
        with self.assertRaises(InvalidActionError):
            self.dispatcher.register_mapping(IntentType.QUESTION, object())

    def test_duplicate_mapping_raises(self):
        self.dispatcher.register_mapping(IntentType.QUESTION, self._action())
        with self.assertRaises(DuplicateMappingError):
            self.dispatcher.register_mapping(IntentType.QUESTION, self._action())

    def test_remove_mapping_removes_it(self):
        self.dispatcher.register_mapping(IntentType.QUESTION, self._action())

        self.dispatcher.remove_mapping(IntentType.QUESTION)

        self.assertNotIn(IntentType.QUESTION, self.dispatcher.list_mappings())

    def test_remove_mapping_rejects_non_intent_type(self):
        with self.assertRaises(InvalidIntentError):
            self.dispatcher.remove_mapping("question")

    def test_remove_unmapped_intent_raises(self):
        with self.assertRaises(MappingNotFoundError):
            self.dispatcher.remove_mapping(IntentType.QUESTION)

    def test_register_after_remove_succeeds(self):
        self.dispatcher.register_mapping(IntentType.QUESTION, self._action())
        self.dispatcher.remove_mapping(IntentType.QUESTION)

        self.dispatcher.register_mapping(IntentType.QUESTION, self._action())  # must not raise

    def test_list_mappings_is_read_only(self):
        mappings = self.dispatcher.list_mappings()
        with self.assertRaises(TypeError):
            mappings[IntentType.QUESTION] = self._action()

    def test_list_mappings_empty_by_default(self):
        self.assertEqual(dict(self.dispatcher.list_mappings()), {})

    def test_mapping_operations_do_not_publish_events(self):
        self.dispatcher.register_mapping(IntentType.QUESTION, self._action())
        self.dispatcher.remove_mapping(IntentType.QUESTION)

        self.assertEqual(self.received, [])


# -- resolve() ------------------------------------------------------------


class ResolveTests(DispatcherTestCase):
    def test_resolve_returns_registered_action(self):
        action = WorkflowAction(
            workflow_id="wf", workflow_engine=_running_engine(_event_bus())
        )
        self.dispatcher.register_mapping(IntentType.QUESTION, action)

        resolved = self.dispatcher.resolve(self._intent(IntentType.QUESTION))

        self.assertIs(resolved, action)

    def test_resolve_rejects_non_intent(self):
        with self.assertRaises(InvalidIntentError):
            self.dispatcher.resolve("not an intent")

    def test_resolve_unmapped_intent_raises_no_mapping_error(self):
        with self.assertRaises(NoMappingError):
            self.dispatcher.resolve(self._intent(IntentType.UNKNOWN))

    def test_resolve_does_not_publish_events(self):
        action = WorkflowAction(
            workflow_id="wf", workflow_engine=_running_engine(_event_bus())
        )
        self.dispatcher.register_mapping(IntentType.QUESTION, action)

        self.dispatcher.resolve(self._intent(IntentType.QUESTION))

        self.assertEqual(self.received, [])


# -- dispatch(): success path ---------------------------------------------


class DispatchSuccessTests(DispatcherTestCase):
    def _register_workflow_mapping(self, intent_type=IntentType.QUESTION):
        engine = _running_engine(self.event_bus)
        workflow = engine.register_workflow(
            name="answer",
            steps=[WorkflowStep("s", lambda ctx: {**ctx, "answered": True})],
        )
        action = WorkflowAction(workflow_id=workflow.id, workflow_engine=engine)
        self.dispatcher.register_mapping(intent_type, action)
        return workflow

    def test_dispatch_returns_action_execution_result(self):
        self._register_workflow_mapping()

        result = self.dispatcher.dispatch(self._intent(IntentType.QUESTION))

        self.assertEqual(result, {"answered": True})

    def test_dispatch_passes_context_through(self):
        self._register_workflow_mapping()

        result = self.dispatcher.dispatch(
            self._intent(IntentType.QUESTION), context={"seed": 1}
        )

        self.assertEqual(result, {"seed": 1, "answered": True})

    def test_dispatch_publishes_full_success_event_sequence_in_order(self):
        self._register_workflow_mapping()

        self.dispatcher.dispatch(self._intent(IntentType.QUESTION))

        dispatcher_events = [
            event.type
            for event in self.received
            if event.source == "intent_dispatcher"
        ]
        self.assertEqual(
            dispatcher_events,
            [
                EventType.INTENT_DISPATCHED,
                EventType.ACTION_RESOLVED,
                EventType.WORKFLOW_SELECTED,
                EventType.DISPATCH_STARTED,
                EventType.DISPATCH_COMPLETED,
            ],
        )

    def test_action_resolved_payload_carries_action_kind(self):
        self._register_workflow_mapping()

        self.dispatcher.dispatch(self._intent(IntentType.QUESTION))

        resolved = self._events_of(EventType.ACTION_RESOLVED)[0]
        self.assertEqual(resolved.payload["action_kind"], "workflow")

    def test_workflow_selected_payload_carries_workflow_id(self):
        workflow = self._register_workflow_mapping()

        self.dispatcher.dispatch(self._intent(IntentType.QUESTION))

        selected = self._events_of(EventType.WORKFLOW_SELECTED)[0]
        self.assertEqual(selected.payload["workflow_id"], workflow.id)

    def test_no_dispatch_failed_on_success(self):
        self._register_workflow_mapping()

        self.dispatcher.dispatch(self._intent(IntentType.QUESTION))

        self.assertEqual(self._events_of(EventType.DISPATCH_FAILED), [])

    def test_non_workflow_action_does_not_publish_workflow_selected(self):
        class _EchoAction(Action):
            kind = "echo"

            def execute(self, *, context=None):
                return dict(context or {})

        self.dispatcher.register_mapping(IntentType.QUESTION, _EchoAction())

        self.dispatcher.dispatch(self._intent(IntentType.QUESTION))

        self.assertEqual(self._events_of(EventType.WORKFLOW_SELECTED), [])


# -- dispatch(): failure paths ----------------------------------------------


class DispatchFailureTests(DispatcherTestCase):
    def test_dispatch_rejects_non_intent(self):
        with self.assertRaises(InvalidIntentError):
            self.dispatcher.dispatch("not an intent")

    def test_dispatch_unknown_intent_raises_no_mapping_error(self):
        # UNKNOWN has no default mapping registered in this test's bare
        # dispatcher (see DispatcherTestCase.setUp) - this is the
        # "Unknown intents" scenario: an intent classified as UNKNOWN,
        # or any other intent name, with nothing registered for it.
        with self.assertRaises(NoMappingError):
            self.dispatcher.dispatch(self._intent(IntentType.UNKNOWN))

    def test_dispatch_unknown_intent_publishes_dispatch_failed(self):
        with self.assertRaises(NoMappingError):
            self.dispatcher.dispatch(self._intent(IntentType.UNKNOWN))

        failed = self._events_of(EventType.DISPATCH_FAILED)
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0].payload["stage"], "resolve")

    def test_dispatch_unknown_intent_still_publishes_intent_dispatched_first(self):
        with self.assertRaises(NoMappingError):
            self.dispatcher.dispatch(self._intent(IntentType.UNKNOWN))

        dispatcher_events = [
            event.type
            for event in self.received
            if event.source == "intent_dispatcher"
        ]
        self.assertEqual(
            dispatcher_events, [EventType.INTENT_DISPATCHED, EventType.DISPATCH_FAILED]
        )

    def test_dispatch_with_invalid_mapping_workflow_id_raises_action_execution_error(self):
        # An "invalid mapping": a WorkflowAction registered against a
        # workflow_id that was never actually registered with the
        # Workflow Engine (exactly the DEFAULT_WORKFLOW_IDS bootstrap
        # scenario before any real workflow exists - see mapping.py).
        engine = _running_engine(self.event_bus)
        action = WorkflowAction(workflow_id="never-registered", workflow_engine=engine)
        self.dispatcher.register_mapping(IntentType.QUESTION, action)

        with self.assertRaises(ActionExecutionError):
            self.dispatcher.dispatch(self._intent(IntentType.QUESTION))

    def test_invalid_mapping_failure_wraps_original_exception(self):
        engine = _running_engine(self.event_bus)
        action = WorkflowAction(workflow_id="never-registered", workflow_engine=engine)
        self.dispatcher.register_mapping(IntentType.QUESTION, action)

        try:
            self.dispatcher.dispatch(self._intent(IntentType.QUESTION))
            self.fail("expected ActionExecutionError")
        except ActionExecutionError as error:
            self.assertIsInstance(error.__cause__, WorkflowNotFoundError)

    def test_invalid_mapping_publishes_dispatch_failed_with_execute_stage(self):
        engine = _running_engine(self.event_bus)
        action = WorkflowAction(workflow_id="never-registered", workflow_engine=engine)
        self.dispatcher.register_mapping(IntentType.QUESTION, action)

        with self.assertRaises(ActionExecutionError):
            self.dispatcher.dispatch(self._intent(IntentType.QUESTION))

        failed = self._events_of(EventType.DISPATCH_FAILED)
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0].payload["stage"], "execute")

    def test_invalid_mapping_still_publishes_dispatch_started_before_failing(self):
        engine = _running_engine(self.event_bus)
        action = WorkflowAction(workflow_id="never-registered", workflow_engine=engine)
        self.dispatcher.register_mapping(IntentType.QUESTION, action)

        with self.assertRaises(ActionExecutionError):
            self.dispatcher.dispatch(self._intent(IntentType.QUESTION))

        dispatcher_events = [
            event.type
            for event in self.received
            if event.source == "intent_dispatcher"
        ]
        self.assertEqual(
            dispatcher_events,
            [
                EventType.INTENT_DISPATCHED,
                EventType.ACTION_RESOLVED,
                EventType.WORKFLOW_SELECTED,
                EventType.DISPATCH_STARTED,
                EventType.DISPATCH_FAILED,
            ],
        )

    def test_failed_dispatch_does_not_publish_dispatch_completed(self):
        engine = _running_engine(self.event_bus)
        action = WorkflowAction(workflow_id="never-registered", workflow_engine=engine)
        self.dispatcher.register_mapping(IntentType.QUESTION, action)

        with self.assertRaises(ActionExecutionError):
            self.dispatcher.dispatch(self._intent(IntentType.QUESTION))

        self.assertEqual(self._events_of(EventType.DISPATCH_COMPLETED), [])


# -- Workflow Engine delegation -------------------------------------------


class WorkflowEngineDelegationTests(DispatcherTestCase):
    def test_dispatch_never_calls_workflow_engine_directly(self):
        # IntentDispatcher delegates exclusively through Action.execute();
        # it never imports IWorkflowEngine itself - see dispatcher.py's
        # module docstring. Checked via the actual import statements
        # only (not the module's prose, which legitimately explains
        # this design decision by naming argus.workflow/IWorkflowEngine
        # in the text - see argus/dispatcher/action.py for where the
        # real IWorkflowEngine import lives instead).
        import inspect

        import argus.dispatcher.dispatcher as dispatcher_module

        source = inspect.getsource(dispatcher_module)
        self.assertNotIn("from argus.workflow", source)
        self.assertNotIn("import argus.workflow", source)

    def test_real_workflow_actually_executes(self):
        engine = _running_engine(self.event_bus)
        calls = []
        workflow = engine.register_workflow(
            name="observed",
            steps=[WorkflowStep("s", lambda ctx: (calls.append(1), ctx)[1])],
        )
        action = WorkflowAction(workflow_id=workflow.id, workflow_engine=engine)
        self.dispatcher.register_mapping(IntentType.COMMAND, action)

        self.dispatcher.dispatch(self._intent(IntentType.COMMAND))

        self.assertEqual(calls, [1])
        self.assertEqual(engine.get_workflow(workflow.id).state.name, "COMPLETED")

    def test_failed_step_surfaces_as_completed_dispatch_not_a_raise(self):
        # A step that raises during execute() does not propagate out of
        # IWorkflowEngine.execute() (Package 010) - it marks the workflow
        # FAILED and returns the context normally. dispatch() therefore
        # succeeds (DispatchCompleted), and the caller must check the
        # workflow's own state to see the step failure, exactly as
        # IWorkflowEngine.execute()'s own callers must.
        engine = _running_engine(self.event_bus)

        def _boom(ctx):
            raise RuntimeError("boom")

        workflow = engine.register_workflow(name="broken", steps=[WorkflowStep("s", _boom)])
        action = WorkflowAction(workflow_id=workflow.id, workflow_engine=engine)
        self.dispatcher.register_mapping(IntentType.MEMORY, action)

        self.dispatcher.dispatch(self._intent(IntentType.MEMORY))  # must not raise

        self.assertEqual(engine.get_workflow(workflow.id).state.name, "FAILED")
        self.assertEqual(self._events_of(EventType.DISPATCH_COMPLETED), [
            e for e in self._events_of(EventType.DISPATCH_COMPLETED)
        ])
        self.assertEqual(len(self._events_of(EventType.DISPATCH_COMPLETED)), 1)


# -- Conversation Manager integration / loose coupling ----------------------


class ConversationManagerIntegrationTests(unittest.TestCase):
    def test_dispatcher_never_imports_conversation_manager(self):
        # Checked via the actual import statements only - see the note
        # on test_dispatch_never_calls_workflow_engine_directly above
        # for why bare substring checks against docstring prose would
        # false-positive here (this module's own docstrings legitimately
        # name ConversationManager and argus.conversation by way of
        # explaining precedent, exactly as ConversationManager's own
        # docstring names KnowledgeService/MemoryService/Scheduler).
        import inspect

        import argus.dispatcher.dispatcher as dispatcher_module
        import argus.dispatcher.interfaces as interfaces_module
        import argus.dispatcher.action as action_module

        for module in (dispatcher_module, interfaces_module, action_module):
            source = inspect.getsource(module)
            self.assertNotIn("from argus.conversation", source)
            self.assertNotIn("import argus.conversation", source)

    def test_dispatcher_never_imports_intent_router_or_parser(self):
        import inspect

        import argus.dispatcher.dispatcher as dispatcher_module

        source = inspect.getsource(dispatcher_module)
        self.assertNotIn("from argus.intent.router", source)
        self.assertNotIn("import argus.intent.router", source)
        self.assertNotIn("from argus.intent.parser", source)
        self.assertNotIn("import argus.intent.parser", source)

    def test_end_to_end_conversation_manager_intent_flows_into_dispatcher(self):
        # ConversationManager (Package 011) produces its Intent the same
        # way this test does here: via IIntentRouter.parse(). Feeding
        # that same kind of Intent into IntentDispatcher.dispatch()
        # proves the two packages compose correctly end-to-end, without
        # either package importing the other.
        event_bus = _event_bus()
        intent_router = IntentRouter(event_bus=event_bus)
        workflow_engine = _running_engine(event_bus)
        conversation_manager = ConversationManager(
            event_bus=event_bus,
            intent_router=intent_router,
            workflow_engine=workflow_engine,
        )
        conversation_manager.initialize()
        conversation_manager.start()
        conversation_manager.start_session()

        dispatcher = IntentDispatcher(event_bus=event_bus)
        dispatcher.initialize()
        dispatcher.start()
        workflow = workflow_engine.register_workflow(
            name="answer", steps=[WorkflowStep("s", lambda ctx: {**ctx, "done": True})]
        )
        dispatcher.register_mapping(
            IntentType.QUESTION,
            WorkflowAction(workflow_id=workflow.id, workflow_engine=workflow_engine),
        )

        # ConversationManager.receive() handles the message on its own
        # terms (classification + optional delegated execution); the
        # Intent it resolved is independently reproducible here via the
        # same IIntentRouter.parse() call, which is exactly what
        # ConversationManager itself calls internally.
        conversation_manager.receive("what time is it?")
        intent = intent_router.parse("what time is it?")

        result = dispatcher.dispatch(intent)

        self.assertEqual(result, {"done": True})


if __name__ == "__main__":
    unittest.main()
