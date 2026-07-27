"""Unit tests for argus.task.builder.TaskBuilder."""

import unittest

from argus.task import (
    ITaskBuilder,
    InvalidTaskError,
    Task,
    TaskBuilder,
    TaskStatus,
)
from argus.task_relationship import RelationshipBuilder, TaskRelationship


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


class WithRelationshipTests(unittest.TestCase):
    def test_with_relationship_returns_self_for_chaining(self):
        builder = TaskBuilder()
        result = builder.with_relationship(TaskRelationship())
        self.assertIs(result, builder)

    def test_with_relationship_on_empty_builder_produces_single_relationship(self):
        relationship = TaskRelationship()
        task = TaskBuilder().with_relationship(relationship).build()
        self.assertEqual(task.relationships, (relationship,))

    def test_with_relationship_accumulates_preserving_insertion_order(self):
        r1, r2, r3 = TaskRelationship(), TaskRelationship(), TaskRelationship()
        task = (
            TaskBuilder()
            .with_relationship(r1)
            .with_relationship(r2)
            .with_relationship(r3)
            .build()
        )
        self.assertEqual(task.relationships, (r1, r2, r3))

    def test_with_relationship_rejects_non_taskrelationship(self):
        with self.assertRaises(InvalidTaskError):
            TaskBuilder().with_relationship("not a relationship")

    def test_with_relationship_rejects_none(self):
        with self.assertRaises(InvalidTaskError):
            TaskBuilder().with_relationship(None)

    def test_with_relationship_rejects_duplicate_relationship_id_same_object(self):
        relationship = TaskRelationship()
        builder = TaskBuilder().with_relationship(relationship)
        with self.assertRaises(InvalidTaskError):
            builder.with_relationship(relationship)

    def test_with_relationship_rejects_duplicate_relationship_id_different_object(self):
        relationship = TaskRelationship()
        duplicate = TaskRelationship(relationship_id=relationship.relationship_id)
        builder = TaskBuilder().with_relationship(relationship)
        with self.assertRaises(InvalidTaskError):
            builder.with_relationship(duplicate)


class WithRelationshipsTests(unittest.TestCase):
    def test_with_relationships_returns_self_for_chaining(self):
        builder = TaskBuilder()
        result = builder.with_relationships([TaskRelationship()])
        self.assertIs(result, builder)

    def test_with_relationships_adds_multiple_in_order(self):
        r1, r2 = TaskRelationship(), TaskRelationship()
        task = TaskBuilder().with_relationships([r1, r2]).build()
        self.assertEqual(task.relationships, (r1, r2))

    def test_with_relationships_combines_with_prior_with_relationship_calls(self):
        r1, r2, r3 = TaskRelationship(), TaskRelationship(), TaskRelationship()
        task = (
            TaskBuilder().with_relationship(r1).with_relationships([r2, r3]).build()
        )
        self.assertEqual(task.relationships, (r1, r2, r3))

    def test_with_relationships_accepts_tuple(self):
        r1, r2 = TaskRelationship(), TaskRelationship()
        task = TaskBuilder().with_relationships((r1, r2)).build()
        self.assertEqual(task.relationships, (r1, r2))

    def test_with_relationships_rejects_non_list_or_tuple(self):
        with self.assertRaises(InvalidTaskError):
            TaskBuilder().with_relationships("not a list")

    def test_with_relationships_rejects_duplicate_within_the_batch(self):
        r1 = TaskRelationship()
        duplicate = TaskRelationship(relationship_id=r1.relationship_id)
        with self.assertRaises(InvalidTaskError):
            TaskBuilder().with_relationships([r1, duplicate])

    def test_with_relationships_rejects_duplicate_against_prior_with_relationship_call(self):
        r1 = TaskRelationship()
        duplicate = TaskRelationship(relationship_id=r1.relationship_id)
        builder = TaskBuilder().with_relationship(r1)
        with self.assertRaises(InvalidTaskError):
            builder.with_relationships([duplicate])


class ClearRelationshipsTests(unittest.TestCase):
    def test_clear_relationships_returns_self_for_chaining(self):
        builder = TaskBuilder()
        result = builder.clear_relationships()
        self.assertIs(result, builder)

    def test_clear_relationships_empties_previously_added_relationships(self):
        task = (
            TaskBuilder()
            .with_relationship(TaskRelationship())
            .clear_relationships()
            .build()
        )
        self.assertEqual(task.relationships, ())

    def test_clear_relationships_then_re_add_produces_only_new_relationships(self):
        r1, r2 = TaskRelationship(), TaskRelationship()
        task = (
            TaskBuilder()
            .with_relationship(r1)
            .clear_relationships()
            .with_relationship(r2)
            .build()
        )
        self.assertEqual(task.relationships, (r2,))


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
        relationship = RelationshipBuilder().build()
        task = (
            TaskBuilder()
            .with_name("Send email")
            .with_description("Send the welcome email")
            .with_status(TaskStatus.READY)
            .with_relationship(relationship)
            .with_metadata("plan_id", "p-1")
            .build()
        )
        self.assertEqual(task.name, "Send email")
        self.assertEqual(task.description, "Send the welcome email")
        self.assertEqual(task.status, TaskStatus.READY)
        self.assertEqual(task.relationships, (relationship,))
        self.assertEqual(dict(task.metadata.extra), {"plan_id": "p-1"})


if __name__ == "__main__":
    unittest.main()
