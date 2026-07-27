"""Unit tests for
argus.capability_executor.result.CapabilityExecutionResult."""

import copy
import dataclasses
import pickle
import unittest

from argus.capability import Capability
from argus.capability_executor import (
    CapabilityExecutionMetadata,
    CapabilityExecutionResult,
    CapabilityExecutionStatus,
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


class DefaultsTests(unittest.TestCase):
    def test_defaults(self):
        result = CapabilityExecutionResult()
        self.assertTrue(result.execution_id)
        self.assertIsNone(result.task)
        self.assertIsNone(result.capability)
        self.assertEqual(result.status, CapabilityExecutionStatus.PENDING)
        self.assertIsInstance(result.metadata, CapabilityExecutionMetadata)

    def test_all_fields_set(self):
        task = Task(name="A")
        capability = _capability()
        metadata = CapabilityExecutionMetadata(extra={"k": "v"})
        result = CapabilityExecutionResult(
            execution_id="fixed-id",
            task=task,
            capability=capability,
            status=CapabilityExecutionStatus.COMPLETED,
            metadata=metadata,
        )
        self.assertEqual(result.execution_id, "fixed-id")
        self.assertIs(result.task, task)
        self.assertIs(result.capability, capability)
        self.assertEqual(result.status, CapabilityExecutionStatus.COMPLETED)
        self.assertIs(result.metadata, metadata)

    def test_default_execution_id_is_unique_per_instance(self):
        a = CapabilityExecutionResult()
        b = CapabilityExecutionResult()
        self.assertNotEqual(a.execution_id, b.execution_id)

    def test_default_metadata_is_a_fresh_instance_per_result(self):
        a = CapabilityExecutionResult()
        b = CapabilityExecutionResult()
        self.assertIsNot(a.metadata, b.metadata)


class NoLogicTests(unittest.TestCase):
    def test_result_holds_no_field_beyond_the_five_documented_fields(self):
        # "It establishes the execution contract only" - the value
        # object itself contains no logic.
        field_names = {f.name for f in dataclasses.fields(CapabilityExecutionResult)}
        self.assertEqual(
            field_names,
            {"execution_id", "task", "capability", "status", "metadata"},
        )

    def test_result_defines_no_public_methods_beyond_dataclass_machinery(self):
        public_methods = [
            name
            for name in vars(CapabilityExecutionResult)
            if not name.startswith("_") and callable(getattr(CapabilityExecutionResult, name))
        ]
        self.assertEqual(public_methods, [])


class TaskAndCapabilityTests(unittest.TestCase):
    def test_none_by_default(self):
        result = CapabilityExecutionResult()
        self.assertIsNone(result.task)
        self.assertIsNone(result.capability)

    def test_task_holds_the_object_directly_not_a_reference(self):
        task = Task(name="A")
        result = CapabilityExecutionResult(task=task)
        self.assertIs(result.task, task)

    def test_capability_holds_the_object_directly_not_a_reference(self):
        capability = _capability()
        result = CapabilityExecutionResult(capability=capability)
        self.assertIs(result.capability, capability)

    def test_capability_is_none_when_status_is_not_found(self):
        result = CapabilityExecutionResult(
            task=Task(name="A"), status=CapabilityExecutionStatus.NOT_FOUND
        )
        self.assertIsNone(result.capability)


class ImmutabilityTests(unittest.TestCase):
    def test_immutability(self):
        result = CapabilityExecutionResult()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            result.status = CapabilityExecutionStatus.COMPLETED

    def test_task_field_cannot_be_reassigned(self):
        result = CapabilityExecutionResult()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            result.task = Task(name="A")

    def test_capability_field_cannot_be_reassigned(self):
        result = CapabilityExecutionResult()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            result.capability = _capability()

    def test_metadata_field_cannot_be_reassigned(self):
        result = CapabilityExecutionResult()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            result.metadata = CapabilityExecutionMetadata()


class InvalidConstructionTests(unittest.TestCase):
    def test_metadata_must_be_a_capabilityexecutionmetadata_not_a_bare_mapping(self):
        # CapabilityExecutionResult performs no isinstance validation
        # of its own (per result.py's own "No Validation Here" note) -
        # a bare dict is accepted at the dataclass level, but does not
        # behave like a CapabilityExecutionMetadata (no .extra
        # attribute), which is exactly the "invalid construction" case
        # CapabilityExecutionResultBuilder exists to prevent - see
        # tests/test_capability_execution_builder.py.
        result = CapabilityExecutionResult(
            metadata={"not": "a CapabilityExecutionMetadata"}  # type: ignore[arg-type]
        )
        with self.assertRaises(AttributeError):
            _ = result.metadata.extra


class SerializationConsistencyTests(unittest.TestCase):
    # Note: CapabilityExecutionMetadata.extra (and, via task/
    # capability, any attached Task's/Capability's own metadata.extra)
    # is wrapped in types.MappingProxyType, which is not picklable/
    # deepcopy-able in Python's standard library - the same inherent
    # limitation documented in tests/test_execution_result.py's own
    # equivalent test class since Package 032. These tests therefore
    # verify serialization consistency of CapabilityExecutionResult's
    # own scalar fields and of CapabilityExecutionStatus/
    # CapabilityExecutionMetadata.extra independently.

    def test_status_value_round_trips_through_the_enum(self):
        for status in CapabilityExecutionStatus:
            self.assertIs(CapabilityExecutionStatus(status.value), status)

    def test_deepcopy_of_scalar_fields_round_trips_equal(self):
        result = CapabilityExecutionResult(status=CapabilityExecutionStatus.COMPLETED)
        copied_id = copy.deepcopy(result.execution_id)
        copied_status = copy.deepcopy(result.status)
        self.assertEqual(copied_id, result.execution_id)
        self.assertIs(copied_status, result.status)

    def test_pickle_of_scalar_fields_round_trips_equal(self):
        result = CapabilityExecutionResult(status=CapabilityExecutionStatus.COMPLETED)
        self.assertEqual(
            pickle.loads(pickle.dumps(result.execution_id)), result.execution_id
        )
        self.assertIs(pickle.loads(pickle.dumps(result.status)), result.status)

    def test_metadata_extra_survives_a_plain_dict_round_trip(self):
        result = CapabilityExecutionResult(
            metadata=CapabilityExecutionMetadata(extra={"reason": "manual", "n": 3})
        )
        plain = dict(result.metadata.extra)
        rebuilt = CapabilityExecutionMetadata(extra=plain)
        self.assertEqual(dict(rebuilt.extra), dict(result.metadata.extra))

    def test_execution_id_is_a_plain_string_suitable_for_json(self):
        result = CapabilityExecutionResult()
        self.assertIsInstance(result.execution_id, str)


class EqualityTests(unittest.TestCase):
    def test_equality_when_all_fields_match(self):
        metadata = CapabilityExecutionMetadata()
        a = CapabilityExecutionResult(
            execution_id="r1", status=CapabilityExecutionStatus.COMPLETED, metadata=metadata
        )
        b = CapabilityExecutionResult(
            execution_id="r1", status=CapabilityExecutionStatus.COMPLETED, metadata=metadata
        )
        self.assertEqual(a, b)

    def test_not_equal_when_execution_id_differs(self):
        metadata = CapabilityExecutionMetadata()
        a = CapabilityExecutionResult(execution_id="r1", metadata=metadata)
        b = CapabilityExecutionResult(execution_id="r2", metadata=metadata)
        self.assertNotEqual(a, b)

    def test_not_equal_when_status_differs(self):
        metadata = CapabilityExecutionMetadata()
        a = CapabilityExecutionResult(
            execution_id="r1", status=CapabilityExecutionStatus.PENDING, metadata=metadata
        )
        b = CapabilityExecutionResult(
            execution_id="r1", status=CapabilityExecutionStatus.COMPLETED, metadata=metadata
        )
        self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main()
