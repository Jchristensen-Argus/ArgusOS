"""Unit tests for argus.workflow.engine.WorkflowEngine."""

import logging
import unittest

from argus.events import EventType, InMemoryEventBus
from argus.lifecycle import LifecycleState
from argus.workflow import (
    DuplicateWorkflowError,
    InvalidWorkflowError,
    WorkflowEngine,
    WorkflowError,
    WorkflowNotFoundError,
    WorkflowState,
    WorkflowStep,
)


def _silent_logger() -> logging.Logger:
    logger = logging.getLogger("test_workflow_engine")
    logger.addHandler(logging.NullHandler())
    logger.propagate = False
    return logger


def _append(ctx, key, value):
    updated = dict(ctx)
    updated[key] = value
    return updated


class EngineTestCase(unittest.TestCase):
    """Common setup: a started WorkflowEngine with an in-memory Event
    Bus recording every published event, keyed by EventType."""

    def setUp(self):
        self.event_bus = InMemoryEventBus(logger=_silent_logger())
        self.received = []
        for event_type in EventType:
            self.event_bus.subscribe(event_type, self._record)
        self.engine = WorkflowEngine(event_bus=self.event_bus)
        self.engine.initialize()
        self.engine.start()

    def _record(self, event):
        self.received.append(event)

    def _events_of(self, event_type):
        return [event for event in self.received if event.type == event_type]

    def _step(self, name, key, value):
        return WorkflowStep(name=name, action=lambda ctx: _append(ctx, key, value))


# -- IService lifecycle ---------------------------------------------------


class WorkflowEngineIServiceTests(unittest.TestCase):
    def setUp(self):
        self.event_bus = InMemoryEventBus(logger=_silent_logger())
        self.engine = WorkflowEngine(event_bus=self.event_bus)

    def test_initial_status_is_created(self):
        self.assertEqual(self.engine.status(), LifecycleState.CREATED)

    def test_full_happy_path(self):
        self.engine.initialize()
        self.assertEqual(self.engine.status(), LifecycleState.INITIALIZING)

        self.engine.start()
        self.assertEqual(self.engine.status(), LifecycleState.RUNNING)

        self.engine.stop()
        self.assertEqual(self.engine.status(), LifecycleState.STOPPED)

    def test_start_without_initialize_raises(self):
        with self.assertRaises(WorkflowError):
            self.engine.start()

    def test_initialize_twice_raises(self):
        self.engine.initialize()

        with self.assertRaises(WorkflowError):
            self.engine.initialize()

    def test_stop_without_start_raises(self):
        self.engine.initialize()

        with self.assertRaises(WorkflowError):
            self.engine.stop()

    def test_registry_operations_work_before_start(self):
        step = WorkflowStep(name="s", action=lambda ctx: ctx)
        workflow = self.engine.register_workflow(name="wf", steps=[step])
        self.engine.cancel(workflow.id)  # must not raise

    def test_execute_before_start_raises(self):
        step = WorkflowStep(name="s", action=lambda ctx: ctx)
        workflow = self.engine.register_workflow(name="wf", steps=[step])

        with self.assertRaises(WorkflowError):
            self.engine.execute(workflow.id)

    def test_execute_after_stop_raises(self):
        step = WorkflowStep(name="s", action=lambda ctx: ctx)
        workflow = self.engine.register_workflow(name="wf", steps=[step])
        self.engine.initialize()
        self.engine.start()
        self.engine.stop()

        with self.assertRaises(WorkflowError):
            self.engine.execute(workflow.id)


# -- register_workflow() ---------------------------------------------------


class RegisterWorkflowTests(EngineTestCase):
    def test_register_returns_pending_workflow(self):
        workflow = self.engine.register_workflow(name="wf", steps=[self._step("s", "k", 1)])

        self.assertEqual(workflow.name, "wf")
        self.assertEqual(workflow.state, WorkflowState.PENDING)
        self.assertEqual(len(workflow.steps), 1)

    def test_register_generates_id_when_not_given(self):
        workflow = self.engine.register_workflow(name="wf", steps=[self._step("s", "k", 1)])

        self.assertTrue(workflow.id)

    def test_register_honors_explicit_workflow_id(self):
        workflow = self.engine.register_workflow(
            name="wf", steps=[self._step("s", "k", 1)], workflow_id="my-id"
        )

        self.assertEqual(workflow.id, "my-id")

    def test_register_honors_metadata(self):
        workflow = self.engine.register_workflow(
            name="wf", steps=[self._step("s", "k", 1)], metadata={"owner": "founder"}
        )

        self.assertEqual(workflow.metadata, {"owner": "founder"})

    def test_register_publishes_no_event(self):
        self.engine.register_workflow(name="wf", steps=[self._step("s", "k", 1)])

        self.assertEqual(len(self.received), 0)

    def test_register_duplicate_workflow_id_raises(self):
        self.engine.register_workflow(
            name="wf", steps=[self._step("s", "k", 1)], workflow_id="dup"
        )

        with self.assertRaises(DuplicateWorkflowError):
            self.engine.register_workflow(
                name="wf2", steps=[self._step("s", "k", 1)], workflow_id="dup"
            )

    def test_register_rejects_empty_name(self):
        with self.assertRaises(InvalidWorkflowError):
            self.engine.register_workflow(name="", steps=[self._step("s", "k", 1)])

    def test_register_rejects_empty_steps(self):
        with self.assertRaises(InvalidWorkflowError):
            self.engine.register_workflow(name="wf", steps=[])

    def test_register_rejects_non_workflow_step_element(self):
        with self.assertRaises(InvalidWorkflowError):
            self.engine.register_workflow(name="wf", steps=["not-a-step"])

    def test_register_rejects_non_callable_step_action(self):
        with self.assertRaises(InvalidWorkflowError):
            self.engine.register_workflow(
                name="wf", steps=[WorkflowStep(name="s", action="not-callable")]
            )


# -- execute(): sequential ordering and success ----------------------------


class ExecuteSuccessTests(EngineTestCase):
    def test_single_step_workflow_completes(self):
        workflow = self.engine.register_workflow(name="wf", steps=[self._step("s", "a", 1)])

        result = self.engine.execute(workflow.id)

        self.assertEqual(result, {"a": 1})
        self.assertEqual(self.engine.get_workflow(workflow.id).state, WorkflowState.COMPLETED)

    def test_steps_run_in_order_and_context_threads_through(self):
        steps = [
            WorkflowStep(name="add-a", action=lambda ctx: _append(ctx, "a", 1)),
            WorkflowStep(
                name="add-b", action=lambda ctx: _append(ctx, "b", ctx["a"] + 1)
            ),
            WorkflowStep(
                name="add-c", action=lambda ctx: _append(ctx, "c", ctx["b"] + 1)
            ),
        ]
        workflow = self.engine.register_workflow(name="wf", steps=steps)

        result = self.engine.execute(workflow.id)

        self.assertEqual(result, {"a": 1, "b": 2, "c": 3})

    def test_execute_honors_initial_context(self):
        workflow = self.engine.register_workflow(
            name="wf", steps=[self._step("s", "b", 2)]
        )

        result = self.engine.execute(workflow.id, context={"a": 1})

        self.assertEqual(result, {"a": 1, "b": 2})

    def test_execute_sets_started_at_and_completed_at(self):
        workflow = self.engine.register_workflow(name="wf", steps=[self._step("s", "a", 1)])

        self.engine.execute(workflow.id)

        finished = self.engine.get_workflow(workflow.id)
        self.assertIsNotNone(finished.started_at)
        self.assertIsNotNone(finished.completed_at)

    def test_execute_publishes_started_then_step_events_then_completed_in_order(self):
        steps = [self._step("first", "a", 1), self._step("second", "b", 2)]
        workflow = self.engine.register_workflow(name="wf", steps=steps)

        self.engine.execute(workflow.id)

        types_in_order = [e.type for e in self.received]
        self.assertEqual(
            types_in_order,
            [
                EventType.WORKFLOW_STARTED,
                EventType.WORKFLOW_STEP_STARTED,
                EventType.WORKFLOW_STEP_COMPLETED,
                EventType.WORKFLOW_STEP_STARTED,
                EventType.WORKFLOW_STEP_COMPLETED,
                EventType.WORKFLOW_COMPLETED,
            ],
        )

    def test_step_started_and_completed_events_carry_step_name_and_index(self):
        steps = [self._step("first", "a", 1), self._step("second", "b", 2)]
        workflow = self.engine.register_workflow(name="wf", steps=steps)

        self.engine.execute(workflow.id)

        started_events = self._events_of(EventType.WORKFLOW_STEP_STARTED)
        self.assertEqual(started_events[0].payload["step_name"], "first")
        self.assertEqual(started_events[0].payload["step_index"], 0)
        self.assertEqual(started_events[1].payload["step_name"], "second")
        self.assertEqual(started_events[1].payload["step_index"], 1)

    def test_workflow_started_event_carries_workflow_id_and_name(self):
        workflow = self.engine.register_workflow(name="my-workflow", steps=[self._step("s", "a", 1)])

        self.engine.execute(workflow.id)

        started = self._events_of(EventType.WORKFLOW_STARTED)
        self.assertEqual(len(started), 1)
        self.assertEqual(started[0].payload["workflow_id"], workflow.id)
        self.assertEqual(started[0].payload["name"], "my-workflow")

    def test_execute_of_missing_workflow_raises_not_found(self):
        with self.assertRaises(WorkflowNotFoundError):
            self.engine.execute("missing")

    def test_execute_of_already_completed_workflow_raises(self):
        workflow = self.engine.register_workflow(name="wf", steps=[self._step("s", "a", 1)])
        self.engine.execute(workflow.id)

        with self.assertRaises(WorkflowError):
            self.engine.execute(workflow.id)


# -- execute(): failure handling --------------------------------------------


class ExecuteFailureTests(EngineTestCase):
    def _failing_step(self, name):
        def action(ctx):
            raise ValueError("boom")

        return WorkflowStep(name=name, action=action)

    def test_failing_step_marks_workflow_failed(self):
        workflow = self.engine.register_workflow(
            name="wf", steps=[self._step("ok", "a", 1), self._failing_step("bad")]
        )

        self.engine.execute(workflow.id)

        self.assertEqual(self.engine.get_workflow(workflow.id).state, WorkflowState.FAILED)

    def test_failing_step_does_not_raise_out_of_execute(self):
        workflow = self.engine.register_workflow(name="wf", steps=[self._failing_step("bad")])

        self.engine.execute(workflow.id)  # must not raise

    def test_failing_step_stops_remaining_steps(self):
        calls = []

        def tracking_action(ctx):
            calls.append("never")
            return ctx

        workflow = self.engine.register_workflow(
            name="wf",
            steps=[
                self._failing_step("bad"),
                WorkflowStep(name="never-runs", action=tracking_action),
            ],
        )

        self.engine.execute(workflow.id)

        self.assertEqual(calls, [])

    def test_failing_step_publishes_workflow_failed_with_step_details(self):
        workflow = self.engine.register_workflow(
            name="wf", steps=[self._step("ok", "a", 1), self._failing_step("bad")]
        )

        self.engine.execute(workflow.id)

        failed = self._events_of(EventType.WORKFLOW_FAILED)
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0].payload["step_name"], "bad")
        self.assertEqual(failed[0].payload["step_index"], 1)
        self.assertIn("boom", failed[0].payload["error"])

    def test_failing_step_does_not_publish_workflow_completed(self):
        workflow = self.engine.register_workflow(name="wf", steps=[self._failing_step("bad")])

        self.engine.execute(workflow.id)

        self.assertEqual(len(self._events_of(EventType.WORKFLOW_COMPLETED)), 0)

    def test_step_before_failure_still_publishes_step_completed(self):
        workflow = self.engine.register_workflow(
            name="wf", steps=[self._step("ok", "a", 1), self._failing_step("bad")]
        )

        self.engine.execute(workflow.id)

        completed = self._events_of(EventType.WORKFLOW_STEP_COMPLETED)
        self.assertEqual(len(completed), 1)
        self.assertEqual(completed[0].payload["step_name"], "ok")

    def test_failing_step_sets_completed_at(self):
        workflow = self.engine.register_workflow(name="wf", steps=[self._failing_step("bad")])

        self.engine.execute(workflow.id)

        self.assertIsNotNone(self.engine.get_workflow(workflow.id).completed_at)

    def test_execute_returns_context_accumulated_before_failure(self):
        workflow = self.engine.register_workflow(
            name="wf", steps=[self._step("ok", "a", 1), self._failing_step("bad")]
        )

        result = self.engine.execute(workflow.id)

        self.assertEqual(result, {"a": 1})


# -- cancel() ---------------------------------------------------------------


class CancelTests(EngineTestCase):
    def test_cancel_pending_workflow_marks_cancelled(self):
        workflow = self.engine.register_workflow(name="wf", steps=[self._step("s", "a", 1)])

        self.engine.cancel(workflow.id)

        self.assertEqual(self.engine.get_workflow(workflow.id).state, WorkflowState.CANCELLED)

    def test_cancel_publishes_workflow_cancelled(self):
        workflow = self.engine.register_workflow(name="my-wf", steps=[self._step("s", "a", 1)])

        self.engine.cancel(workflow.id)

        cancelled = self._events_of(EventType.WORKFLOW_CANCELLED)
        self.assertEqual(len(cancelled), 1)
        self.assertEqual(cancelled[0].payload["workflow_id"], workflow.id)
        self.assertEqual(cancelled[0].payload["name"], "my-wf")

    def test_cancel_sets_completed_at(self):
        workflow = self.engine.register_workflow(name="wf", steps=[self._step("s", "a", 1)])

        self.engine.cancel(workflow.id)

        self.assertIsNotNone(self.engine.get_workflow(workflow.id).completed_at)

    def test_cancel_missing_workflow_raises_not_found(self):
        with self.assertRaises(WorkflowNotFoundError):
            self.engine.cancel("missing")

    def test_cancel_already_completed_workflow_raises(self):
        workflow = self.engine.register_workflow(name="wf", steps=[self._step("s", "a", 1)])
        self.engine.execute(workflow.id)

        with self.assertRaises(WorkflowError):
            self.engine.cancel(workflow.id)

    def test_cancel_already_cancelled_workflow_raises(self):
        workflow = self.engine.register_workflow(name="wf", steps=[self._step("s", "a", 1)])
        self.engine.cancel(workflow.id)

        with self.assertRaises(WorkflowError):
            self.engine.cancel(workflow.id)

    def test_cancel_failed_workflow_raises(self):
        def failing_action(ctx):
            raise ValueError("boom")

        workflow = self.engine.register_workflow(
            name="wf", steps=[WorkflowStep(name="bad", action=failing_action)]
        )
        self.engine.execute(workflow.id)

        with self.assertRaises(WorkflowError):
            self.engine.cancel(workflow.id)

    def test_cancelled_workflow_cannot_be_executed(self):
        workflow = self.engine.register_workflow(name="wf", steps=[self._step("s", "a", 1)])
        self.engine.cancel(workflow.id)

        with self.assertRaises(WorkflowError):
            self.engine.execute(workflow.id)


# -- get_workflow() / status reporting --------------------------------------


class GetWorkflowTests(EngineTestCase):
    def test_get_workflow_returns_current_snapshot(self):
        workflow = self.engine.register_workflow(name="wf", steps=[self._step("s", "a", 1)])

        fetched = self.engine.get_workflow(workflow.id)

        self.assertEqual(fetched.id, workflow.id)
        self.assertEqual(fetched.state, WorkflowState.PENDING)

    def test_get_workflow_reflects_state_after_execution(self):
        workflow = self.engine.register_workflow(name="wf", steps=[self._step("s", "a", 1)])
        self.engine.execute(workflow.id)

        self.assertEqual(self.engine.get_workflow(workflow.id).state, WorkflowState.COMPLETED)

    def test_get_workflow_missing_raises_not_found(self):
        with self.assertRaises(WorkflowNotFoundError):
            self.engine.get_workflow("missing")

    def test_get_workflow_does_not_require_running_engine(self):
        engine = WorkflowEngine(event_bus=self.event_bus)
        workflow = engine.register_workflow(name="wf", steps=[self._step("s", "a", 1)])

        engine.get_workflow(workflow.id)  # must not raise


# -- loose coupling -----------------------------------------------------


class LooseCouplingTests(EngineTestCase):
    def test_engine_module_does_not_import_other_core_services(self):
        import argus.workflow.engine as engine_module

        source = __import__("inspect").getsource(engine_module)
        for forbidden in ("argus.knowledge", "argus.memory", "argus.scheduler", "argus.intent"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
