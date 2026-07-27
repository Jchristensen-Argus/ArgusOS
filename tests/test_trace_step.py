"""Unit tests for argus.trace.step.TraceStep."""

import dataclasses
import unittest
from datetime import datetime

from argus.trace import TraceStep


class DefaultsTests(unittest.TestCase):
    def test_defaults(self):
        step = TraceStep(component="AgentService", action="entry")
        self.assertEqual(step.component, "AgentService")
        self.assertEqual(step.action, "entry")
        self.assertTrue(step.step_id)
        self.assertIsInstance(step.timestamp, datetime)
        self.assertEqual(dict(step.metadata), {})

    def test_all_fields_set(self):
        step = TraceStep(
            component="CognitivePipeline",
            action="completed",
            step_id="fixed-id",
            metadata={"k": "v"},
        )
        self.assertEqual(step.component, "CognitivePipeline")
        self.assertEqual(step.action, "completed")
        self.assertEqual(step.step_id, "fixed-id")
        self.assertEqual(dict(step.metadata), {"k": "v"})

    def test_default_step_id_is_unique_per_instance(self):
        a = TraceStep(component="AgentService", action="entry")
        b = TraceStep(component="AgentService", action="entry")
        self.assertNotEqual(a.step_id, b.step_id)

    def test_component_and_action_are_required(self):
        with self.assertRaises(TypeError):
            TraceStep()  # type: ignore[call-arg]
        with self.assertRaises(TypeError):
            TraceStep(component="AgentService")  # type: ignore[call-arg]


class MetadataTests(unittest.TestCase):
    def test_metadata_is_wrapped_in_mappingproxytype(self):
        step = TraceStep(component="AgentService", action="entry", metadata={"a": 1})
        self.assertNotIsInstance(step.metadata, dict)
        self.assertEqual(step.metadata["a"], 1)

    def test_metadata_defensive_copy_not_shared_with_caller(self):
        original = {"a": 1}
        step = TraceStep(component="AgentService", action="entry", metadata=original)
        original["a"] = 999
        self.assertEqual(step.metadata["a"], 1)

    def test_metadata_is_immutable(self):
        step = TraceStep(component="AgentService", action="entry", metadata={"a": 1})
        with self.assertRaises(TypeError):
            step.metadata["a"] = 2


class ImmutabilityTests(unittest.TestCase):
    def test_immutability(self):
        step = TraceStep(component="AgentService", action="entry")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            step.component = "ResponseEngine"

    def test_action_field_cannot_be_reassigned(self):
        step = TraceStep(component="AgentService", action="entry")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            step.action = "completed"


class NoInternalReasoningTests(unittest.TestCase):
    def test_step_holds_no_reference_to_reasoning_or_output(self):
        # "The trace records that a stage occurred, not its internal
        # reasoning" - TraceStep has no field for whatever data a
        # component actually produced.
        field_names = {f.name for f in dataclasses.fields(TraceStep)}
        self.assertEqual(
            field_names, {"component", "action", "step_id", "timestamp", "metadata"}
        )


class EqualityTests(unittest.TestCase):
    def test_equality_when_all_fields_match(self):
        a = TraceStep(component="AgentService", action="entry", step_id="s1", timestamp=datetime(2026, 1, 1))
        b = TraceStep(component="AgentService", action="entry", step_id="s1", timestamp=datetime(2026, 1, 1))
        self.assertEqual(a, b)

    def test_not_equal_when_step_id_differs(self):
        a = TraceStep(component="AgentService", action="entry", step_id="s1")
        b = TraceStep(component="AgentService", action="entry", step_id="s2")
        self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main()
