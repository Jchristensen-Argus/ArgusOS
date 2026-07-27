"""Unit tests for argus.task.task.Task."""

import copy
import dataclasses
import pickle
import unittest

from argus.task import Task, TaskMetadata, TaskStatus
from argus.task_relationship import RelationshipBuilder, TaskRelationship


class DefaultsTests(unittest.TestCase):
    def test_defaults(self):
        task = Task()
        self.assertTrue(task.task_id)
        self.assertEqual(task.name, "")
        self.assertEqual(task.description, "")
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertIsInstance(task.metadata, TaskMetadata)

    def test_all_fields_set(self):
        metadata = TaskMetadata(extra={"k": "v"})
        task = Task(
            task_id="fixed-id",
            name="Send email",
            description="Send the welcome email",
            status=TaskStatus.READY,
            metadata=metadata,
        )
        self.assertEqual(task.task_id, "fixed-id")
        self.assertEqual(task.name, "Send email")
        self.assertEqual(task.description, "Send the welcome email")
        self.assertEqual(task.status, TaskStatus.READY)
        self.assertIs(task.metadata, metadata)

    def test_default_task_id_is_unique_per_instance(self):
        a = Task()
        b = Task()
        self.assertNotEqual(a.task_id, b.task_id)

    def test_default_metadata_is_a_fresh_instance_per_task(self):
        a = Task()
        b = Task()
        self.assertIsNot(a.metadata, b.metadata)


class RelationshipsTests(unittest.TestCase):
    # "Extend the Task domain so that Tasks can describe immutable
    # relationships with other Tasks." (Package 031)

    def test_empty_relationships_by_default(self):
        task = Task()
        self.assertEqual(task.relationships, ())

    def test_one_relationship(self):
        relationship = TaskRelationship()
        task = Task(relationships=[relationship])
        self.assertEqual(task.relationships, (relationship,))

    def test_many_relationships_preserve_insertion_order(self):
        r1 = TaskRelationship()
        r2 = TaskRelationship()
        r3 = TaskRelationship()
        task = Task(relationships=[r1, r2, r3])
        self.assertEqual(task.relationships, (r1, r2, r3))

    def test_relationships_is_a_tuple(self):
        relationship = TaskRelationship()
        task = Task(relationships=[relationship])
        self.assertIsInstance(task.relationships, tuple)

    def test_relationships_immutable_from_source_list(self):
        r1 = TaskRelationship()
        source = [r1]
        task = Task(relationships=source)
        source.append(TaskRelationship())
        self.assertEqual(task.relationships, (r1,))

    def test_relationships_tuple_cannot_be_mutated_in_place(self):
        task = Task(relationships=[TaskRelationship()])
        with self.assertRaises(AttributeError):
            task.relationships.append(TaskRelationship())

    def test_relationships_field_cannot_be_reassigned(self):
        task = Task()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            task.relationships = ()

    def test_a_relationship_may_reference_this_task_itself(self):
        # Not rejected at the Task level - see
        # tests/test_task_relationship.py's own equivalent note.
        task = Task(name="A")
        relationship = RelationshipBuilder().with_source_task(task).build()
        populated = Task(name="A", relationships=[relationship])
        self.assertIs(populated.relationships[0].source_task, task)


class NoExecutableLogicTests(unittest.TestCase):
    def test_task_holds_no_field_beyond_identity_description_status_relationships_metadata(self):
        # "The task contains no executable logic. It is purely a
        # value object." Package 031 added `relationships`.
        field_names = {f.name for f in dataclasses.fields(Task)}
        self.assertEqual(
            field_names,
            {"task_id", "name", "description", "status", "relationships", "metadata"},
        )

    def test_task_defines_no_public_methods_beyond_dataclass_machinery(self):
        public_methods = [
            name
            for name in vars(Task)
            if not name.startswith("_") and callable(getattr(Task, name))
        ]
        self.assertEqual(public_methods, [])


class ImmutabilityTests(unittest.TestCase):
    def test_immutability(self):
        task = Task()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            task.name = "other"

    def test_status_field_cannot_be_reassigned(self):
        task = Task()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            task.status = TaskStatus.COMPLETED

    def test_metadata_field_cannot_be_reassigned(self):
        task = Task()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            task.metadata = TaskMetadata()


class InvalidConstructionTests(unittest.TestCase):
    def test_relationships_item_need_not_be_isinstance_checked_here(self):
        # Like every other collection field in this codebase (Plan.steps,
        # Plan.tasks/PlanningSession.tasks), Task performs no
        # isinstance validation of its own items - see the module
        # docstring's "No Validation Here" note. This is exercised
        # directly by TaskBuilder.with_relationship()'s own validation
        # instead - see tests/test_task_builder.py.
        task = Task(relationships=["not a TaskRelationship"])  # type: ignore[list-item]
        self.assertEqual(task.relationships, ("not a TaskRelationship",))

    def test_metadata_must_be_a_taskmetadata_not_a_bare_mapping(self):
        # Task performs no isinstance validation of its own (per
        # task.py's own "No Validation Here" note) - a bare dict is
        # accepted at the dataclass level, but does not behave like a
        # TaskMetadata (no .extra attribute), which is exactly the
        # "invalid construction" case TaskBuilder exists to prevent -
        # see tests/test_task_builder.py.
        task = Task(metadata={"not": "a TaskMetadata"})  # type: ignore[arg-type]
        with self.assertRaises(AttributeError):
            _ = task.metadata.extra


class SerializationConsistencyTests(unittest.TestCase):
    # Note: `TaskMetadata.extra` is wrapped in `types.MappingProxyType`
    # (see metadata.py's own module docstring), and MappingProxyType
    # is not picklable/deepcopy-able in Python's standard library -
    # this is an inherent limitation shared by every metadata class in
    # this codebase (ContextMetadata, PlanningMetadata, ResponseMetadata,
    # TraceMetadata all wrap `extra` the same way), not something
    # specific to Task. These tests therefore verify serialization
    # consistency of Task's own scalar fields and of TaskStatus/
    # TaskMetadata.extra independently, rather than pickling/
    # deepcopying a whole Task with metadata attached.

    def test_status_value_round_trips_through_the_enum(self):
        for status in TaskStatus:
            self.assertIs(TaskStatus(status.value), status)

    def test_deepcopy_of_scalar_fields_round_trips_equal(self):
        task = Task(name="A", description="B", status=TaskStatus.READY)
        copied_name = copy.deepcopy(task.name)
        copied_description = copy.deepcopy(task.description)
        copied_status = copy.deepcopy(task.status)
        self.assertEqual(copied_name, task.name)
        self.assertEqual(copied_description, task.description)
        self.assertIs(copied_status, task.status)

    def test_pickle_of_scalar_fields_round_trips_equal(self):
        task = Task(name="A", description="B", status=TaskStatus.READY)
        self.assertEqual(pickle.loads(pickle.dumps(task.name)), task.name)
        self.assertEqual(pickle.loads(pickle.dumps(task.description)), task.description)
        self.assertIs(pickle.loads(pickle.dumps(task.status)), task.status)

    def test_metadata_extra_survives_a_plain_dict_round_trip(self):
        task = Task(metadata=TaskMetadata(extra={"plan_id": "p-1", "n": 3}))
        plain = dict(task.metadata.extra)
        rebuilt = TaskMetadata(extra=plain)
        self.assertEqual(dict(rebuilt.extra), dict(task.metadata.extra))

    def test_task_id_and_name_are_plain_strings_suitable_for_json(self):
        task = Task(name="A", description="B")
        self.assertIsInstance(task.task_id, str)
        self.assertIsInstance(task.name, str)
        self.assertIsInstance(task.description, str)


class EqualityTests(unittest.TestCase):
    def test_equality_when_all_fields_match(self):
        metadata = TaskMetadata()
        a = Task(task_id="t1", name="A", status=TaskStatus.PENDING, metadata=metadata)
        b = Task(task_id="t1", name="A", status=TaskStatus.PENDING, metadata=metadata)
        self.assertEqual(a, b)

    def test_not_equal_when_task_id_differs(self):
        metadata = TaskMetadata()
        a = Task(task_id="t1", name="A", metadata=metadata)
        b = Task(task_id="t2", name="A", metadata=metadata)
        self.assertNotEqual(a, b)

    def test_not_equal_when_status_differs(self):
        metadata = TaskMetadata()
        a = Task(task_id="t1", name="A", status=TaskStatus.PENDING, metadata=metadata)
        b = Task(task_id="t1", name="A", status=TaskStatus.READY, metadata=metadata)
        self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main()
