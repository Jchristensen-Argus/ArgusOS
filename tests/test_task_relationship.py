"""Unit tests for argus.task_relationship.relationship.TaskRelationship."""

import copy
import dataclasses
import pickle
import unittest

from argus.task import Task
from argus.task_relationship import (
    RelationshipMetadata,
    RelationshipType,
    TaskRelationship,
)


class DefaultsTests(unittest.TestCase):
    def test_defaults(self):
        relationship = TaskRelationship()
        self.assertTrue(relationship.relationship_id)
        self.assertIsNone(relationship.source_task)
        self.assertIsNone(relationship.target_task)
        self.assertEqual(relationship.relationship_type, RelationshipType.RELATED)
        self.assertIsInstance(relationship.metadata, RelationshipMetadata)

    def test_all_fields_set(self):
        source = Task(name="A")
        target = Task(name="B")
        metadata = RelationshipMetadata(extra={"k": "v"})
        relationship = TaskRelationship(
            relationship_id="fixed-id",
            source_task=source,
            target_task=target,
            relationship_type=RelationshipType.BLOCKS,
            metadata=metadata,
        )
        self.assertEqual(relationship.relationship_id, "fixed-id")
        self.assertIs(relationship.source_task, source)
        self.assertIs(relationship.target_task, target)
        self.assertEqual(relationship.relationship_type, RelationshipType.BLOCKS)
        self.assertIs(relationship.metadata, metadata)

    def test_default_relationship_id_is_unique_per_instance(self):
        a = TaskRelationship()
        b = TaskRelationship()
        self.assertNotEqual(a.relationship_id, b.relationship_id)

    def test_default_metadata_is_a_fresh_instance_per_relationship(self):
        a = TaskRelationship()
        b = TaskRelationship()
        self.assertIsNot(a.metadata, b.metadata)


class NoLogicTests(unittest.TestCase):
    def test_relationship_holds_no_field_beyond_id_source_target_type_metadata(self):
        # "The relationship contains no logic. It is purely
        # descriptive."
        field_names = {f.name for f in dataclasses.fields(TaskRelationship)}
        self.assertEqual(
            field_names,
            {
                "relationship_id",
                "source_task",
                "target_task",
                "relationship_type",
                "metadata",
            },
        )

    def test_relationship_defines_no_public_methods_beyond_dataclass_machinery(self):
        public_methods = [
            name
            for name in vars(TaskRelationship)
            if not name.startswith("_") and callable(getattr(TaskRelationship, name))
        ]
        self.assertEqual(public_methods, [])


class ImmutabilityTests(unittest.TestCase):
    def test_immutability(self):
        relationship = TaskRelationship()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            relationship.relationship_type = RelationshipType.BLOCKS

    def test_source_task_field_cannot_be_reassigned(self):
        relationship = TaskRelationship()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            relationship.source_task = Task()

    def test_target_task_field_cannot_be_reassigned(self):
        relationship = TaskRelationship()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            relationship.target_task = Task()

    def test_metadata_field_cannot_be_reassigned(self):
        relationship = TaskRelationship()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            relationship.metadata = RelationshipMetadata()


class NoInterpretationTests(unittest.TestCase):
    def test_every_relationship_type_member_is_accepted_identically(self):
        # "Do not interpret them. Do not infer behavior." - every
        # RelationshipType member constructs identically; none is
        # rejected or treated specially.
        for relationship_type in RelationshipType:
            relationship = TaskRelationship(relationship_type=relationship_type)
            self.assertEqual(relationship.relationship_type, relationship_type)

    def test_source_and_target_may_be_the_same_task(self):
        # Not rejected - see relationship.py's own "Non-
        # Responsibilities" note.
        task = Task(name="A")
        relationship = TaskRelationship(source_task=task, target_task=task)
        self.assertIs(relationship.source_task, task)
        self.assertIs(relationship.target_task, task)


class InvalidConstructionTests(unittest.TestCase):
    def test_metadata_must_be_a_relationshipmetadata_not_a_bare_mapping(self):
        # TaskRelationship performs no isinstance validation of its
        # own (per relationship.py's own "No Validation Here" note) -
        # a bare dict is accepted at the dataclass level, but does not
        # behave like a RelationshipMetadata (no .extra attribute),
        # which is exactly the "invalid construction" case
        # RelationshipBuilder exists to prevent - see
        # tests/test_relationship_builder.py.
        relationship = TaskRelationship(metadata={"not": "a RelationshipMetadata"})  # type: ignore[arg-type]
        with self.assertRaises(AttributeError):
            _ = relationship.metadata.extra


class SerializationConsistencyTests(unittest.TestCase):
    # Note: both RelationshipMetadata.extra and (via source_task/
    # target_task) any attached Task's own TaskMetadata.extra are
    # wrapped in types.MappingProxyType, which is not picklable/
    # deepcopy-able in Python's standard library - the same inherent
    # limitation documented in tests/test_task.py's own equivalent
    # test class, since Package 029. These tests therefore verify
    # serialization consistency of TaskRelationship's own scalar
    # fields and of RelationshipType/RelationshipMetadata.extra
    # independently, rather than pickling/deepcopying a whole
    # TaskRelationship with metadata (or an attached Task) present.

    def test_relationship_type_value_round_trips_through_the_enum(self):
        for relationship_type in RelationshipType:
            self.assertIs(RelationshipType(relationship_type.value), relationship_type)

    def test_deepcopy_of_scalar_fields_round_trips_equal(self):
        relationship = TaskRelationship(relationship_type=RelationshipType.PRECEDES)
        copied_id = copy.deepcopy(relationship.relationship_id)
        copied_type = copy.deepcopy(relationship.relationship_type)
        self.assertEqual(copied_id, relationship.relationship_id)
        self.assertIs(copied_type, relationship.relationship_type)

    def test_pickle_of_scalar_fields_round_trips_equal(self):
        relationship = TaskRelationship(relationship_type=RelationshipType.FOLLOWS)
        self.assertEqual(
            pickle.loads(pickle.dumps(relationship.relationship_id)),
            relationship.relationship_id,
        )
        self.assertIs(
            pickle.loads(pickle.dumps(relationship.relationship_type)),
            relationship.relationship_type,
        )

    def test_metadata_extra_survives_a_plain_dict_round_trip(self):
        relationship = TaskRelationship(
            metadata=RelationshipMetadata(extra={"reason": "manual", "n": 3})
        )
        plain = dict(relationship.metadata.extra)
        rebuilt = RelationshipMetadata(extra=plain)
        self.assertEqual(dict(rebuilt.extra), dict(relationship.metadata.extra))

    def test_relationship_id_is_a_plain_string_suitable_for_json(self):
        relationship = TaskRelationship()
        self.assertIsInstance(relationship.relationship_id, str)


class EqualityTests(unittest.TestCase):
    def test_equality_when_all_fields_match(self):
        metadata = RelationshipMetadata()
        a = TaskRelationship(
            relationship_id="r1",
            relationship_type=RelationshipType.RELATED,
            metadata=metadata,
        )
        b = TaskRelationship(
            relationship_id="r1",
            relationship_type=RelationshipType.RELATED,
            metadata=metadata,
        )
        self.assertEqual(a, b)

    def test_not_equal_when_relationship_id_differs(self):
        metadata = RelationshipMetadata()
        a = TaskRelationship(relationship_id="r1", metadata=metadata)
        b = TaskRelationship(relationship_id="r2", metadata=metadata)
        self.assertNotEqual(a, b)

    def test_not_equal_when_relationship_type_differs(self):
        metadata = RelationshipMetadata()
        a = TaskRelationship(
            relationship_id="r1", relationship_type=RelationshipType.PRECEDES, metadata=metadata
        )
        b = TaskRelationship(
            relationship_id="r1", relationship_type=RelationshipType.FOLLOWS, metadata=metadata
        )
        self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main()
