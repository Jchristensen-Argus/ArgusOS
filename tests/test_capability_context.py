"""Unit tests for argus.capability_context.context.CapabilityContext."""

import copy
import dataclasses
import pickle
import unittest

from argus.capability_context import CapabilityContext, CapabilityContextMetadata
from argus.intent import Intent
from argus.planner.plan import Plan
from argus.task import Task


def _plan(**kwargs) -> Plan:
    defaults = dict(originating_intent=Intent(name="demo_intent", confidence=0.9))
    defaults.update(kwargs)
    return Plan(**defaults)


class DefaultsTests(unittest.TestCase):
    def test_defaults(self):
        context = CapabilityContext()
        self.assertTrue(context.context_id)
        self.assertIsNone(context.task)
        self.assertIsNone(context.plan)
        self.assertIsNone(context.execution_trace)
        self.assertIsInstance(context.metadata, CapabilityContextMetadata)

    def test_all_fields_set(self):
        task = Task(name="A")
        plan = _plan()
        metadata = CapabilityContextMetadata(extra={"k": "v"})
        context = CapabilityContext(
            context_id="fixed-id",
            task=task,
            plan=plan,
            execution_trace=None,
            metadata=metadata,
        )
        self.assertEqual(context.context_id, "fixed-id")
        self.assertIs(context.task, task)
        self.assertIs(context.plan, plan)
        self.assertIsNone(context.execution_trace)
        self.assertIs(context.metadata, metadata)

    def test_default_context_id_is_unique_per_instance(self):
        a = CapabilityContext()
        b = CapabilityContext()
        self.assertNotEqual(a.context_id, b.context_id)


class FieldOrderTests(unittest.TestCase):
    def test_field_order_places_metadata_last(self):
        field_names = [f.name for f in dataclasses.fields(CapabilityContext)]
        self.assertEqual(
            field_names,
            ["context_id", "task", "plan", "execution_trace", "metadata"],
        )


class ExecutionTraceAlwaysNoneInVersion1Tests(unittest.TestCase):
    def test_execution_trace_field_exists_and_defaults_to_none(self):
        # See context.py's own module docstring's "execution_trace Is
        # Always None In Version 1" note - no genuine ExecutionTrace
        # exists at the point ExecutionEngine constructs a
        # CapabilityContext, so this field is never populated by
        # ExecutionEngine in Version 1.
        context = CapabilityContext(task=Task(name="A"), plan=_plan())
        self.assertIsNone(context.execution_trace)


class ObjectReferenceIdentityTests(unittest.TestCase):
    def test_task_holds_the_actual_object_not_a_reference_string(self):
        task = Task(name="A")
        context = CapabilityContext(task=task)
        self.assertIs(context.task, task)

    def test_plan_holds_the_actual_object_not_a_reference_string(self):
        plan = _plan()
        context = CapabilityContext(plan=plan)
        self.assertIs(context.plan, plan)


class ImmutabilityTests(unittest.TestCase):
    def test_immutability(self):
        context = CapabilityContext()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            context.context_id = "mutated"

    def test_task_field_immutable(self):
        context = CapabilityContext()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            context.task = Task(name="B")

    def test_metadata_field_immutable(self):
        context = CapabilityContext()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            context.metadata = CapabilityContextMetadata()


class MiscellaneousRobustnessTests(unittest.TestCase):
    def test_deepcopy_of_scalar_fields_round_trips_equal(self):
        context = CapabilityContext()
        copied_id = copy.deepcopy(context.context_id)
        self.assertEqual(copied_id, context.context_id)

    def test_pickle_of_scalar_fields_round_trips_equal(self):
        context = CapabilityContext()
        self.assertEqual(
            pickle.loads(pickle.dumps(context.context_id)), context.context_id
        )

    def test_context_id_is_a_plain_string_suitable_for_json(self):
        context = CapabilityContext()
        self.assertIsInstance(context.context_id, str)


class EqualityTests(unittest.TestCase):
    def test_equality_when_all_fields_match(self):
        metadata = CapabilityContextMetadata()
        a = CapabilityContext(context_id="c1", metadata=metadata)
        b = CapabilityContext(context_id="c1", metadata=metadata)
        self.assertEqual(a, b)

    def test_not_equal_when_context_id_differs(self):
        metadata = CapabilityContextMetadata()
        a = CapabilityContext(context_id="c1", metadata=metadata)
        b = CapabilityContext(context_id="c2", metadata=metadata)
        self.assertNotEqual(a, b)

    def test_not_equal_when_task_differs(self):
        metadata = CapabilityContextMetadata()
        a = CapabilityContext(context_id="c1", task=Task(name="A"), metadata=metadata)
        b = CapabilityContext(context_id="c1", task=Task(name="B"), metadata=metadata)
        self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main()
