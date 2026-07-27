"""Unit tests for argus.execution_engine.result.ExecutionResult."""

import copy
import dataclasses
import pickle
import unittest

from argus.execution_engine import ExecutionMetadata, ExecutionResult, ExecutionStatus
from argus.intent import Intent, IntentType
from argus.planner import Plan
from argus.task import Task


def _plan(**kwargs) -> Plan:
    return Plan(originating_intent=Intent(name=IntentType.UNKNOWN, confidence=0.0), **kwargs)


class DefaultsTests(unittest.TestCase):
    def test_defaults(self):
        result = ExecutionResult()
        self.assertTrue(result.execution_id)
        self.assertIsNone(result.plan)
        self.assertEqual(result.completed_tasks, ())
        self.assertEqual(result.failed_tasks, ())
        self.assertEqual(result.status, ExecutionStatus.PENDING)
        self.assertIsInstance(result.metadata, ExecutionMetadata)

    def test_all_fields_set(self):
        plan = _plan()
        completed = (Task(name="A"), Task(name="B"))
        failed = (Task(name="C"),)
        metadata = ExecutionMetadata(extra={"k": "v"})
        result = ExecutionResult(
            execution_id="fixed-id",
            plan=plan,
            completed_tasks=completed,
            failed_tasks=failed,
            status=ExecutionStatus.COMPLETED,
            metadata=metadata,
        )
        self.assertEqual(result.execution_id, "fixed-id")
        self.assertIs(result.plan, plan)
        self.assertEqual(result.completed_tasks, completed)
        self.assertEqual(result.failed_tasks, failed)
        self.assertEqual(result.status, ExecutionStatus.COMPLETED)
        self.assertIs(result.metadata, metadata)

    def test_default_execution_id_is_unique_per_instance(self):
        a = ExecutionResult()
        b = ExecutionResult()
        self.assertNotEqual(a.execution_id, b.execution_id)

    def test_default_metadata_is_a_fresh_instance_per_result(self):
        a = ExecutionResult()
        b = ExecutionResult()
        self.assertIsNot(a.metadata, b.metadata)


class NoLogicTests(unittest.TestCase):
    def test_result_holds_no_field_beyond_the_six_documented_fields(self):
        # "It simply establishes the execution lifecycle" - the value
        # object itself contains no logic.
        field_names = {f.name for f in dataclasses.fields(ExecutionResult)}
        self.assertEqual(
            field_names,
            {"execution_id", "plan", "completed_tasks", "failed_tasks", "status", "metadata"},
        )

    def test_result_defines_no_public_methods_beyond_dataclass_machinery(self):
        public_methods = [
            name
            for name in vars(ExecutionResult)
            if not name.startswith("_") and callable(getattr(ExecutionResult, name))
        ]
        self.assertEqual(public_methods, [])


class CompletedAndFailedTasksTests(unittest.TestCase):
    def test_empty_by_default(self):
        result = ExecutionResult()
        self.assertEqual(result.completed_tasks, ())
        self.assertEqual(result.failed_tasks, ())

    def test_a_list_is_wrapped_in_a_tuple(self):
        tasks = [Task(name="A"), Task(name="B")]
        result = ExecutionResult(completed_tasks=tasks)
        self.assertIsInstance(result.completed_tasks, tuple)
        self.assertEqual(result.completed_tasks, tuple(tasks))

    def test_insertion_order_is_preserved(self):
        first = Task(name="A")
        second = Task(name="B")
        third = Task(name="C")
        result = ExecutionResult(completed_tasks=[first, second, third])
        self.assertEqual(result.completed_tasks, (first, second, third))

    def test_duplicates_are_not_rejected(self):
        # Unlike Plan.tasks (030) / Task.relationships (031), this
        # package's own Requirements list for ExecutionResult does
        # not say "no duplicates" - see result.py's own module
        # docstring's "completed_tasks/failed_tasks Hold Task Objects
        # Directly, In Order" note.
        task = Task(name="A")
        result = ExecutionResult(completed_tasks=[task, task])
        self.assertEqual(result.completed_tasks, (task, task))

    def test_completed_and_failed_tasks_are_independent_collections(self):
        completed = Task(name="A")
        failed = Task(name="B")
        result = ExecutionResult(completed_tasks=[completed], failed_tasks=[failed])
        self.assertEqual(result.completed_tasks, (completed,))
        self.assertEqual(result.failed_tasks, (failed,))


class ImmutabilityTests(unittest.TestCase):
    def test_immutability(self):
        result = ExecutionResult()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            result.status = ExecutionStatus.COMPLETED

    def test_plan_field_cannot_be_reassigned(self):
        result = ExecutionResult()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            result.plan = _plan()

    def test_completed_tasks_field_cannot_be_reassigned(self):
        result = ExecutionResult()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            result.completed_tasks = (Task(),)

    def test_failed_tasks_field_cannot_be_reassigned(self):
        result = ExecutionResult()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            result.failed_tasks = (Task(),)

    def test_metadata_field_cannot_be_reassigned(self):
        result = ExecutionResult()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            result.metadata = ExecutionMetadata()

    def test_completed_tasks_tuple_itself_cannot_be_appended_to(self):
        result = ExecutionResult(completed_tasks=[Task(name="A")])
        with self.assertRaises(AttributeError):
            result.completed_tasks.append(Task(name="B"))  # type: ignore[attr-defined]


class InvalidConstructionTests(unittest.TestCase):
    def test_metadata_must_be_an_executionmetadata_not_a_bare_mapping(self):
        # ExecutionResult performs no isinstance validation of its own
        # (per result.py's own "No Validation Here" note) - a bare
        # dict is accepted at the dataclass level, but does not behave
        # like an ExecutionMetadata (no .extra attribute), which is
        # exactly the "invalid construction" case ExecutionResultBuilder
        # exists to prevent - see tests/test_execution_builder.py.
        result = ExecutionResult(metadata={"not": "an ExecutionMetadata"})  # type: ignore[arg-type]
        with self.assertRaises(AttributeError):
            _ = result.metadata.extra


class SerializationConsistencyTests(unittest.TestCase):
    # Note: both ExecutionMetadata.extra and (via plan/completed_tasks/
    # failed_tasks) any attached Plan's/Task's own metadata.extra are
    # wrapped in types.MappingProxyType, which is not picklable/
    # deepcopy-able in Python's standard library - the same inherent
    # limitation documented in tests/test_task.py's and
    # tests/test_task_relationship.py's own equivalent test classes
    # since Packages 029/031. These tests therefore verify
    # serialization consistency of ExecutionResult's own scalar
    # fields and of ExecutionStatus/ExecutionMetadata.extra
    # independently, rather than pickling/deepcopying a whole
    # ExecutionResult with metadata (or an attached Plan) present.

    def test_status_value_round_trips_through_the_enum(self):
        for status in ExecutionStatus:
            self.assertIs(ExecutionStatus(status.value), status)

    def test_deepcopy_of_scalar_fields_round_trips_equal(self):
        result = ExecutionResult(status=ExecutionStatus.COMPLETED)
        copied_id = copy.deepcopy(result.execution_id)
        copied_status = copy.deepcopy(result.status)
        self.assertEqual(copied_id, result.execution_id)
        self.assertIs(copied_status, result.status)

    def test_pickle_of_scalar_fields_round_trips_equal(self):
        result = ExecutionResult(status=ExecutionStatus.COMPLETED)
        self.assertEqual(
            pickle.loads(pickle.dumps(result.execution_id)), result.execution_id
        )
        self.assertIs(
            pickle.loads(pickle.dumps(result.status)), result.status
        )

    def test_metadata_extra_survives_a_plain_dict_round_trip(self):
        result = ExecutionResult(metadata=ExecutionMetadata(extra={"reason": "manual", "n": 3}))
        plain = dict(result.metadata.extra)
        rebuilt = ExecutionMetadata(extra=plain)
        self.assertEqual(dict(rebuilt.extra), dict(result.metadata.extra))

    def test_execution_id_is_a_plain_string_suitable_for_json(self):
        result = ExecutionResult()
        self.assertIsInstance(result.execution_id, str)


class EqualityTests(unittest.TestCase):
    def test_equality_when_all_fields_match(self):
        metadata = ExecutionMetadata()
        a = ExecutionResult(
            execution_id="r1", status=ExecutionStatus.COMPLETED, metadata=metadata
        )
        b = ExecutionResult(
            execution_id="r1", status=ExecutionStatus.COMPLETED, metadata=metadata
        )
        self.assertEqual(a, b)

    def test_not_equal_when_execution_id_differs(self):
        metadata = ExecutionMetadata()
        a = ExecutionResult(execution_id="r1", metadata=metadata)
        b = ExecutionResult(execution_id="r2", metadata=metadata)
        self.assertNotEqual(a, b)

    def test_not_equal_when_status_differs(self):
        metadata = ExecutionMetadata()
        a = ExecutionResult(
            execution_id="r1", status=ExecutionStatus.PENDING, metadata=metadata
        )
        b = ExecutionResult(
            execution_id="r1", status=ExecutionStatus.COMPLETED, metadata=metadata
        )
        self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main()
