"""Unit tests for argus.task_relationship.builder.RelationshipBuilder."""

import unittest

from argus.task import Task
from argus.task_relationship import (
    IRelationshipBuilder,
    InvalidTaskRelationshipError,
    RelationshipBuilder,
    RelationshipType,
    TaskRelationship,
)


class IdentityTests(unittest.TestCase):
    def test_is_an_irelationshipbuilder(self):
        self.assertIsInstance(RelationshipBuilder(), IRelationshipBuilder)

    def test_is_not_an_iservice(self):
        from argus.lifecycle import IService

        self.assertNotIsInstance(RelationshipBuilder(), IService)

    def test_starts_with_default_values(self):
        relationship = RelationshipBuilder().build()
        self.assertIsNone(relationship.source_task)
        self.assertIsNone(relationship.target_task)
        self.assertEqual(relationship.relationship_type, RelationshipType.RELATED)

    def test_constructor_takes_no_arguments(self):
        builder = RelationshipBuilder()
        self.assertIsInstance(builder, RelationshipBuilder)


class WithSourceTaskTests(unittest.TestCase):
    def test_with_source_task_returns_self_for_chaining(self):
        builder = RelationshipBuilder()
        result = builder.with_source_task(Task())
        self.assertIs(result, builder)

    def test_with_source_task_is_overwritten_not_accumulated(self):
        first = Task(name="A")
        second = Task(name="B")
        relationship = (
            RelationshipBuilder().with_source_task(first).with_source_task(second).build()
        )
        self.assertIs(relationship.source_task, second)

    def test_with_source_task_rejects_non_task(self):
        with self.assertRaises(InvalidTaskRelationshipError):
            RelationshipBuilder().with_source_task("not a task")

    def test_with_source_task_rejects_none(self):
        with self.assertRaises(InvalidTaskRelationshipError):
            RelationshipBuilder().with_source_task(None)


class WithTargetTaskTests(unittest.TestCase):
    def test_with_target_task_returns_self_for_chaining(self):
        builder = RelationshipBuilder()
        result = builder.with_target_task(Task())
        self.assertIs(result, builder)

    def test_with_target_task_is_overwritten_not_accumulated(self):
        first = Task(name="A")
        second = Task(name="B")
        relationship = (
            RelationshipBuilder().with_target_task(first).with_target_task(second).build()
        )
        self.assertIs(relationship.target_task, second)

    def test_with_target_task_rejects_non_task(self):
        with self.assertRaises(InvalidTaskRelationshipError):
            RelationshipBuilder().with_target_task("not a task")

    def test_with_target_task_rejects_none(self):
        with self.assertRaises(InvalidTaskRelationshipError):
            RelationshipBuilder().with_target_task(None)

    def test_source_and_target_may_be_set_to_the_same_task(self):
        # Not rejected - "Do not interpret them. Do not infer
        # behavior."
        task = Task(name="A")
        relationship = (
            RelationshipBuilder().with_source_task(task).with_target_task(task).build()
        )
        self.assertIs(relationship.source_task, task)
        self.assertIs(relationship.target_task, task)


class WithTypeTests(unittest.TestCase):
    def test_with_type_returns_self_for_chaining(self):
        builder = RelationshipBuilder()
        result = builder.with_type(RelationshipType.BLOCKS)
        self.assertIs(result, builder)

    def test_with_type_is_overwritten_not_accumulated(self):
        relationship = (
            RelationshipBuilder()
            .with_type(RelationshipType.PRECEDES)
            .with_type(RelationshipType.BLOCKS)
            .build()
        )
        self.assertEqual(relationship.relationship_type, RelationshipType.BLOCKS)

    def test_with_type_accepts_every_enum_member(self):
        for relationship_type in RelationshipType:
            relationship = RelationshipBuilder().with_type(relationship_type).build()
            self.assertEqual(relationship.relationship_type, relationship_type)

    def test_with_type_rejects_non_relationshiptype(self):
        with self.assertRaises(InvalidTaskRelationshipError):
            RelationshipBuilder().with_type("blocks")

    def test_with_type_rejects_none(self):
        with self.assertRaises(InvalidTaskRelationshipError):
            RelationshipBuilder().with_type(None)


class WithMetadataTests(unittest.TestCase):
    def test_with_metadata_returns_self_for_chaining(self):
        builder = RelationshipBuilder()
        result = builder.with_metadata("k", "v")
        self.assertIs(result, builder)

    def test_with_metadata_accumulates_distinct_keys(self):
        relationship = (
            RelationshipBuilder().with_metadata("a", 1).with_metadata("b", 2).build()
        )
        self.assertEqual(dict(relationship.metadata.extra), {"a": 1, "b": 2})

    def test_with_metadata_same_key_last_call_wins(self):
        relationship = (
            RelationshipBuilder().with_metadata("a", 1).with_metadata("a", 2).build()
        )
        self.assertEqual(dict(relationship.metadata.extra), {"a": 2})

    def test_with_metadata_rejects_empty_key(self):
        with self.assertRaises(InvalidTaskRelationshipError):
            RelationshipBuilder().with_metadata("", "v")

    def test_with_metadata_rejects_non_string_key(self):
        with self.assertRaises(InvalidTaskRelationshipError):
            RelationshipBuilder().with_metadata(123, "v")


class BuildTests(unittest.TestCase):
    def test_build_returns_a_taskrelationship(self):
        relationship = RelationshipBuilder().build()
        self.assertIsInstance(relationship, TaskRelationship)

    def test_build_without_with_source_task_produces_none_not_an_error(self):
        relationship = RelationshipBuilder().build()
        self.assertIsNone(relationship.source_task)

    def test_independent_snapshots_earlier_build_not_mutated_by_later_calls(self):
        source = Task(name="A")
        builder = RelationshipBuilder().with_source_task(source)
        first = builder.build()
        target = Task(name="B")
        builder.with_target_task(target)
        second = builder.build()
        self.assertIsNone(first.target_task)
        self.assertIs(second.target_task, target)

    def test_different_builders_produce_different_relationship_ids(self):
        a = RelationshipBuilder().build()
        b = RelationshipBuilder().build()
        self.assertNotEqual(a.relationship_id, b.relationship_id)

    def test_full_chain_produces_a_fully_populated_relationship(self):
        source = Task(name="A")
        target = Task(name="B")
        relationship = (
            RelationshipBuilder()
            .with_source_task(source)
            .with_target_task(target)
            .with_type(RelationshipType.PRECEDES)
            .with_metadata("reason", "manual")
            .build()
        )
        self.assertIs(relationship.source_task, source)
        self.assertIs(relationship.target_task, target)
        self.assertEqual(relationship.relationship_type, RelationshipType.PRECEDES)
        self.assertEqual(dict(relationship.metadata.extra), {"reason": "manual"})


if __name__ == "__main__":
    unittest.main()
