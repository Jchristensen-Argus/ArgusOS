"""Unit tests for argus.dispatcher.dispatcher.IntentDispatcher, as
revised by Package 013 (Capability Registry)."""

import functools
import logging
import unittest

from argus.capability import Capability, CapabilityRegistry
from argus.conversation import ConversationManager
from argus.dispatcher import (
    Action,
    ActionExecutionError,
    DispatcherError,
    IntentDispatcher,
    InvalidActionError,
    InvalidIntentError,
    NoCapabilityError,
    WorkflowAction,
    build_action_from_capability,
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


def _capability(intent_type, workflow_id, *, enabled=True):
    return Capability(
        name=f"{intent_type.name.title()} Capability",
        description="test capability",
        intent_types=(intent_type,),
        action_kind=WorkflowAction.kind,
        workflow_id=workflow_id,
        enabled=enabled,
    )


class DispatcherTestCase(unittest.TestCase):
    """Common setup: a started IntentDispatcher wired to a real,
    shared Event Bus, a real CapabilityRegistry, and a real
    WorkflowEngine-backed action_factory, with a spy subscribed to
    every event."""

    def setUp(self):
        self.event_bus = _event_bus()
        self.workflow_engine = _running_engine(self.event_bus)
        self.capability_registry = CapabilityRegistry(event_bus=self.event_bus)
        self.action_factory = functools.partial(
            build_action_from_capability, workflow_engine=self.workflow_engine
        )
        self.dispatcher = IntentDispatcher(
            event_bus=self.event_bus,
            capability_registry=self.capability_registry,
            action_factory=self.action_factory,
        )
        self.dispatcher.initialize()
        self.dispatcher.start()
        self.received = []
        for event_type in EventType:
            self.event_bus.subscribe(event_type, self.received.append)

    def _events_of(self, event_type):
        return [event for event in self.received if event.type == event_type]

    def _dispatcher_events(self):
        return [
            event.type for event in self.received if event.source == "intent_dispatcher"
        ]

    def _register_workflow_capability(self, intent_type=IntentType.QUESTION, name="answer"):
        workflow = self.workflow_engine.register_workflow(
            name=name,
            steps=[WorkflowStep("s", lambda ctx: {**ctx, "answered": True})],
        )
        self.capability_registry.register(_capability(intent_type, workflow.id))
        return workflow

    @staticmethod
    def _intent(name=IntentType.QUESTION, confidence=0.9):
        return Intent(name=name, confidence=confidence)


# -- IService lifecycle -------------------------------------------------


class IntentDispatcherIServiceTests(unittest.TestCase):
    def setUp(self):
        event_bus = _event_bus()
        self.capability_registry = CapabilityRegistry(event_bus=event_bus)
        self.dispatcher = IntentDispatcher(
            event_bus=event_bus,
            capability_registry=self.capability_registry,
            action_factory=lambda capability: None,
        )

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

    def test_resolve_works_before_start(self):
        self.capability_registry.register(_capability(IntentType.QUESTION, "wf"))
        capability = self.dispatcher.resolve(Intent(name=IntentType.QUESTION, confidence=1.0))
        self.assertEqual(capability.workflow_id, "wf")

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


# -- resolve() ------------------------------------------------------------


class ResolveTests(DispatcherTestCase):
    def test_resolve_returns_registered_capability(self):
        workflow = self._register_workflow_capability()

        capability = self.dispatcher.resolve(self._intent(IntentType.QUESTION))

        self.assertEqual(capability.workflow_id, workflow.id)

    def test_resolve_rejects_non_intent(self):
        with self.assertRaises(InvalidIntentError):
            self.dispatcher.resolve("not an intent")

    def test_resolve_unmapped_intent_raises_no_capability_error(self):
        with self.assertRaises(NoCapabilityError):
            self.dispatcher.resolve(self._intent(IntentType.UNKNOWN))

    def test_resolve_skips_disabled_capability(self):
        workflow = self.workflow_engine.register_workflow(
            name="disabled-wf", steps=[WorkflowStep("s", lambda ctx: ctx)]
        )
        self.capability_registry.register(
            _capability(IntentType.QUESTION, workflow.id, enabled=False)
        )

        with self.assertRaises(NoCapabilityError):
            self.dispatcher.resolve(self._intent(IntentType.QUESTION))

    def test_resolve_picks_first_enabled_match_in_registration_order(self):
        wf1 = self.workflow_engine.register_workflow(
            name="wf1", steps=[WorkflowStep("s", lambda ctx: ctx)]
        )
        wf2 = self.workflow_engine.register_workflow(
            name="wf2", steps=[WorkflowStep("s", lambda ctx: ctx)]
        )
        self.capability_registry.register(_capability(IntentType.QUESTION, wf1.id))
        self.capability_registry.register(
            Capability(
                name="Second",
                description="d",
                intent_types=(IntentType.QUESTION,),
                action_kind=WorkflowAction.kind,
                workflow_id=wf2.id,
            )
        )

        capability = self.dispatcher.resolve(self._intent(IntentType.QUESTION))

        self.assertEqual(capability.workflow_id, wf1.id)

    def test_resolve_skips_disabled_first_match_and_returns_next_enabled(self):
        wf1 = self.workflow_engine.register_workflow(
            name="wf1", steps=[WorkflowStep("s", lambda ctx: ctx)]
        )
        wf2 = self.workflow_engine.register_workflow(
            name="wf2", steps=[WorkflowStep("s", lambda ctx: ctx)]
        )
        self.capability_registry.register(
            _capability(IntentType.QUESTION, wf1.id, enabled=False)
        )
        self.capability_registry.register(
            Capability(
                name="Second",
                description="d",
                intent_types=(IntentType.QUESTION,),
                action_kind=WorkflowAction.kind,
                workflow_id=wf2.id,
            )
        )

        capability = self.dispatcher.resolve(self._intent(IntentType.QUESTION))

        self.assertEqual(capability.workflow_id, wf2.id)

    def test_resolve_does_not_publish_events(self):
        self._register_workflow_capability()
        # Registering the capability itself publishes
        # CapabilityRegistered (CapabilityRegistry's own event, not
        # the dispatcher's) - clear that before isolating resolve()'s
        # own behavior.
        self.received.clear()

        self.dispatcher.resolve(self._intent(IntentType.QUESTION))

        self.assertEqual(self.received, [])


# -- dispatch(): success path ---------------------------------------------


class DispatchSuccessTests(DispatcherTestCase):
    def test_dispatch_returns_action_execution_result(self):
        self._register_workflow_capability()

        result = self.dispatcher.dispatch(self._intent(IntentType.QUESTION))

        self.assertEqual(result, {"answered": True})

    def test_dispatch_passes_context_through(self):
        self._register_workflow_capability()

        result = self.dispatcher.dispatch(
            self._intent(IntentType.QUESTION), context={"seed": 1}
        )

        self.assertEqual(result, {"seed": 1, "answered": True})

    def test_dispatch_publishes_full_success_event_sequence_in_order(self):
        self._register_workflow_capability()

        self.dispatcher.dispatch(self._intent(IntentType.QUESTION))

        self.assertEqual(
            self._dispatcher_events(),
            [
                EventType.INTENT_DISPATCHED,
                EventType.ACTION_RESOLVED,
                EventType.WORKFLOW_SELECTED,
                EventType.DISPATCH_STARTED,
                EventType.DISPATCH_COMPLETED,
            ],
        )

    def test_action_resolved_payload_carries_capability_id_and_action_kind(self):
        workflow = self._register_workflow_capability()
        capability = self.capability_registry.find_by_intent_type(IntentType.QUESTION)[0]

        self.dispatcher.dispatch(self._intent(IntentType.QUESTION))

        resolved = self._events_of(EventType.ACTION_RESOLVED)[0]
        self.assertEqual(resolved.payload["capability_id"], capability.id)
        self.assertEqual(resolved.payload["action_kind"], "workflow")
        self.assertIsNotNone(workflow)

    def test_workflow_selected_payload_carries_workflow_id(self):
        workflow = self._register_workflow_capability()

        self.dispatcher.dispatch(self._intent(IntentType.QUESTION))

        selected = self._events_of(EventType.WORKFLOW_SELECTED)[0]
        self.assertEqual(selected.payload["workflow_id"], workflow.id)

    def test_no_dispatch_failed_on_success(self):
        self._register_workflow_capability()

        self.dispatcher.dispatch(self._intent(IntentType.QUESTION))

        self.assertEqual(self._events_of(EventType.DISPATCH_FAILED), [])

    def test_non_workflow_action_does_not_publish_workflow_selected(self):
        class _EchoAction(Action):
            kind = "echo"

            def execute(self, *, context=None):
                return dict(context or {})

        self.capability_registry.register(
            Capability(
                name="Echo",
                description="d",
                intent_types=(IntentType.QUESTION,),
                action_kind="echo",
            )
        )
        dispatcher = IntentDispatcher(
            event_bus=self.event_bus,
            capability_registry=self.capability_registry,
            action_factory=lambda capability: _EchoAction(),
        )
        dispatcher.initialize()
        dispatcher.start()

        dispatcher.dispatch(self._intent(IntentType.QUESTION))

        self.assertEqual(self._events_of(EventType.WORKFLOW_SELECTED), [])


# -- dispatch(): failure paths ----------------------------------------------


class DispatchFailureTests(DispatcherTestCase):
    def test_dispatch_rejects_non_intent(self):
        with self.assertRaises(InvalidIntentError):
            self.dispatcher.dispatch("not an intent")

    def test_dispatch_unknown_intent_raises_no_capability_error(self):
        with self.assertRaises(NoCapabilityError):
            self.dispatcher.dispatch(self._intent(IntentType.UNKNOWN))

    def test_dispatch_unknown_intent_publishes_dispatch_failed_with_resolve_stage(self):
        with self.assertRaises(NoCapabilityError):
            self.dispatcher.dispatch(self._intent(IntentType.UNKNOWN))

        failed = self._events_of(EventType.DISPATCH_FAILED)
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0].payload["stage"], "resolve")

    def test_dispatch_unknown_intent_event_sequence(self):
        with self.assertRaises(NoCapabilityError):
            self.dispatcher.dispatch(self._intent(IntentType.UNKNOWN))

        self.assertEqual(
            self._dispatcher_events(),
            [EventType.INTENT_DISPATCHED, EventType.DISPATCH_FAILED],
        )

    def test_unregistered_workflow_id_raises_action_execution_error(self):
        # The DEFAULT_WORKFLOW_IDS-style scenario: a capability
        # registered against a workflow_id nothing has actually
        # registered with the Workflow Engine yet.
        self.capability_registry.register(
            _capability(IntentType.QUESTION, "never-registered")
        )

        with self.assertRaises(ActionExecutionError):
            self.dispatcher.dispatch(self._intent(IntentType.QUESTION))

    def test_unregistered_workflow_id_wraps_workflow_not_found_error(self):
        self.capability_registry.register(
            _capability(IntentType.QUESTION, "never-registered")
        )

        try:
            self.dispatcher.dispatch(self._intent(IntentType.QUESTION))
            self.fail("expected ActionExecutionError")
        except ActionExecutionError as error:
            self.assertIsInstance(error.__cause__, WorkflowNotFoundError)

    def test_unregistered_workflow_id_publishes_dispatch_failed_with_execute_stage(self):
        self.capability_registry.register(
            _capability(IntentType.QUESTION, "never-registered")
        )

        with self.assertRaises(ActionExecutionError):
            self.dispatcher.dispatch(self._intent(IntentType.QUESTION))

        failed = self._events_of(EventType.DISPATCH_FAILED)
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0].payload["stage"], "execute")

    def test_unsupported_action_kind_raises_action_execution_error_with_build_stage(self):
        self.capability_registry.register(
            Capability(
                name="Unsupported",
                description="d",
                intent_types=(IntentType.QUESTION,),
                action_kind="plugin",
            )
        )

        with self.assertRaises(ActionExecutionError) as ctx:
            self.dispatcher.dispatch(self._intent(IntentType.QUESTION))
        self.assertIsInstance(ctx.exception.__cause__, InvalidActionError)

        failed = self._events_of(EventType.DISPATCH_FAILED)
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0].payload["stage"], "build")

    def test_failed_dispatch_does_not_publish_dispatch_completed(self):
        self.capability_registry.register(
            _capability(IntentType.QUESTION, "never-registered")
        )

        with self.assertRaises(ActionExecutionError):
            self.dispatcher.dispatch(self._intent(IntentType.QUESTION))

        self.assertEqual(self._events_of(EventType.DISPATCH_COMPLETED), [])


# -- Workflow Engine delegation -------------------------------------------


class WorkflowEngineDelegationTests(DispatcherTestCase):
    def test_dispatcher_never_imports_workflow_engine_module(self):
        # IntentDispatcher delegates exclusively through the injected
        # action_factory; it never imports argus.workflow itself - see
        # dispatcher.py's module docstring. Checked via the actual
        # import statements only (not the module's prose, which
        # legitimately explains this design decision by naming
        # argus.workflow/IWorkflowEngine in the text).
        import inspect

        import argus.dispatcher.dispatcher as dispatcher_module

        source = inspect.getsource(dispatcher_module)
        self.assertNotIn("from argus.workflow", source)
        self.assertNotIn("import argus.workflow", source)

    def test_dispatcher_never_imports_capability_registry_implementation(self):
        # dispatcher.py may depend on ICapabilityRegistry (the
        # interface, injected) but must never import the concrete
        # CapabilityRegistry class - matching the same
        # depend-on-interfaces-not-implementations discipline already
        # applied to IWorkflowEngine. Checked via the actual import
        # statement only: "CapabilityRegistry" as a bare substring
        # would false-positive against every legitimate mention of
        # "ICapabilityRegistry" in this module's own docstrings.
        import inspect

        import argus.dispatcher.dispatcher as dispatcher_module

        source = inspect.getsource(dispatcher_module)
        self.assertNotIn("from argus.capability.registry", source)
        self.assertNotIn("import argus.capability.registry", source)

    def test_real_workflow_actually_executes(self):
        calls = []
        workflow = self.workflow_engine.register_workflow(
            name="observed",
            steps=[WorkflowStep("s", lambda ctx: (calls.append(1), ctx)[1])],
        )
        self.capability_registry.register(_capability(IntentType.COMMAND, workflow.id))

        self.dispatcher.dispatch(self._intent(IntentType.COMMAND))

        self.assertEqual(calls, [1])
        self.assertEqual(self.workflow_engine.get_workflow(workflow.id).state.name, "COMPLETED")

    def test_failed_step_surfaces_as_completed_dispatch_not_a_raise(self):
        # A step that raises during execute() does not propagate out of
        # IWorkflowEngine.execute() (Package 010) - it marks the workflow
        # FAILED and returns the context normally. dispatch() therefore
        # succeeds (DispatchCompleted), and the caller must check the
        # workflow's own state to see the step failure.
        def _boom(ctx):
            raise RuntimeError("boom")

        workflow = self.workflow_engine.register_workflow(
            name="broken", steps=[WorkflowStep("s", _boom)]
        )
        self.capability_registry.register(_capability(IntentType.MEMORY, workflow.id))

        self.dispatcher.dispatch(self._intent(IntentType.MEMORY))  # must not raise

        self.assertEqual(self.workflow_engine.get_workflow(workflow.id).state.name, "FAILED")
        self.assertEqual(len(self._events_of(EventType.DISPATCH_COMPLETED)), 1)


# -- Conversation Manager integration / loose coupling ----------------------


class ConversationManagerIntegrationTests(unittest.TestCase):
    def test_dispatcher_never_imports_conversation_manager(self):
        import inspect

        import argus.dispatcher.action as action_module
        import argus.dispatcher.dispatcher as dispatcher_module
        import argus.dispatcher.interfaces as interfaces_module

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

        capability_registry = CapabilityRegistry(event_bus=event_bus)
        dispatcher = IntentDispatcher(
            event_bus=event_bus,
            capability_registry=capability_registry,
            action_factory=functools.partial(
                build_action_from_capability, workflow_engine=workflow_engine
            ),
        )
        dispatcher.initialize()
        dispatcher.start()
        workflow = workflow_engine.register_workflow(
            name="answer", steps=[WorkflowStep("s", lambda ctx: {**ctx, "done": True})]
        )
        capability_registry.register(_capability(IntentType.QUESTION, workflow.id))

        conversation_manager.receive("what time is it?")
        intent = intent_router.parse("what time is it?")

        result = dispatcher.dispatch(intent)

        self.assertEqual(result, {"done": True})


if __name__ == "__main__":
    unittest.main()
