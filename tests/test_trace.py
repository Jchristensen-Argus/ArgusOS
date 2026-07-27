"""Unit tests for argus.trace.trace.ExecutionTrace."""

import dataclasses
import unittest

from argus.trace import ExecutionTrace, TraceMetadata, TraceStep


class DefaultsTests(unittest.TestCase):
    def test_defaults(self):
        trace = ExecutionTrace()
        self.assertTrue(trace.trace_id)
        self.assertEqual(trace.steps, ())
        self.assertIsInstance(trace.metadata, TraceMetadata)

    def test_all_fields_set(self):
        step = TraceStep(component="AgentService", action="entry")
        metadata = TraceMetadata(extra={"k": "v"})
        trace = ExecutionTrace(trace_id="fixed-id", steps=(step,), metadata=metadata)
        self.assertEqual(trace.trace_id, "fixed-id")
        self.assertEqual(trace.steps, (step,))
        self.assertIs(trace.metadata, metadata)

    def test_default_trace_id_is_unique_per_instance(self):
        a = ExecutionTrace()
        b = ExecutionTrace()
        self.assertNotEqual(a.trace_id, b.trace_id)

    def test_default_metadata_is_a_fresh_instance_per_trace(self):
        a = ExecutionTrace()
        b = ExecutionTrace()
        self.assertIsNot(a.metadata, b.metadata)


class EmptyTraceTests(unittest.TestCase):
    def test_empty_trace_is_valid(self):
        trace = ExecutionTrace()
        self.assertEqual(len(trace.steps), 0)


class PopulatedTraceTests(unittest.TestCase):
    def test_populated_trace_preserves_call_order(self):
        step_a = TraceStep(component="AgentService", action="entry")
        step_b = TraceStep(component="CognitivePipeline", action="completed")
        step_c = TraceStep(component="ResponseEngine", action="invoked")
        trace = ExecutionTrace(steps=(step_a, step_b, step_c))
        self.assertEqual(trace.steps, (step_a, step_b, step_c))

    def test_steps_given_as_a_list_are_stored_as_a_tuple(self):
        step = TraceStep(component="AgentService", action="entry")
        trace = ExecutionTrace(steps=[step])
        self.assertIsInstance(trace.steps, tuple)
        self.assertEqual(trace.steps, (step,))


class ImmutabilityTests(unittest.TestCase):
    def test_immutability(self):
        trace = ExecutionTrace()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            trace.trace_id = "other"

    def test_steps_field_cannot_be_reassigned(self):
        trace = ExecutionTrace()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            trace.steps = ()

    def test_steps_tuple_itself_is_immutable(self):
        step = TraceStep(component="AgentService", action="entry")
        trace = ExecutionTrace(steps=(step,))
        with self.assertRaises(AttributeError):
            trace.steps.append(step)  # type: ignore[attr-defined]


class NoInternalReasoningTests(unittest.TestCase):
    def test_trace_holds_no_field_beyond_identity_steps_and_metadata(self):
        field_names = {f.name for f in dataclasses.fields(ExecutionTrace)}
        self.assertEqual(field_names, {"trace_id", "steps", "metadata"})


class EqualityTests(unittest.TestCase):
    def test_equality_when_all_fields_match(self):
        step = TraceStep(component="AgentService", action="entry", step_id="s1")
        metadata = TraceMetadata()
        a = ExecutionTrace(trace_id="t1", steps=(step,), metadata=metadata)
        b = ExecutionTrace(trace_id="t1", steps=(step,), metadata=metadata)
        self.assertEqual(a, b)

    def test_not_equal_when_trace_id_differs(self):
        metadata = TraceMetadata()
        a = ExecutionTrace(trace_id="t1", metadata=metadata)
        b = ExecutionTrace(trace_id="t2", metadata=metadata)
        self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main()
