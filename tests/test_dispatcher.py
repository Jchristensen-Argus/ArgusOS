"""Unit tests for argus.dispatcher.action (Action, WorkflowAction) and
argus.dispatcher.mapping (DEFAULT_WORKFLOW_IDS)."""

import logging
import unittest
from abc import ABC

from argus.dispatcher import Action, InvalidActionError, WorkflowAction
from argus.dispatcher.mapping import DEFAULT_WORKFLOW_IDS
from argus.events import InMemoryEventBus
from argus.intent import IntentType
from argus.workflow import WorkflowEngine, WorkflowStep


def _silent_logger() -> logging.Logger:
    logger = logging.getLogger("test_dispatcher")
    logger.addHandler(logging.NullHandler())
    logger.propagate = False
    return logger


def _engine():
    engine = WorkflowEngine(event_bus=InMemoryEventBus(logger=_silent_logger()))
    engine.initialize()
    engine.start()
    return engine


class ActionAbstractContractTests(unittest.TestCase):
    def test_action_is_abstract(self):
        self.assertTrue(issubclass(Action, ABC))
        with self.assertRaises(TypeError):
            Action()  # abstract - cannot be instantiated directly

    def test_action_has_default_kind(self):
        self.assertEqual(Action.kind, "action")

    def test_incomplete_subclass_cannot_be_instantiated(self):
        class Incomplete(Action):
            pass

        with self.assertRaises(TypeError):
            Incomplete()

    def test_complete_subclass_can_be_instantiated(self):
        class Complete(Action):
            def execute(self, *, context=None):
                return {}

        Complete()  # must not raise


class WorkflowActionConstructionTests(unittest.TestCase):
    def test_valid_construction(self):
        action = WorkflowAction(workflow_id="wf-1", workflow_engine=_engine())
        self.assertEqual(action.workflow_id, "wf-1")

    def test_kind_is_workflow(self):
        action = WorkflowAction(workflow_id="wf-1", workflow_engine=_engine())
        self.assertEqual(action.kind, "workflow")

    def test_is_an_action(self):
        action = WorkflowAction(workflow_id="wf-1", workflow_engine=_engine())
        self.assertIsInstance(action, Action)

    def test_empty_workflow_id_raises(self):
        with self.assertRaises(InvalidActionError):
            WorkflowAction(workflow_id="", workflow_engine=_engine())

    def test_non_string_workflow_id_raises(self):
        with self.assertRaises(InvalidActionError):
            WorkflowAction(workflow_id=123, workflow_engine=_engine())

    def test_invalid_workflow_engine_raises(self):
        with self.assertRaises(InvalidActionError):
            WorkflowAction(workflow_id="wf-1", workflow_engine=object())


class WorkflowActionExecuteTests(unittest.TestCase):
    def test_execute_delegates_to_workflow_engine(self):
        engine = _engine()
        workflow = engine.register_workflow(
            name="test",
            steps=[WorkflowStep("step", lambda ctx: {**ctx, "ran": True})],
        )
        action = WorkflowAction(workflow_id=workflow.id, workflow_engine=engine)

        result = action.execute(context={"start": True})

        self.assertEqual(result, {"start": True, "ran": True})
        self.assertEqual(engine.get_workflow(workflow.id).state.name, "COMPLETED")

    def test_execute_with_no_context_defaults_to_empty(self):
        engine = _engine()
        workflow = engine.register_workflow(
            name="test",
            steps=[WorkflowStep("step", lambda ctx: {**ctx, "ran": True})],
        )
        action = WorkflowAction(workflow_id=workflow.id, workflow_engine=engine)

        result = action.execute()

        self.assertEqual(result, {"ran": True})

    def test_execute_with_unregistered_workflow_id_raises(self):
        engine = _engine()
        action = WorkflowAction(workflow_id="missing", workflow_engine=engine)

        from argus.workflow import WorkflowNotFoundError

        with self.assertRaises(WorkflowNotFoundError):
            action.execute()

    def test_execute_does_not_catch_step_engine_errors(self):
        # execute() propagates whatever IWorkflowEngine.execute() raises;
        # it does not translate or swallow anything itself (see the
        # module's Non-Responsibilities) - proven here via an engine
        # that has never been started, so execute() raises WorkflowError.
        engine = WorkflowEngine(event_bus=InMemoryEventBus(logger=_silent_logger()))
        workflow = engine.register_workflow(
            name="test", steps=[WorkflowStep("step", lambda ctx: ctx)]
        )
        action = WorkflowAction(workflow_id=workflow.id, workflow_engine=engine)

        from argus.workflow import WorkflowError

        with self.assertRaises(WorkflowError):
            action.execute()


class DefaultWorkflowIdsTests(unittest.TestCase):
    def test_covers_every_intent_type(self):
        for intent_type in IntentType:
            self.assertIn(
                intent_type,
                DEFAULT_WORKFLOW_IDS,
                msg=f"{intent_type.name} has no default workflow_id",
            )

    def test_values_are_non_empty_strings(self):
        for workflow_id in DEFAULT_WORKFLOW_IDS.values():
            self.assertIsInstance(workflow_id, str)
            self.assertTrue(workflow_id)

    def test_values_are_unique(self):
        values = list(DEFAULT_WORKFLOW_IDS.values())
        self.assertEqual(len(values), len(set(values)))

    def test_is_read_only(self):
        with self.assertRaises(TypeError):
            DEFAULT_WORKFLOW_IDS[IntentType.QUESTION] = "changed"

    def test_expected_mapping_values(self):
        self.assertEqual(DEFAULT_WORKFLOW_IDS[IntentType.QUESTION], "answer_workflow")
        self.assertEqual(DEFAULT_WORKFLOW_IDS[IntentType.COMMAND], "command_workflow")
        self.assertEqual(DEFAULT_WORKFLOW_IDS[IntentType.MEMORY], "memory_workflow")
        self.assertEqual(DEFAULT_WORKFLOW_IDS[IntentType.SCHEDULE], "reminder_workflow")
        self.assertEqual(
            DEFAULT_WORKFLOW_IDS[IntentType.UNKNOWN], "unknown_handler_workflow"
        )


if __name__ == "__main__":
    unittest.main()
