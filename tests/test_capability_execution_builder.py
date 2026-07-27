"""Unit tests for
argus.capability_executor.builder.CapabilityExecutionResultBuilder."""

import unittest

from argus.capability import Capability
from argus.capability_executor import (
    CapabilityExecutionResultBuilder,
    CapabilityExecutionStatus,
    ICapabilityExecutionResultBuilder,
    InvalidCapabilityExecutionResultError,
)
from argus.intent import IntentType
from argus.task import Task


def _capability(**kwargs) -> Capability:
    defaults = dict(
        name="Do Thing",
        description="d",
        intent_types=(IntentType.UNKNOWN,),
        action_kind="workflow",
        workflow_id="w",
    )
    defaults.update(kwargs)
    return Capability(**defaults)


class IdentityTests(unittest.TestCase):
    def test_is_an_icapabilityexecutionresultbuilder(self):
        self.assertIsInstance(
            CapabilityExecutionResultBuilder(), ICapabilityExecutionResultBuilder
        )

    def test_is_not_an_iservice(self):
        from argus.lifecycle import IService

        self.assertNotIsInstance(CapabilityExecutionResultBuilder(), IService)

    def test_starts_with_default_values(self):
        result = CapabilityExecutionResultBuilder().build()
        self.assertIsNone(result.task)
        self.assertIsNone(result.capability)
        self.assertEqual(result.status, CapabilityExecutionStatus.PENDING)

    def test_constructor_takes_no_arguments(self):
        builder = CapabilityExecutionResultBuilder()
        self.assertIsInstance(builder, CapabilityExecutionResultBuilder)

    def test_no_with_execution_id_method_exists(self):
        # Unlike CapabilityBuilder (033), whose own Responsibilities
        # list explicitly names "assign id," this package's own list
        # does not name "assign execution_id" - matching
        # RelationshipBuilder's (031) and ExecutionResultBuilder's
        # (032) own shape. See builder.py's own module docstring.
        self.assertFalse(hasattr(CapabilityExecutionResultBuilder(), "with_execution_id"))


class WithTaskTests(unittest.TestCase):
    def test_with_task_returns_self_for_chaining(self):
        builder = CapabilityExecutionResultBuilder()
        result = builder.with_task(Task(name="A"))
        self.assertIs(result, builder)

    def test_with_task_is_overwritten_not_accumulated(self):
        first = Task(name="A")
        second = Task(name="B")
        result = (
            CapabilityExecutionResultBuilder().with_task(first).with_task(second).build()
        )
        self.assertIs(result.task, second)

    def test_with_task_rejects_non_task(self):
        with self.assertRaises(InvalidCapabilityExecutionResultError):
            CapabilityExecutionResultBuilder().with_task("not a task")

    def test_with_task_rejects_none(self):
        with self.assertRaises(InvalidCapabilityExecutionResultError):
            CapabilityExecutionResultBuilder().with_task(None)


class WithCapabilityTests(unittest.TestCase):
    def test_with_capability_returns_self_for_chaining(self):
        builder = CapabilityExecutionResultBuilder()
        result = builder.with_capability(_capability())
        self.assertIs(result, builder)

    def test_with_capability_is_overwritten_not_accumulated(self):
        first = _capability(name="First")
        second = _capability(name="Second")
        result = (
            CapabilityExecutionResultBuilder()
            .with_capability(first)
            .with_capability(second)
            .build()
        )
        self.assertIs(result.capability, second)

    def test_with_capability_rejects_non_capability(self):
        with self.assertRaises(InvalidCapabilityExecutionResultError):
            CapabilityExecutionResultBuilder().with_capability("not a capability")

    def test_with_capability_rejects_none(self):
        # Mirrors ExecutionResultBuilder.with_plan()'s own identical
        # rule - a CapabilityExecutionResult with capability=None (the
        # NOT_FOUND case) is produced by never calling
        # with_capability() at all, not by calling with_capability(None).
        with self.assertRaises(InvalidCapabilityExecutionResultError):
            CapabilityExecutionResultBuilder().with_capability(None)

    def test_capability_stays_none_when_with_capability_is_never_called(self):
        result = (
            CapabilityExecutionResultBuilder()
            .with_task(Task(name="A"))
            .with_status(CapabilityExecutionStatus.NOT_FOUND)
            .build()
        )
        self.assertIsNone(result.capability)


class WithStatusTests(unittest.TestCase):
    def test_with_status_returns_self_for_chaining(self):
        builder = CapabilityExecutionResultBuilder()
        result = builder.with_status(CapabilityExecutionStatus.COMPLETED)
        self.assertIs(result, builder)

    def test_with_status_is_overwritten_not_accumulated(self):
        result = (
            CapabilityExecutionResultBuilder()
            .with_status(CapabilityExecutionStatus.NOT_FOUND)
            .with_status(CapabilityExecutionStatus.COMPLETED)
            .build()
        )
        self.assertEqual(result.status, CapabilityExecutionStatus.COMPLETED)

    def test_with_status_rejects_non_status(self):
        with self.assertRaises(InvalidCapabilityExecutionResultError):
            CapabilityExecutionResultBuilder().with_status("completed")

    def test_with_status_rejects_none(self):
        with self.assertRaises(InvalidCapabilityExecutionResultError):
            CapabilityExecutionResultBuilder().with_status(None)

    def test_default_status_is_pending(self):
        result = CapabilityExecutionResultBuilder().build()
        self.assertEqual(result.status, CapabilityExecutionStatus.PENDING)


class WithMetadataTests(unittest.TestCase):
    def test_with_metadata_returns_self_for_chaining(self):
        builder = CapabilityExecutionResultBuilder()
        result = builder.with_metadata("k", "v")
        self.assertIs(result, builder)

    def test_with_metadata_populates_extra(self):
        result = CapabilityExecutionResultBuilder().with_metadata("reason", "manual").build()
        self.assertEqual(result.metadata.extra["reason"], "manual")

    def test_with_metadata_accumulates_distinct_keys(self):
        result = (
            CapabilityExecutionResultBuilder()
            .with_metadata("a", 1)
            .with_metadata("b", 2)
            .build()
        )
        self.assertEqual(dict(result.metadata.extra), {"a": 1, "b": 2})

    def test_with_metadata_same_key_overwrites(self):
        result = (
            CapabilityExecutionResultBuilder()
            .with_metadata("k", "first")
            .with_metadata("k", "second")
            .build()
        )
        self.assertEqual(result.metadata.extra["k"], "second")

    def test_with_metadata_rejects_empty_key(self):
        with self.assertRaises(InvalidCapabilityExecutionResultError):
            CapabilityExecutionResultBuilder().with_metadata("", "v")

    def test_with_metadata_rejects_non_string_key(self):
        with self.assertRaises(InvalidCapabilityExecutionResultError):
            CapabilityExecutionResultBuilder().with_metadata(123, "v")


class BuildTests(unittest.TestCase):
    def test_build_with_no_calls_produces_an_empty_result(self):
        result = CapabilityExecutionResultBuilder().build()
        self.assertIsNone(result.task)
        self.assertIsNone(result.capability)
        self.assertEqual(result.status, CapabilityExecutionStatus.PENDING)

    def test_build_produces_a_fresh_execution_id_each_call(self):
        builder = CapabilityExecutionResultBuilder().with_task(Task(name="A"))
        first = builder.build()
        second = builder.build()
        self.assertNotEqual(first.execution_id, second.execution_id)

    def test_build_after_build_does_not_mutate_the_earlier_result(self):
        capability_a = _capability(name="A")
        capability_b = _capability(name="B")
        builder = CapabilityExecutionResultBuilder().with_capability(capability_a)
        first = builder.build()
        builder.with_capability(capability_b)
        second = builder.build()
        self.assertIs(first.capability, capability_a)
        self.assertIs(second.capability, capability_b)

    def test_full_chain_produces_the_expected_result(self):
        task = Task(name="A")
        capability = _capability()
        result = (
            CapabilityExecutionResultBuilder()
            .with_task(task)
            .with_capability(capability)
            .with_status(CapabilityExecutionStatus.COMPLETED)
            .with_metadata("k", "v")
            .build()
        )
        self.assertIs(result.task, task)
        self.assertIs(result.capability, capability)
        self.assertEqual(result.status, CapabilityExecutionStatus.COMPLETED)
        self.assertEqual(result.metadata.extra["k"], "v")


if __name__ == "__main__":
    unittest.main()
