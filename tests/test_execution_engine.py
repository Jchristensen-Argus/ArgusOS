"""Unit tests for argus.execution_engine.engine.ExecutionEngine."""

import dataclasses
import logging
import unittest

from argus.capability import CapabilityRegistry, ICapabilityRegistry
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


def _engine(capability_registry=None) -> ExecutionEngine:
    return ExecutionEngine(capability_registry=capability_registry or _capability_registry())


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

    def test_constructor_requires_capability_registry(self):
        # Package 033: "Modify constructor only... Accept:
        # CapabilityRegistry" - capability_registry is now a required
        # constructor argument, unlike Package 032's own fully empty
        # constructor.
        with self.assertRaises(TypeError):
            ExecutionEngine()  # type: ignore[call-arg]


# -- constructor injection (Package 033) ---------------------------------


class ConstructorInjectionTests(unittest.TestCase):
    def test_capability_registry_is_stored(self):
        registry = _capability_registry()
        engine = ExecutionEngine(capability_registry=registry)
        self.assertIs(engine._capability_registry, registry)

    def test_accepts_any_icapabilityregistry_implementation(self):
        registry = _capability_registry()
        engine = ExecutionEngine(capability_registry=registry)
        self.assertIsInstance(engine, ExecutionEngine)
        self.assertIsInstance(registry, ICapabilityRegistry)

    def test_capability_registry_is_never_called_by_execute(self):
        # "No dispatch. No execution. No lookup. No behavior changes."
        # A registry whose every method raises still lets execute()
        # succeed, since execute() never calls any of them.
        class _ExplodingRegistry:
            def __getattr__(self, name):
                raise AssertionError(
                    f"ExecutionEngine.execute() must never call "
                    f"CapabilityRegistry.{name}() in Package 033."
                )

        engine = ExecutionEngine(capability_registry=_ExplodingRegistry())
        result = engine.execute(_plan(tasks=[Task(name="A")]))
        self.assertEqual(result.status, ExecutionStatus.COMPLETED)


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
    def test_engine_holds_exactly_state_and_capability_registry(self):
        # As of Package 033, ExecutionEngine holds one constructor-
        # injected collaborator (capability_registry) - but execute()
        # itself still calls into nothing, so the only failure mode
        # remains an invalid Plan reference, covered by
        # InvalidPlanTests above; see ConstructorInjectionTests for
        # confirmation execute() never touches capability_registry.
        registry = _capability_registry()
        engine = ExecutionEngine(capability_registry=registry)
        self.assertEqual(
            vars(engine),
            {"_capability_registry": registry, "_state": LifecycleState.CREATED},
        )


if __name__ == "__main__":
    unittest.main()
