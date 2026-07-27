"""Unit tests for
argus.capability_context.builder.CapabilityContextBuilder."""

import unittest

from argus.capability_context import (
    CapabilityContextBuilder,
    ICapabilityContextBuilder,
    InvalidCapabilityContextError,
)
from argus.intent import Intent
from argus.planner.plan import Plan
from argus.task import Task
from argus.trace.trace import ExecutionTrace


def _plan(**kwargs) -> Plan:
    defaults = dict(originating_intent=Intent(name="demo_intent", confidence=0.9))
    defaults.update(kwargs)
    return Plan(**defaults)


class IdentityTests(unittest.TestCase):
    def test_is_an_icapabilitycontextbuilder(self):
        self.assertIsInstance(CapabilityContextBuilder(), ICapabilityContextBuilder)

    def test_is_not_an_iservice(self):
        from argus.lifecycle import IService

        self.assertNotIsInstance(CapabilityContextBuilder(), IService)

    def test_starts_with_default_values(self):
        context = CapabilityContextBuilder().build()
        self.assertIsNone(context.task)
        self.assertIsNone(context.plan)
        self.assertIsNone(context.execution_trace)

    def test_constructor_takes_no_arguments(self):
        builder = CapabilityContextBuilder()
        self.assertIsInstance(builder, CapabilityContextBuilder)

    def test_no_with_context_id_method_exists(self):
        # This package's own Responsibilities list ("assign task,
        # assign plan, assign execution_trace, assign metadata, build
        # immutable CapabilityContext") does not name "assign
        # context_id" - matching RelationshipBuilder's (031),
        # ExecutionResultBuilder's (032), and
        # CapabilityExecutionResultBuilder's (034) own shape. See
        # builder.py's own module docstring.
        self.assertFalse(hasattr(CapabilityContextBuilder(), "with_context_id"))


class WithTaskTests(unittest.TestCase):
    def test_with_task_returns_self_for_chaining(self):
        builder = CapabilityContextBuilder()
        result = builder.with_task(Task(name="A"))
        self.assertIs(result, builder)

    def test_with_task_is_overwritten_not_accumulated(self):
        first = Task(name="A")
        second = Task(name="B")
        context = CapabilityContextBuilder().with_task(first).with_task(second).build()
        self.assertIs(context.task, second)

    def test_with_task_rejects_non_task(self):
        with self.assertRaises(InvalidCapabilityContextError):
            CapabilityContextBuilder().with_task("not a task")

    def test_with_task_rejects_none(self):
        with self.assertRaises(InvalidCapabilityContextError):
            CapabilityContextBuilder().with_task(None)


class WithPlanTests(unittest.TestCase):
    def test_with_plan_returns_self_for_chaining(self):
        builder = CapabilityContextBuilder()
        result = builder.with_plan(_plan())
        self.assertIs(result, builder)

    def test_with_plan_is_overwritten_not_accumulated(self):
        first = _plan()
        second = _plan()
        context = CapabilityContextBuilder().with_plan(first).with_plan(second).build()
        self.assertIs(context.plan, second)

    def test_with_plan_rejects_non_plan(self):
        with self.assertRaises(InvalidCapabilityContextError):
            CapabilityContextBuilder().with_plan("not a plan")

    def test_with_plan_rejects_none(self):
        with self.assertRaises(InvalidCapabilityContextError):
            CapabilityContextBuilder().with_plan(None)

    def test_plan_stays_none_when_with_plan_is_never_called(self):
        context = CapabilityContextBuilder().with_task(Task(name="A")).build()
        self.assertIsNone(context.plan)


class WithExecutionTraceTests(unittest.TestCase):
    def test_with_execution_trace_returns_self_for_chaining(self):
        builder = CapabilityContextBuilder()
        result = builder.with_execution_trace(ExecutionTrace())
        self.assertIs(result, builder)

    def test_with_execution_trace_is_overwritten_not_accumulated(self):
        first = ExecutionTrace()
        second = ExecutionTrace()
        context = (
            CapabilityContextBuilder()
            .with_execution_trace(first)
            .with_execution_trace(second)
            .build()
        )
        self.assertIs(context.execution_trace, second)

    def test_with_execution_trace_rejects_non_execution_trace(self):
        with self.assertRaises(InvalidCapabilityContextError):
            CapabilityContextBuilder().with_execution_trace("not a trace")

    def test_with_execution_trace_rejects_none(self):
        with self.assertRaises(InvalidCapabilityContextError):
            CapabilityContextBuilder().with_execution_trace(None)

    def test_execution_trace_stays_none_when_never_called(self):
        # Mirrors ExecutionEngine's own Version 1 call pattern - see
        # context.py's own module docstring's "execution_trace Is
        # Always None In Version 1" note.
        context = CapabilityContextBuilder().with_task(Task(name="A")).build()
        self.assertIsNone(context.execution_trace)


class WithMetadataTests(unittest.TestCase):
    def test_with_metadata_returns_self_for_chaining(self):
        builder = CapabilityContextBuilder()
        result = builder.with_metadata("k", "v")
        self.assertIs(result, builder)

    def test_with_metadata_populates_extra(self):
        context = CapabilityContextBuilder().with_metadata("reason", "manual").build()
        self.assertEqual(context.metadata.extra["reason"], "manual")

    def test_with_metadata_accumulates_distinct_keys(self):
        context = (
            CapabilityContextBuilder().with_metadata("a", 1).with_metadata("b", 2).build()
        )
        self.assertEqual(dict(context.metadata.extra), {"a": 1, "b": 2})

    def test_with_metadata_same_key_overwrites(self):
        context = (
            CapabilityContextBuilder()
            .with_metadata("k", "first")
            .with_metadata("k", "second")
            .build()
        )
        self.assertEqual(context.metadata.extra["k"], "second")


class BuildTests(unittest.TestCase):
    def test_build_with_no_calls_produces_an_empty_context(self):
        context = CapabilityContextBuilder().build()
        self.assertIsNone(context.task)
        self.assertIsNone(context.plan)
        self.assertIsNone(context.execution_trace)

    def test_build_produces_a_fresh_context_id_each_call(self):
        builder = CapabilityContextBuilder().with_task(Task(name="A"))
        first = builder.build()
        second = builder.build()
        self.assertNotEqual(first.context_id, second.context_id)

    def test_build_after_build_does_not_mutate_the_earlier_context(self):
        task_a = Task(name="A")
        task_b = Task(name="B")
        builder = CapabilityContextBuilder().with_task(task_a)
        first = builder.build()
        builder.with_task(task_b)
        second = builder.build()
        self.assertIs(first.task, task_a)
        self.assertIs(second.task, task_b)

    def test_full_chain_produces_the_expected_context(self):
        task = Task(name="A")
        plan = _plan()
        context = (
            CapabilityContextBuilder()
            .with_task(task)
            .with_plan(plan)
            .with_metadata("k", "v")
            .build()
        )
        self.assertIs(context.task, task)
        self.assertIs(context.plan, plan)
        self.assertIsNone(context.execution_trace)
        self.assertEqual(context.metadata.extra["k"], "v")


if __name__ == "__main__":
    unittest.main()
