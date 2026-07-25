"""Unit tests for argus.runtime.runtime.AgentRuntime."""

import logging
import unittest

from argus.capability import Capability, CapabilityRegistry
from argus.events import EventType, InMemoryEventBus
from argus.intent import Intent, IntentType
from argus.lifecycle import IService, LifecycleState
from argus.planner import Planner
from argus.runtime import (
    AgentRuntime,
    AgentRuntimeError,
    ExecutionNotFoundError,
    ExecutionStatus,
    IAgentRuntime,
    InvalidExecutionError,
    InvalidExecutionStateError,
    StepExecutionError,
)


def _silent_logger() -> logging.Logger:
    logger = logging.getLogger("test_runtime")
    logger.addHandler(logging.NullHandler())
    logger.propagate = False
    return logger


def _intent(**overrides):
    defaults = dict(name=IntentType.QUESTION, confidence=0.9)
    defaults.update(overrides)
    return Intent(**defaults)


class _FakeDispatcher:
    """A minimal stand-in for IIntentDispatcher.dispatch(), giving
    tests full, precise control over per-step results, failures, and
    reentrancy (simulating a pause/cancel requested from within a
    dispatched step's own action) without depending on a real
    WorkflowEngine or Dispatcher."""

    def __init__(self):
        self.calls = []
        self.results_by_step = {}
        self.fail_on_steps = set()
        self.on_dispatch = None  # optional callable(context)

    def dispatch(self, intent, *, context=None):
        context = dict(context or {})
        self.calls.append((intent, context))
        step_id = context.get("step_id")
        if self.on_dispatch is not None:
            self.on_dispatch(context)
        if step_id in self.fail_on_steps:
            raise ValueError(f"synthetic failure for step {step_id!r}")
        return self.results_by_step.get(step_id, {"ok": True, "step_id": step_id})


class RuntimeTestCase(unittest.TestCase):
    def setUp(self):
        self.event_bus = InMemoryEventBus(logger=_silent_logger())
        self.capability_registry = CapabilityRegistry(event_bus=self.event_bus)
        self.planner = Planner(event_bus=self.event_bus, capability_registry=self.capability_registry)
        self.dispatcher = _FakeDispatcher()
        self.runtime = AgentRuntime(
            event_bus=self.event_bus, dispatcher=self.dispatcher, planner=self.planner
        )
        self.received = []
        for event_type in EventType:
            self.event_bus.subscribe(event_type, self.received.append)

    def _validated_plan(self, step_count=1, capability_id="cap-1"):
        self.capability_registry.register(
            Capability(
                name="Answer",
                description="d",
                intent_types=[IntentType.QUESTION],
                action_kind="workflow",
                workflow_id="answer_workflow",
                id=capability_id,
            )
        )
        plan = self.planner.create_plan(_intent())
        for i in range(step_count):
            plan = self.planner.add_step(
                plan.id, description=f"Step {i}", required_capability=capability_id
            )
        return self.planner.validate_plan(plan.id)

    def _start_runtime(self):
        self.runtime.initialize()
        self.runtime.start()


# -- interface / IService adoption -------------------------------------


class RuntimeIdentityTests(unittest.TestCase):
    def _runtime(self):
        bus = InMemoryEventBus(logger=_silent_logger())
        registry = CapabilityRegistry(event_bus=bus)
        planner = Planner(event_bus=bus, capability_registry=registry)
        return AgentRuntime(event_bus=bus, dispatcher=_FakeDispatcher(), planner=planner)

    def test_is_an_iagentruntime(self):
        self.assertIsInstance(self._runtime(), IAgentRuntime)

    def test_is_an_iservice(self):
        # Deliberate: unlike Capability Registry (013), Plugin Manager
        # (014), and Planner (015), AgentRuntime DOES adopt IService -
        # see argus/runtime/interfaces.py's Architectural Note.
        self.assertIsInstance(self._runtime(), IService)

    def test_initial_state_is_created(self):
        self.assertEqual(self._runtime().status(), LifecycleState.CREATED)

    def test_initialize_then_start_reaches_running(self):
        runtime = self._runtime()
        runtime.initialize()
        self.assertEqual(runtime.status(), LifecycleState.INITIALIZING)
        runtime.start()
        self.assertEqual(runtime.status(), LifecycleState.RUNNING)

    def test_stop_reaches_stopped(self):
        runtime = self._runtime()
        runtime.initialize()
        runtime.start()
        runtime.stop()
        self.assertEqual(runtime.status(), LifecycleState.STOPPED)

    def test_start_without_initialize_raises(self):
        with self.assertRaises(AgentRuntimeError):
            self._runtime().start()

    def test_stop_without_start_raises(self):
        with self.assertRaises(AgentRuntimeError):
            self._runtime().stop()

    def test_double_initialize_raises(self):
        runtime = self._runtime()
        runtime.initialize()
        with self.assertRaises(AgentRuntimeError):
            runtime.initialize()


# -- start_execution() ---------------------------------------------------


class StartExecutionGatingTests(RuntimeTestCase):
    def test_rejects_when_runtime_not_running(self):
        plan = self._validated_plan()

        with self.assertRaises(InvalidExecutionStateError):
            self.runtime.start_execution(plan)

    def test_rejects_non_plan(self):
        self._start_runtime()

        with self.assertRaises(InvalidExecutionError):
            self.runtime.start_execution(object())

    def test_rejects_unvalidated_plan(self):
        self._start_runtime()
        plan = self.planner.create_plan(_intent())  # status CREATED, never validated

        with self.assertRaises(InvalidExecutionStateError):
            self.runtime.start_execution(plan)

    def test_rejects_plan_not_registered_with_planner(self):
        from argus.planner import Plan

        self._start_runtime()
        rogue_plan = Plan(originating_intent=_intent())  # never passed through planner

        with self.assertRaises(InvalidExecutionStateError):
            self.runtime.start_execution(rogue_plan)


class StartExecutionSuccessTests(RuntimeTestCase):
    def test_creates_execution_for_plan(self):
        self._start_runtime()
        plan = self._validated_plan()

        execution = self.runtime.start_execution(plan)

        self.assertEqual(execution.plan_id, plan.id)

    def test_single_step_completes(self):
        self._start_runtime()
        plan = self._validated_plan(step_count=1)

        execution = self.runtime.start_execution(plan)

        self.assertEqual(execution.status, ExecutionStatus.COMPLETED)
        self.assertEqual(execution.current_step, 1)
        self.assertIsNotNone(execution.started_at)
        self.assertIsNotNone(execution.completed_at)

    def test_multi_step_dispatches_in_order(self):
        self._start_runtime()
        plan = self._validated_plan(step_count=3)

        execution = self.runtime.start_execution(plan)

        self.assertEqual(execution.status, ExecutionStatus.COMPLETED)
        self.assertEqual(execution.current_step, 3)
        self.assertEqual(len(self.dispatcher.calls), 3)
        dispatched_step_ids = [ctx["step_id"] for _, ctx in self.dispatcher.calls]
        self.assertEqual(dispatched_step_ids, [s.id for s in plan.steps])

    def test_collects_step_results(self):
        self._start_runtime()
        plan = self._validated_plan(step_count=2)
        for step in plan.steps:
            self.dispatcher.results_by_step[step.id] = {"answer": step.id}

        execution = self.runtime.start_execution(plan)

        for step in plan.steps:
            self.assertEqual(execution.results[step.id], {"answer": step.id})

    def test_empty_plan_completes_vacuously(self):
        self._start_runtime()
        plan = self.planner.create_plan(_intent())
        plan = self.planner.validate_plan(plan.id)

        execution = self.runtime.start_execution(plan)

        self.assertEqual(execution.status, ExecutionStatus.COMPLETED)
        self.assertEqual(execution.current_step, 0)
        self.assertEqual(len(self.dispatcher.calls), 0)

    def test_context_includes_required_capability_and_ids(self):
        self._start_runtime()
        plan = self._validated_plan(step_count=1)

        execution = self.runtime.start_execution(plan)

        _, context = self.dispatcher.calls[0]
        self.assertEqual(context["plan_id"], plan.id)
        self.assertEqual(context["execution_id"], execution.id)
        self.assertEqual(context["step_id"], plan.steps[0].id)
        self.assertEqual(context["required_capability"], plan.steps[0].required_capability)

    def test_multiple_executions_of_same_plan_get_distinct_ids(self):
        self._start_runtime()
        plan = self._validated_plan(step_count=1)

        first = self.runtime.start_execution(plan)
        second = self.runtime.start_execution(plan)

        self.assertNotEqual(first.id, second.id)
        self.assertEqual(first.plan_id, second.plan_id)
        self.assertEqual(len(self.runtime.list_executions()), 2)


class StartExecutionFailureTests(RuntimeTestCase):
    def test_step_failure_raises_step_execution_error(self):
        self._start_runtime()
        plan = self._validated_plan(step_count=1)
        self.dispatcher.fail_on_steps.add(plan.steps[0].id)

        with self.assertRaises(StepExecutionError):
            self.runtime.start_execution(plan)

    def test_step_failure_marks_execution_failed(self):
        self._start_runtime()
        plan = self._validated_plan(step_count=1)
        self.dispatcher.fail_on_steps.add(plan.steps[0].id)

        with self.assertRaises(StepExecutionError):
            self.runtime.start_execution(plan)

        execution = self.runtime.list_executions()[0]
        self.assertEqual(execution.status, ExecutionStatus.FAILED)
        self.assertIsNotNone(execution.completed_at)

    def test_stops_immediately_no_further_steps_dispatched(self):
        self._start_runtime()
        plan = self._validated_plan(step_count=3)
        self.dispatcher.fail_on_steps.add(plan.steps[0].id)

        with self.assertRaises(StepExecutionError):
            self.runtime.start_execution(plan)

        self.assertEqual(len(self.dispatcher.calls), 1)

    def test_no_retries(self):
        self._start_runtime()
        plan = self._validated_plan(step_count=1)
        self.dispatcher.fail_on_steps.add(plan.steps[0].id)

        with self.assertRaises(StepExecutionError):
            self.runtime.start_execution(plan)

        self.assertEqual(len(self.dispatcher.calls), 1)


class StartExecutionEventTests(RuntimeTestCase):
    def test_publishes_events_in_order_on_success(self):
        self._start_runtime()
        plan = self._validated_plan(step_count=2)

        self.runtime.start_execution(plan)

        event_types = [e.type for e in self.received]
        expected_prefix = [
            EventType.EXECUTION_CREATED,
            EventType.EXECUTION_STARTED,
            EventType.STEP_STARTED,
            EventType.STEP_COMPLETED,
            EventType.STEP_STARTED,
            EventType.STEP_COMPLETED,
            EventType.EXECUTION_COMPLETED,
        ]
        runtime_events = [e for e in event_types if e in expected_prefix or e == EventType.EXECUTION_FAILED]
        self.assertEqual(runtime_events, expected_prefix)

    def test_publishes_execution_failed_on_step_failure(self):
        self._start_runtime()
        plan = self._validated_plan(step_count=1)
        self.dispatcher.fail_on_steps.add(plan.steps[0].id)

        with self.assertRaises(StepExecutionError):
            self.runtime.start_execution(plan)

        failed_events = [e for e in self.received if e.type == EventType.EXECUTION_FAILED]
        self.assertEqual(len(failed_events), 1)
        completed_events = [e for e in self.received if e.type == EventType.EXECUTION_COMPLETED]
        self.assertEqual(completed_events, [])

    def test_execution_created_payload(self):
        self._start_runtime()
        plan = self._validated_plan(step_count=1)

        execution = self.runtime.start_execution(plan)

        created = [e for e in self.received if e.type == EventType.EXECUTION_CREATED]
        self.assertEqual(len(created), 1)
        self.assertEqual(created[0].payload["execution_id"], execution.id)
        self.assertEqual(created[0].payload["plan_id"], plan.id)


# -- pause_execution() / resume_execution() ------------------------------


class PauseResumeTests(RuntimeTestCase):
    def test_pause_mid_run_stops_before_next_step(self):
        self._start_runtime()
        plan = self._validated_plan(step_count=2)
        captured = {}
        self.event_bus.subscribe(
            EventType.EXECUTION_CREATED, lambda e: captured.setdefault("id", e.payload["execution_id"])
        )

        def on_dispatch(context):
            if context["step_id"] == plan.steps[0].id:
                self.runtime.pause_execution(captured["id"])

        self.dispatcher.on_dispatch = on_dispatch

        execution = self.runtime.start_execution(plan)

        self.assertEqual(execution.status, ExecutionStatus.PAUSED)
        self.assertEqual(execution.current_step, 1)
        self.assertEqual(len(self.dispatcher.calls), 1)

    def test_resume_continues_from_current_step(self):
        self._start_runtime()
        plan = self._validated_plan(step_count=2)
        captured = {}
        self.event_bus.subscribe(
            EventType.EXECUTION_CREATED, lambda e: captured.setdefault("id", e.payload["execution_id"])
        )
        self.dispatcher.on_dispatch = lambda context: (
            self.runtime.pause_execution(captured["id"])
            if context["step_id"] == plan.steps[0].id
            else None
        )

        paused = self.runtime.start_execution(plan)
        self.dispatcher.on_dispatch = None  # let step 2 run normally
        resumed = self.runtime.resume_execution(paused.id)

        self.assertEqual(resumed.status, ExecutionStatus.COMPLETED)
        self.assertEqual(resumed.current_step, 2)
        self.assertEqual(len(self.dispatcher.calls), 2)

    def test_pause_rejects_non_running_execution(self):
        self._start_runtime()
        plan = self._validated_plan(step_count=1)
        execution = self.runtime.start_execution(plan)  # already COMPLETED

        with self.assertRaises(InvalidExecutionStateError):
            self.runtime.pause_execution(execution.id)

    def test_pause_rejects_non_string_id(self):
        with self.assertRaises(InvalidExecutionError):
            self.runtime.pause_execution(123)

    def test_pause_rejects_unknown_id(self):
        with self.assertRaises(ExecutionNotFoundError):
            self.runtime.pause_execution("missing")

    def test_resume_rejects_non_paused_execution(self):
        self._start_runtime()
        plan = self._validated_plan(step_count=1)
        execution = self.runtime.start_execution(plan)  # already COMPLETED

        with self.assertRaises(InvalidExecutionStateError):
            self.runtime.resume_execution(execution.id)

    def test_resume_rejects_unknown_id(self):
        self._start_runtime()

        with self.assertRaises(ExecutionNotFoundError):
            self.runtime.resume_execution("missing")

    def test_resume_rejects_when_runtime_not_running(self):
        self._start_runtime()
        plan = self._validated_plan(step_count=2)
        captured = {}
        self.event_bus.subscribe(
            EventType.EXECUTION_CREATED, lambda e: captured.setdefault("id", e.payload["execution_id"])
        )
        self.dispatcher.on_dispatch = lambda context: self.runtime.pause_execution(captured["id"])
        paused = self.runtime.start_execution(plan)
        self.runtime.stop()

        with self.assertRaises(InvalidExecutionStateError):
            self.runtime.resume_execution(paused.id)


# -- cancel_execution() ---------------------------------------------------


class CancelExecutionTests(RuntimeTestCase):
    def test_cancel_paused_execution(self):
        self._start_runtime()
        plan = self._validated_plan(step_count=2)
        captured = {}
        self.event_bus.subscribe(
            EventType.EXECUTION_CREATED, lambda e: captured.setdefault("id", e.payload["execution_id"])
        )
        self.dispatcher.on_dispatch = lambda context: self.runtime.pause_execution(captured["id"])
        paused = self.runtime.start_execution(plan)

        cancelled = self.runtime.cancel_execution(paused.id)

        self.assertEqual(cancelled.status, ExecutionStatus.CANCELLED)
        self.assertIsNotNone(cancelled.completed_at)

    def test_cancel_rejects_completed_execution(self):
        self._start_runtime()
        plan = self._validated_plan(step_count=1)
        execution = self.runtime.start_execution(plan)

        with self.assertRaises(InvalidExecutionStateError):
            self.runtime.cancel_execution(execution.id)

    def test_cancel_rejects_failed_execution(self):
        self._start_runtime()
        plan = self._validated_plan(step_count=1)
        self.dispatcher.fail_on_steps.add(plan.steps[0].id)
        with self.assertRaises(StepExecutionError):
            self.runtime.start_execution(plan)
        execution = self.runtime.list_executions()[0]

        with self.assertRaises(InvalidExecutionStateError):
            self.runtime.cancel_execution(execution.id)

    def test_cancel_rejects_already_cancelled(self):
        self._start_runtime()
        plan = self._validated_plan(step_count=2)
        captured = {}
        self.event_bus.subscribe(
            EventType.EXECUTION_CREATED, lambda e: captured.setdefault("id", e.payload["execution_id"])
        )
        self.dispatcher.on_dispatch = lambda context: self.runtime.pause_execution(captured["id"])
        paused = self.runtime.start_execution(plan)
        cancelled = self.runtime.cancel_execution(paused.id)

        with self.assertRaises(InvalidExecutionStateError):
            self.runtime.cancel_execution(cancelled.id)

    def test_cancel_rejects_non_string_id(self):
        with self.assertRaises(InvalidExecutionError):
            self.runtime.cancel_execution(123)

    def test_cancel_rejects_unknown_id(self):
        with self.assertRaises(ExecutionNotFoundError):
            self.runtime.cancel_execution("missing")

    def test_cancel_not_gated_on_runtime_state(self):
        # cancel_execution() is a pure registry operation - not
        # affected by the Runtime's own IService lifecycle state,
        # matching pause_execution()'s identical precedent.
        self._start_runtime()
        plan = self._validated_plan(step_count=2)
        captured = {}
        self.event_bus.subscribe(
            EventType.EXECUTION_CREATED, lambda e: captured.setdefault("id", e.payload["execution_id"])
        )
        self.dispatcher.on_dispatch = lambda context: self.runtime.pause_execution(captured["id"])
        paused = self.runtime.start_execution(plan)
        self.runtime.stop()

        cancelled = self.runtime.cancel_execution(paused.id)  # must not raise

        self.assertEqual(cancelled.status, ExecutionStatus.CANCELLED)


# -- get_execution() -------------------------------------------------------


class GetExecutionTests(RuntimeTestCase):
    def test_returns_registered_execution(self):
        self._start_runtime()
        plan = self._validated_plan(step_count=1)
        execution = self.runtime.start_execution(plan)

        self.assertEqual(self.runtime.get_execution(execution.id).id, execution.id)

    def test_rejects_non_string(self):
        with self.assertRaises(InvalidExecutionError):
            self.runtime.get_execution(123)

    def test_rejects_unknown_id(self):
        with self.assertRaises(ExecutionNotFoundError):
            self.runtime.get_execution("missing")


# -- list_executions() ------------------------------------------------------


class ListExecutionsTests(RuntimeTestCase):
    def test_empty_by_default(self):
        self.assertEqual(self.runtime.list_executions(), ())

    def test_returns_all_executions_in_creation_order(self):
        self._start_runtime()
        plan = self._validated_plan(step_count=1)

        first = self.runtime.start_execution(plan)
        second = self.runtime.start_execution(plan)

        self.assertEqual(
            [e.id for e in self.runtime.list_executions()], [first.id, second.id]
        )

    def test_does_not_publish_events(self):
        self._start_runtime()
        plan = self._validated_plan(step_count=1)
        self.runtime.start_execution(plan)
        self.received.clear()

        self.runtime.list_executions()

        self.assertEqual(self.received, [])


if __name__ == "__main__":
    unittest.main()
