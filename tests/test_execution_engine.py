"""Unit tests for argus.execution_engine.engine.ExecutionEngine."""

import dataclasses
import unittest

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


def _plan(**kwargs) -> Plan:
    return Plan(originating_intent=Intent(name=IntentType.UNKNOWN, confidence=0.0), **kwargs)


# -- identity / IService ----------------------------------------------


class ExecutionEngineIdentityTests(unittest.TestCase):
    def test_is_an_iexecutionengine(self):
        self.assertIsInstance(ExecutionEngine(), IExecutionEngine)

    def test_is_an_iservice(self):
        self.assertIsInstance(ExecutionEngine(), IService)

    def test_starts_in_created_state(self):
        self.assertEqual(ExecutionEngine().status(), LifecycleState.CREATED)

    def test_constructor_takes_no_arguments(self):
        # "ExecutionEngine may depend only on Plan" - a per-call
        # argument, never a constructor dependency.
        engine = ExecutionEngine()
        self.assertIsInstance(engine, ExecutionEngine)


# -- lifecycle ----------------------------------------------------------


class ExecutionEngineLifecycleTests(unittest.TestCase):
    def test_initialize_transitions_to_initializing(self):
        engine = ExecutionEngine()
        engine.initialize()
        self.assertEqual(engine.status(), LifecycleState.INITIALIZING)

    def test_initialize_twice_raises(self):
        engine = ExecutionEngine()
        engine.initialize()
        with self.assertRaises(ExecutionError):
            engine.initialize()

    def test_start_requires_initializing(self):
        engine = ExecutionEngine()
        with self.assertRaises(ExecutionError):
            engine.start()

    def test_start_transitions_to_running(self):
        engine = ExecutionEngine()
        engine.initialize()
        engine.start()
        self.assertEqual(engine.status(), LifecycleState.RUNNING)

    def test_stop_requires_running(self):
        engine = ExecutionEngine()
        with self.assertRaises(ExecutionError):
            engine.stop()

    def test_stop_transitions_to_stopped(self):
        engine = ExecutionEngine()
        engine.initialize()
        engine.start()
        engine.stop()
        self.assertEqual(engine.status(), LifecycleState.STOPPED)

    def test_status_reflects_current_state_throughout(self):
        engine = ExecutionEngine()
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
        engine = ExecutionEngine()
        self.assertEqual(engine.status(), LifecycleState.CREATED)
        result = engine.execute(_plan())
        self.assertIsInstance(result, ExecutionResult)

    def test_execute_works_while_running(self):
        engine = ExecutionEngine()
        engine.initialize()
        engine.start()
        result = engine.execute(_plan())
        self.assertIsInstance(result, ExecutionResult)

    def test_execute_works_after_stopped(self):
        engine = ExecutionEngine()
        engine.initialize()
        engine.start()
        engine.stop()
        result = engine.execute(_plan())
        self.assertIsInstance(result, ExecutionResult)


# -- valid plan / invalid plan -------------------------------------------


class EmptyPlanTests(unittest.TestCase):
    def test_empty_plan_produces_a_completed_result_with_no_tasks(self):
        engine = ExecutionEngine()
        plan = _plan()
        self.assertEqual(plan.tasks, ())

        result = engine.execute(plan)

        self.assertIs(result.plan, plan)
        self.assertEqual(result.completed_tasks, ())
        self.assertEqual(result.failed_tasks, ())
        self.assertEqual(result.status, ExecutionStatus.COMPLETED)


class PopulatedPlanTests(unittest.TestCase):
    def test_every_task_is_placed_into_completed_tasks_in_order(self):
        engine = ExecutionEngine()
        first = Task(name="A")
        second = Task(name="B")
        third = Task(name="C")
        plan = _plan(tasks=[first, second, third])

        result = engine.execute(plan)

        self.assertEqual(result.completed_tasks, (first, second, third))
        self.assertEqual(result.failed_tasks, ())
        self.assertEqual(result.status, ExecutionStatus.COMPLETED)

    def test_tasks_are_placed_unmodified_not_recreated(self):
        engine = ExecutionEngine()
        task = Task(name="A")
        plan = _plan(tasks=[task])

        result = engine.execute(plan)

        self.assertIs(result.completed_tasks[0], task)

    def test_single_task_plan_produces_a_completed_result(self):
        engine = ExecutionEngine()
        plan = _plan(tasks=[Task(name="A")])

        result = engine.execute(plan)

        self.assertEqual(len(result.completed_tasks), 1)
        self.assertEqual(result.status, ExecutionStatus.COMPLETED)


class InvalidPlanTests(unittest.TestCase):
    def test_non_plan_argument_raises(self):
        engine = ExecutionEngine()
        with self.assertRaises(InvalidPlanReferenceError):
            engine.execute("not a plan")

    def test_none_argument_raises(self):
        engine = ExecutionEngine()
        with self.assertRaises(InvalidPlanReferenceError):
            engine.execute(None)

    def test_dict_masquerading_as_plan_raises(self):
        engine = ExecutionEngine()
        with self.assertRaises(InvalidPlanReferenceError):
            engine.execute({"originating_intent": None})


# -- immutable result / no mutation of inputs ----------------------------


class ImmutableResultTests(unittest.TestCase):
    def test_result_cannot_be_mutated(self):
        engine = ExecutionEngine()
        result = engine.execute(_plan())
        with self.assertRaises(dataclasses.FrozenInstanceError):
            result.status = ExecutionStatus.FAILED

    def test_plan_is_never_mutated(self):
        engine = ExecutionEngine()
        plan = _plan(tasks=[Task(name="A")])
        before = dataclasses.replace(plan)
        engine.execute(plan)
        self.assertEqual(plan, before)

    def test_multiple_executions_of_the_same_plan_produce_independent_results(self):
        engine = ExecutionEngine()
        plan = _plan(tasks=[Task(name="A")])
        first = engine.execute(plan)
        second = engine.execute(plan)
        self.assertNotEqual(first.execution_id, second.execution_id)
        self.assertEqual(first.completed_tasks, second.completed_tasks)


# -- dependency failures (this engine has no dependency to fail on) ------


class NoDependencyToFailTests(unittest.TestCase):
    def test_engine_holds_no_collaborator_reference(self):
        # ExecutionEngine may depend only on Plan - there is no
        # constructor-injected collaborator whose failure could ever
        # propagate through execute(); the only failure mode is an
        # invalid Plan reference, covered by InvalidPlanTests above.
        engine = ExecutionEngine()
        self.assertEqual(vars(engine), {"_state": LifecycleState.CREATED})


if __name__ == "__main__":
    unittest.main()
