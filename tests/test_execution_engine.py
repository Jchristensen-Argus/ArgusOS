"""Unit tests for argus.execution_engine.engine.ExecutionEngine."""

import dataclasses
import logging
import unittest

from argus.capability import Capability, CapabilityRegistry, ICapabilityRegistry
from argus.capability_context import CapabilityContext
from argus.capability_executor import (
    CapabilityExecutionStatus,
    CapabilityExecutor,
    ICapabilityExecutor,
)
from argus.events import InMemoryEventBus
from argus.execution_engine import (
    ExecutionEngine,
    ExecutionError,
    ExecutionResult,
    ExecutionStatus,
    IExecutionEngine,
    InvalidPlanReferenceError,
)
from argus.intent import Intent, IntentType
from argus.lifecycle import IService
from argus.lifecycle.lifecycle import LifecycleState
from argus.planner import Plan
from argus.task import Task


def _silent_logger() -> logging.Logger:
    logger = logging.getLogger("test_execution_engine")
    logger.addHandler(logging.NullHandler())
    logger.propagate = False
    return logger


def _capability_registry() -> CapabilityRegistry:
    return CapabilityRegistry(event_bus=InMemoryEventBus(logger=_silent_logger()))


def _capability_executor(capability_registry=None) -> CapabilityExecutor:
    return CapabilityExecutor(capability_registry=capability_registry or _capability_registry())


def _engine(capability_executor=None) -> ExecutionEngine:
    return ExecutionEngine(capability_executor=capability_executor or _capability_executor())


def _plan(**kwargs) -> Plan:
    return Plan(originating_intent=Intent(name=IntentType.UNKNOWN, confidence=0.0), **kwargs)


# -- identity / IService ----------------------------------------------


class ExecutionEngineIdentityTests(unittest.TestCase):
    def test_is_an_iexecutionengine(self):
        self.assertIsInstance(_engine(), IExecutionEngine)

    def test_is_an_iservice(self):
        self.assertIsInstance(_engine(), IService)

    def test_starts_in_created_state(self):
        self.assertEqual(_engine().status(), LifecycleState.CREATED)

    def test_constructor_requires_capability_executor(self):
        # Package 034: "ExecutionEngine now owns: CapabilityExecutor" -
        # capability_executor is now a required constructor argument,
        # replacing Package 033's own capability_registry parameter.
        with self.assertRaises(TypeError):
            ExecutionEngine()  # type: ignore[call-arg]

    def test_constructor_no_longer_accepts_capability_registry(self):
        with self.assertRaises(TypeError):
            ExecutionEngine(capability_registry=_capability_registry())  # type: ignore[call-arg]


# -- constructor injection (Package 034) ---------------------------------


class ConstructorInjectionTests(unittest.TestCase):
    def test_capability_executor_is_stored(self):
        executor = _capability_executor()
        engine = ExecutionEngine(capability_executor=executor)
        self.assertIs(engine._capability_executor, executor)

    def test_accepts_any_icapabilityexecutor_implementation(self):
        executor = _capability_executor()
        engine = ExecutionEngine(capability_executor=executor)
        self.assertIsInstance(engine, ExecutionEngine)
        self.assertIsInstance(executor, ICapabilityExecutor)

    def test_execute_calls_resolve_once_per_task_in_order(self):
        calls = []

        class _RecordingExecutor:
            def resolve(self, context):
                calls.append(context.task)
                from argus.capability_executor import CapabilityExecutionResult

                return CapabilityExecutionResult(task=context.task)

        first = Task(name="A")
        second = Task(name="B")
        engine = ExecutionEngine(capability_executor=_RecordingExecutor())
        engine.execute(_plan(tasks=[first, second]))

        self.assertEqual(calls, [first, second])

    def test_execute_ignores_the_returned_capabilityexecutionresult(self):
        # "Ignore the returned status for now." A CapabilityExecutor
        # whose resolve() always reports NOT_FOUND still lets every
        # Task complete.
        class _AlwaysNotFoundExecutor:
            def resolve(self, context):
                from argus.capability_executor import (
                    CapabilityExecutionResult,
                    CapabilityExecutionStatus,
                )

                return CapabilityExecutionResult(
                    task=context.task, status=CapabilityExecutionStatus.NOT_FOUND
                )

        engine = ExecutionEngine(capability_executor=_AlwaysNotFoundExecutor())
        result = engine.execute(_plan(tasks=[Task(name="A")]))

        self.assertEqual(result.status, ExecutionStatus.COMPLETED)
        self.assertEqual(len(result.completed_tasks), 1)

    def test_empty_plan_never_calls_resolve(self):
        class _ExplodingExecutor:
            def resolve(self, context):
                raise AssertionError("resolve() must not be called for an empty Plan.")

        engine = ExecutionEngine(capability_executor=_ExplodingExecutor())
        result = engine.execute(_plan())

        self.assertEqual(result.status, ExecutionStatus.COMPLETED)

    def test_execute_sends_a_capabilitycontext_not_a_bare_task(self):
        # Package 035: "CapabilityExecutor now accepts
        # CapabilityContext instead of a bare Task."
        received = []

        class _RecordingExecutor:
            def resolve(self, context):
                received.append(context)
                from argus.capability_executor import CapabilityExecutionResult

                return CapabilityExecutionResult(task=context.task)

        task = Task(name="A")
        plan = _plan(tasks=[task])
        engine = ExecutionEngine(capability_executor=_RecordingExecutor())
        engine.execute(plan)

        self.assertEqual(len(received), 1)
        self.assertIsInstance(received[0], CapabilityContext)

    def test_execute_builds_one_context_per_task_carrying_that_task_and_the_plan(self):
        # "ExecutionEngine creates one CapabilityContext for each
        # Task" - carrying task=task, plan=plan.
        received = []

        class _RecordingExecutor:
            def resolve(self, context):
                received.append(context)
                from argus.capability_executor import CapabilityExecutionResult

                return CapabilityExecutionResult(task=context.task)

        first = Task(name="A")
        second = Task(name="B")
        plan = _plan(tasks=[first, second])
        engine = ExecutionEngine(capability_executor=_RecordingExecutor())
        engine.execute(plan)

        self.assertEqual(len(received), 2)
        self.assertIs(received[0].task, first)
        self.assertIs(received[0].plan, plan)
        self.assertIs(received[1].task, second)
        self.assertIs(received[1].plan, plan)

    def test_execute_builds_a_fresh_context_per_task_not_a_shared_one(self):
        received = []

        class _RecordingExecutor:
            def resolve(self, context):
                received.append(context)
                from argus.capability_executor import CapabilityExecutionResult

                return CapabilityExecutionResult(task=context.task)

        plan = _plan(tasks=[Task(name="A"), Task(name="B")])
        engine = ExecutionEngine(capability_executor=_RecordingExecutor())
        engine.execute(plan)

        self.assertNotEqual(received[0].context_id, received[1].context_id)

    def test_execute_leaves_execution_trace_as_none_on_every_context(self):
        # See context.py's own module docstring's "execution_trace Is
        # Always None In Version 1" note - no genuine ExecutionTrace
        # exists yet at the point execute() runs.
        received = []

        class _RecordingExecutor:
            def resolve(self, context):
                received.append(context)
                from argus.capability_executor import CapabilityExecutionResult

                return CapabilityExecutionResult(task=context.task)

        plan = _plan(tasks=[Task(name="A")])
        engine = ExecutionEngine(capability_executor=_RecordingExecutor())
        engine.execute(plan)

        self.assertIsNone(received[0].execution_trace)


# -- lifecycle ----------------------------------------------------------


class ExecutionEngineLifecycleTests(unittest.TestCase):
    def test_initialize_transitions_to_initializing(self):
        engine = _engine()
        engine.initialize()
        self.assertEqual(engine.status(), LifecycleState.INITIALIZING)

    def test_initialize_twice_raises(self):
        engine = _engine()
        engine.initialize()
        with self.assertRaises(ExecutionError):
            engine.initialize()

    def test_start_requires_initializing(self):
        engine = _engine()
        with self.assertRaises(ExecutionError):
            engine.start()

    def test_start_transitions_to_running(self):
        engine = _engine()
        engine.initialize()
        engine.start()
        self.assertEqual(engine.status(), LifecycleState.RUNNING)

    def test_stop_requires_running(self):
        engine = _engine()
        with self.assertRaises(ExecutionError):
            engine.stop()

    def test_stop_transitions_to_stopped(self):
        engine = _engine()
        engine.initialize()
        engine.start()
        engine.stop()
        self.assertEqual(engine.status(), LifecycleState.STOPPED)

    def test_status_reflects_current_state_throughout(self):
        engine = _engine()
        self.assertEqual(engine.status(), LifecycleState.CREATED)
        engine.initialize()
        self.assertEqual(engine.status(), LifecycleState.INITIALIZING)
        engine.start()
        self.assertEqual(engine.status(), LifecycleState.RUNNING)
        engine.stop()
        self.assertEqual(engine.status(), LifecycleState.STOPPED)


# -- execute() is never gated -------------------------------------------


class UngatedBehaviorTests(unittest.TestCase):
    def test_execute_works_in_created_state(self):
        engine = _engine()
        self.assertEqual(engine.status(), LifecycleState.CREATED)
        result = engine.execute(_plan())
        self.assertIsInstance(result, ExecutionResult)

    def test_execute_works_while_running(self):
        engine = _engine()
        engine.initialize()
        engine.start()
        result = engine.execute(_plan())
        self.assertIsInstance(result, ExecutionResult)

    def test_execute_works_after_stopped(self):
        engine = _engine()
        engine.initialize()
        engine.start()
        engine.stop()
        result = engine.execute(_plan())
        self.assertIsInstance(result, ExecutionResult)


# -- valid plan / invalid plan -------------------------------------------


class EmptyPlanTests(unittest.TestCase):
    def test_empty_plan_produces_a_completed_result_with_no_tasks(self):
        engine = _engine()
        plan = _plan()
        self.assertEqual(plan.tasks, ())

        result = engine.execute(plan)

        self.assertIs(result.plan, plan)
        self.assertEqual(result.completed_tasks, ())
        self.assertEqual(result.failed_tasks, ())
        self.assertEqual(result.status, ExecutionStatus.COMPLETED)


class PopulatedPlanTests(unittest.TestCase):
    def test_every_task_is_placed_into_completed_tasks_in_order(self):
        engine = _engine()
        first = Task(name="A")
        second = Task(name="B")
        third = Task(name="C")
        plan = _plan(tasks=[first, second, third])

        result = engine.execute(plan)

        self.assertEqual(result.completed_tasks, (first, second, third))
        self.assertEqual(result.failed_tasks, ())
        self.assertEqual(result.status, ExecutionStatus.COMPLETED)

    def test_tasks_are_placed_unmodified_not_recreated(self):
        engine = _engine()
        task = Task(name="A")
        plan = _plan(tasks=[task])

        result = engine.execute(plan)

        self.assertIs(result.completed_tasks[0], task)

    def test_single_task_plan_produces_a_completed_result(self):
        engine = _engine()
        plan = _plan(tasks=[Task(name="A")])

        result = engine.execute(plan)

        self.assertEqual(len(result.completed_tasks), 1)
        self.assertEqual(result.status, ExecutionStatus.COMPLETED)

    def test_every_task_still_completes_regardless_of_resolution_outcome(self):
        # A mix of resolvable and unresolvable Task names - "Continue
        # placing every Task into completed_tasks (unchanged behavior
        # from Package 032)."
        registry = _capability_registry()
        registry.register(
            Capability(
                name="A",
                description="d",
                intent_types=(IntentType.UNKNOWN,),
                action_kind="workflow",
                workflow_id="w",
            )
        )
        engine = _engine(capability_executor=_capability_executor(registry))
        plan = _plan(tasks=[Task(name="A"), Task(name="Unresolvable")])

        result = engine.execute(plan)

        self.assertEqual(len(result.completed_tasks), 2)
        self.assertEqual(result.status, ExecutionStatus.COMPLETED)


class InvalidPlanTests(unittest.TestCase):
    def test_non_plan_argument_raises(self):
        engine = _engine()
        with self.assertRaises(InvalidPlanReferenceError):
            engine.execute("not a plan")

    def test_none_argument_raises(self):
        engine = _engine()
        with self.assertRaises(InvalidPlanReferenceError):
            engine.execute(None)

    def test_dict_masquerading_as_plan_raises(self):
        engine = _engine()
        with self.assertRaises(InvalidPlanReferenceError):
            engine.execute({"originating_intent": None})


# -- immutable result / no mutation of inputs ----------------------------


class ImmutableResultTests(unittest.TestCase):
    def test_result_cannot_be_mutated(self):
        engine = _engine()
        result = engine.execute(_plan())
        with self.assertRaises(dataclasses.FrozenInstanceError):
            result.status = ExecutionStatus.FAILED

    def test_plan_is_never_mutated(self):
        engine = _engine()
        plan = _plan(tasks=[Task(name="A")])
        before = dataclasses.replace(plan)
        engine.execute(plan)
        self.assertEqual(plan, before)

    def test_multiple_executions_of_the_same_plan_produce_independent_results(self):
        engine = _engine()
        plan = _plan(tasks=[Task(name="A")])
        first = engine.execute(plan)
        second = engine.execute(plan)
        self.assertNotEqual(first.execution_id, second.execution_id)
        self.assertEqual(first.completed_tasks, second.completed_tasks)


# -- dependency failures (execute() itself has no dependency to fail on) -


class NoDependencyToFailTests(unittest.TestCase):
    def test_engine_holds_exactly_state_and_capability_executor(self):
        # As of Package 034, ExecutionEngine holds one constructor-
        # injected collaborator (capability_executor), genuinely
        # called once per Task - see ConstructorInjectionTests above
        # for confirmation of exactly how it is called.
        executor = _capability_executor()
        engine = ExecutionEngine(capability_executor=executor)
        self.assertEqual(
            vars(engine),
            {"_capability_executor": executor, "_state": LifecycleState.CREATED},
        )


if __name__ == "__main__":
    unittest.main()
