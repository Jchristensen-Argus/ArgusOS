"""Unit tests for argus.execution_engine.builder.ExecutionResultBuilder."""

import unittest

from argus.execution_engine import (
    ExecutionResult,
    ExecutionResultBuilder,
    ExecutionStatus,
    IExecutionResultBuilder,
    InvalidExecutionResultError,
)
from argus.intent import Intent, IntentType
from argus.planner import Plan
from argus.task import Task


def _plan(**kwargs) -> Plan:
    return Plan(originating_intent=Intent(name=IntentType.UNKNOWN, confidence=0.0), **kwargs)


class IdentityTests(unittest.TestCase):
    def test_is_an_iexecutionresultbuilder(self):
        self.assertIsInstance(ExecutionResultBuilder(), IExecutionResultBuilder)

    def test_is_not_an_iservice(self):
        from argus.lifecycle import IService

        self.assertNotIsInstance(ExecutionResultBuilder(), IService)

    def test_starts_with_default_values(self):
        result = ExecutionResultBuilder().build()
        self.assertIsNone(result.plan)
        self.assertEqual(result.completed_tasks, ())
        self.assertEqual(result.failed_tasks, ())
        self.assertEqual(result.status, ExecutionStatus.PENDING)

    def test_constructor_takes_no_arguments(self):
        builder = ExecutionResultBuilder()
        self.assertIsInstance(builder, ExecutionResultBuilder)


class WithPlanTests(unittest.TestCase):
    def test_with_plan_returns_self_for_chaining(self):
        builder = ExecutionResultBuilder()
        result = builder.with_plan(_plan())
        self.assertIs(result, builder)

    def test_with_plan_is_overwritten_not_accumulated(self):
        first = _plan()
        second = _plan()
        result = ExecutionResultBuilder().with_plan(first).with_plan(second).build()
        self.assertIs(result.plan, second)

    def test_with_plan_rejects_non_plan(self):
        with self.assertRaises(InvalidExecutionResultError):
            ExecutionResultBuilder().with_plan("not a plan")

    def test_with_plan_rejects_none(self):
        with self.assertRaises(InvalidExecutionResultError):
            ExecutionResultBuilder().with_plan(None)


class WithCompletedTaskTests(unittest.TestCase):
    def test_with_completed_task_returns_self_for_chaining(self):
        builder = ExecutionResultBuilder()
        result = builder.with_completed_task(Task())
        self.assertIs(result, builder)

    def test_with_completed_task_accumulates_in_call_order(self):
        first = Task(name="A")
        second = Task(name="B")
        result = (
            ExecutionResultBuilder()
            .with_completed_task(first)
            .with_completed_task(second)
            .build()
        )
        self.assertEqual(result.completed_tasks, (first, second))

    def test_with_completed_task_rejects_non_task(self):
        with self.assertRaises(InvalidExecutionResultError):
            ExecutionResultBuilder().with_completed_task("not a task")

    def test_with_completed_task_rejects_none(self):
        with self.assertRaises(InvalidExecutionResultError):
            ExecutionResultBuilder().with_completed_task(None)

    def test_with_completed_task_does_not_reject_duplicates(self):
        # Deliberate omission - see builder.py's own module docstring.
        task = Task(name="A")
        result = (
            ExecutionResultBuilder()
            .with_completed_task(task)
            .with_completed_task(task)
            .build()
        )
        self.assertEqual(result.completed_tasks, (task, task))


class WithCompletedTasksTests(unittest.TestCase):
    def test_with_completed_tasks_returns_self_for_chaining(self):
        builder = ExecutionResultBuilder()
        result = builder.with_completed_tasks([Task()])
        self.assertIs(result, builder)

    def test_with_completed_tasks_accumulates_each_item_in_order(self):
        first = Task(name="A")
        second = Task(name="B")
        result = ExecutionResultBuilder().with_completed_tasks([first, second]).build()
        self.assertEqual(result.completed_tasks, (first, second))

    def test_with_completed_tasks_accepts_a_tuple(self):
        first = Task(name="A")
        result = ExecutionResultBuilder().with_completed_tasks((first,)).build()
        self.assertEqual(result.completed_tasks, (first,))

    def test_with_completed_tasks_combines_with_prior_calls(self):
        first = Task(name="A")
        second = Task(name="B")
        result = (
            ExecutionResultBuilder()
            .with_completed_task(first)
            .with_completed_tasks([second])
            .build()
        )
        self.assertEqual(result.completed_tasks, (first, second))

    def test_with_completed_tasks_rejects_a_non_list_non_tuple(self):
        with self.assertRaises(InvalidExecutionResultError):
            ExecutionResultBuilder().with_completed_tasks("not a list")

    def test_with_completed_tasks_rejects_a_list_containing_a_non_task(self):
        with self.assertRaises(InvalidExecutionResultError):
            ExecutionResultBuilder().with_completed_tasks([Task(), "not a task"])


class ClearCompletedTasksTests(unittest.TestCase):
    def test_clear_completed_tasks_returns_self_for_chaining(self):
        builder = ExecutionResultBuilder()
        result = builder.clear_completed_tasks()
        self.assertIs(result, builder)

    def test_clear_completed_tasks_resets_to_empty(self):
        result = (
            ExecutionResultBuilder()
            .with_completed_task(Task())
            .clear_completed_tasks()
            .build()
        )
        self.assertEqual(result.completed_tasks, ())


class WithFailedTaskTests(unittest.TestCase):
    def test_with_failed_task_returns_self_for_chaining(self):
        builder = ExecutionResultBuilder()
        result = builder.with_failed_task(Task())
        self.assertIs(result, builder)

    def test_with_failed_task_accumulates_in_call_order(self):
        first = Task(name="A")
        second = Task(name="B")
        result = (
            ExecutionResultBuilder().with_failed_task(first).with_failed_task(second).build()
        )
        self.assertEqual(result.failed_tasks, (first, second))

    def test_with_failed_task_rejects_non_task(self):
        with self.assertRaises(InvalidExecutionResultError):
            ExecutionResultBuilder().with_failed_task("not a task")

    def test_with_failed_task_rejects_none(self):
        with self.assertRaises(InvalidExecutionResultError):
            ExecutionResultBuilder().with_failed_task(None)

    def test_completed_and_failed_are_independent_accumulators(self):
        completed = Task(name="A")
        failed = Task(name="B")
        result = (
            ExecutionResultBuilder()
            .with_completed_task(completed)
            .with_failed_task(failed)
            .build()
        )
        self.assertEqual(result.completed_tasks, (completed,))
        self.assertEqual(result.failed_tasks, (failed,))


class WithFailedTasksTests(unittest.TestCase):
    def test_with_failed_tasks_returns_self_for_chaining(self):
        builder = ExecutionResultBuilder()
        result = builder.with_failed_tasks([Task()])
        self.assertIs(result, builder)

    def test_with_failed_tasks_accumulates_each_item_in_order(self):
        first = Task(name="A")
        second = Task(name="B")
        result = ExecutionResultBuilder().with_failed_tasks([first, second]).build()
        self.assertEqual(result.failed_tasks, (first, second))

    def test_with_failed_tasks_rejects_a_non_list_non_tuple(self):
        with self.assertRaises(InvalidExecutionResultError):
            ExecutionResultBuilder().with_failed_tasks("not a list")

    def test_with_failed_tasks_rejects_a_list_containing_a_non_task(self):
        with self.assertRaises(InvalidExecutionResultError):
            ExecutionResultBuilder().with_failed_tasks([Task(), "not a task"])


class ClearFailedTasksTests(unittest.TestCase):
    def test_clear_failed_tasks_returns_self_for_chaining(self):
        builder = ExecutionResultBuilder()
        result = builder.clear_failed_tasks()
        self.assertIs(result, builder)

    def test_clear_failed_tasks_resets_to_empty(self):
        result = (
            ExecutionResultBuilder().with_failed_task(Task()).clear_failed_tasks().build()
        )
        self.assertEqual(result.failed_tasks, ())


class WithStatusTests(unittest.TestCase):
    def test_with_status_returns_self_for_chaining(self):
        builder = ExecutionResultBuilder()
        result = builder.with_status(ExecutionStatus.COMPLETED)
        self.assertIs(result, builder)

    def test_with_status_is_overwritten_not_accumulated(self):
        result = (
            ExecutionResultBuilder()
            .with_status(ExecutionStatus.RUNNING)
            .with_status(ExecutionStatus.COMPLETED)
            .build()
        )
        self.assertEqual(result.status, ExecutionStatus.COMPLETED)

    def test_with_status_accepts_every_enum_member(self):
        for status in ExecutionStatus:
            result = ExecutionResultBuilder().with_status(status).build()
            self.assertEqual(result.status, status)

    def test_with_status_rejects_non_executionstatus(self):
        with self.assertRaises(InvalidExecutionResultError):
            ExecutionResultBuilder().with_status("completed")

    def test_with_status_rejects_none(self):
        with self.assertRaises(InvalidExecutionResultError):
            ExecutionResultBuilder().with_status(None)


class WithMetadataTests(unittest.TestCase):
    def test_with_metadata_returns_self_for_chaining(self):
        builder = ExecutionResultBuilder()
        result = builder.with_metadata("k", "v")
        self.assertIs(result, builder)

    def test_with_metadata_accumulates_distinct_keys(self):
        result = (
            ExecutionResultBuilder().with_metadata("a", 1).with_metadata("b", 2).build()
        )
        self.assertEqual(dict(result.metadata.extra), {"a": 1, "b": 2})

    def test_with_metadata_same_key_last_call_wins(self):
        result = (
            ExecutionResultBuilder().with_metadata("a", 1).with_metadata("a", 2).build()
        )
        self.assertEqual(dict(result.metadata.extra), {"a": 2})

    def test_with_metadata_rejects_empty_key(self):
        with self.assertRaises(InvalidExecutionResultError):
            ExecutionResultBuilder().with_metadata("", "v")

    def test_with_metadata_rejects_non_string_key(self):
        with self.assertRaises(InvalidExecutionResultError):
            ExecutionResultBuilder().with_metadata(123, "v")


class BuildTests(unittest.TestCase):
    def test_build_returns_an_executionresult(self):
        result = ExecutionResultBuilder().build()
        self.assertIsInstance(result, ExecutionResult)

    def test_build_without_with_plan_produces_none_not_an_error(self):
        result = ExecutionResultBuilder().build()
        self.assertIsNone(result.plan)

    def test_independent_snapshots_earlier_build_not_mutated_by_later_calls(self):
        first_task = Task(name="A")
        builder = ExecutionResultBuilder().with_completed_task(first_task)
        first = builder.build()
        second_task = Task(name="B")
        builder.with_completed_task(second_task)
        second = builder.build()
        self.assertEqual(first.completed_tasks, (first_task,))
        self.assertEqual(second.completed_tasks, (first_task, second_task))

    def test_different_builders_produce_different_execution_ids(self):
        a = ExecutionResultBuilder().build()
        b = ExecutionResultBuilder().build()
        self.assertNotEqual(a.execution_id, b.execution_id)

    def test_full_chain_produces_a_fully_populated_result(self):
        plan = _plan()
        completed = Task(name="A")
        result = (
            ExecutionResultBuilder()
            .with_plan(plan)
            .with_completed_task(completed)
            .with_status(ExecutionStatus.COMPLETED)
            .with_metadata("reason", "manual")
            .build()
        )
        self.assertIs(result.plan, plan)
        self.assertEqual(result.completed_tasks, (completed,))
        self.assertEqual(result.failed_tasks, ())
        self.assertEqual(result.status, ExecutionStatus.COMPLETED)
        self.assertEqual(dict(result.metadata.extra), {"reason": "manual"})


if __name__ == "__main__":
    unittest.main()
