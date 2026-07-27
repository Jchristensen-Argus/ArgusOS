"""Unit tests for argus.task.builder.TaskBuilder."""

import unittest

from argus.task import (
    ITaskBuilder,
    InvalidTaskError,
    Task,
    TaskBuilder,
    TaskStatus,
)


class IdentityTests(unittest.TestCase):
    def test_is_an_itaskbuilder(self):
        self.assertIsInstance(TaskBuilder(), ITaskBuilder)

    def test_starts_with_default_values(self):
        task = TaskBuilder().build()
        self.assertEqual(task.name, "")
        self.assertEqual(task.description, "")
        self.assertEqual(task.status, TaskStatus.PENDING)

    def test_constructor_takes_no_arguments(self):
        builder = TaskBuilder()
        self.assertIsInstance(builder, TaskBuilder)


class WithNameTests(unittest.TestCase):
    def test_with_name_returns_self_for_chaining(self):
        builder = TaskBuilder()
        result = builder.with_name("A")
        self.assertIs(result, builder)

    def test_with_name_is_overwritten_not_accumulated(self):
        task = TaskBuilder().with_name("A").with_name("B").build()
        self.assertEqual(task.name, "B")

    def test_with_name_rejects_empty_string(self):
        with self.assertRaises(InvalidTaskError):
            TaskBuilder().with_name("")

    def test_with_name_rejects_non_string(self):
        with self.assertRaises(InvalidTaskError):
            TaskBuilder().with_name(123)

    def test_with_name_rejects_none(self):
        with self.assertRaises(InvalidTaskError):
            TaskBuilder().with_name(None)


class WithDescriptionTests(unittest.TestCase):
    def test_with_description_returns_self_for_chaining(self):
        builder = TaskBuilder()
        result = builder.with_description("desc")
        self.assertIs(result, builder)

    def test_with_description_is_overwritten_not_accumulated(self):
        task = TaskBuilder().with_description("A").with_description("B").build()
        self.assertEqual(task.description, "B")

    def test_with_description_accepts_empty_string(self):
        task = TaskBuilder().with_name("x").with_description("").build()
        self.assertEqual(task.description, "")

    def test_with_description_rejects_non_string(self):
        with self.assertRaises(InvalidTaskError):
            TaskBuilder().with_description(123)

    def test_with_description_rejects_none(self):
        with self.assertRaises(InvalidTaskError):
            TaskBuilder().with_description(None)


class WithStatusTests(unittest.TestCase):
    def test_with_status_returns_self_for_chaining(self):
        builder = TaskBuilder()
        result = builder.with_status(TaskStatus.READY)
        self.assertIs(result, builder)

    def test_with_status_is_overwritten_not_accumulated(self):
        task = (
            TaskBuilder()
            .with_status(TaskStatus.READY)
            .with_status(TaskStatus.COMPLETED)
            .build()
        )
        self.assertEqual(task.status, TaskStatus.COMPLETED)

    def test_with_status_accepts_every_enum_member(self):
        for status in TaskStatus:
            task = TaskBuilder().with_status(status).build()
            self.assertEqual(task.status, status)

    def test_with_status_rejects_non_taskstatus(self):
        with self.assertRaises(InvalidTaskError):
            TaskBuilder().with_status("ready")

    def test_with_status_rejects_none(self):
        with self.assertRaises(InvalidTaskError):
            TaskBuilder().with_status(None)


class WithMetadataTests(unittest.TestCase):
    def test_with_metadata_returns_self_for_chaining(self):
        builder = TaskBuilder()
        result = builder.with_metadata("k", "v")
        self.assertIs(result, builder)

    def test_with_metadata_accumulates_distinct_keys(self):
        task = TaskBuilder().with_metadata("a", 1).with_metadata("b", 2).build()
        self.assertEqual(dict(task.metadata.extra), {"a": 1, "b": 2})

    def test_with_metadata_same_key_last_call_wins(self):
        task = TaskBuilder().with_metadata("a", 1).with_metadata("a", 2).build()
        self.assertEqual(dict(task.metadata.extra), {"a": 2})

    def test_with_metadata_rejects_empty_key(self):
        with self.assertRaises(InvalidTaskError):
            TaskBuilder().with_metadata("", "v")

    def test_with_metadata_rejects_non_string_key(self):
        with self.assertRaises(InvalidTaskError):
            TaskBuilder().with_metadata(123, "v")


class BuildTests(unittest.TestCase):
    def test_build_returns_a_task(self):
        task = TaskBuilder().build()
        self.assertIsInstance(task, Task)

    def test_build_without_with_name_produces_empty_name_not_an_error(self):
        task = TaskBuilder().build()
        self.assertEqual(task.name, "")

    def test_independent_snapshots_earlier_build_not_mutated_by_later_calls(self):
        builder = TaskBuilder().with_name("A")
        first = builder.build()
        builder.with_name("B")
        second = builder.build()
        self.assertEqual(first.name, "A")
        self.assertEqual(second.name, "B")

    def test_different_builders_produce_different_task_ids(self):
        a = TaskBuilder().build()
        b = TaskBuilder().build()
        self.assertNotEqual(a.task_id, b.task_id)

    def test_full_chain_produces_a_fully_populated_task(self):
        task = (
            TaskBuilder()
            .with_name("Send email")
            .with_description("Send the welcome email")
            .with_status(TaskStatus.READY)
            .with_metadata("plan_id", "p-1")
            .build()
        )
        self.assertEqual(task.name, "Send email")
        self.assertEqual(task.description, "Send the welcome email")
        self.assertEqual(task.status, TaskStatus.READY)
        self.assertEqual(dict(task.metadata.extra), {"plan_id": "p-1"})


if __name__ == "__main__":
    unittest.main()
