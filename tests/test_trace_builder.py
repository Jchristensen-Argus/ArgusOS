"""Unit tests for argus.trace.builder.TraceBuilder."""

import unittest

from argus.trace import (
    ExecutionTrace,
    ITraceBuilder,
    InvalidTraceStepError,
    TraceBuilder,
)


class IdentityTests(unittest.TestCase):
    def test_is_an_itracebuilder(self):
        self.assertIsInstance(TraceBuilder(), ITraceBuilder)

    def test_starts_with_no_steps(self):
        trace = TraceBuilder().build()
        self.assertEqual(trace.steps, ())

    def test_constructor_takes_no_arguments(self):
        builder = TraceBuilder()
        self.assertIsInstance(builder, TraceBuilder)


class WithStepTests(unittest.TestCase):
    def test_with_step_returns_self_for_chaining(self):
        builder = TraceBuilder()
        result = builder.with_step("AgentService", "entry")
        self.assertIs(result, builder)

    def test_with_step_accumulates_in_call_order(self):
        trace = (
            TraceBuilder()
            .with_step("AgentService", "entry")
            .with_step("CognitivePipeline", "completed")
            .with_step("ResponseEngine", "invoked")
            .build()
        )
        self.assertEqual(
            [(s.component, s.action) for s in trace.steps],
            [
                ("AgentService", "entry"),
                ("CognitivePipeline", "completed"),
                ("ResponseEngine", "invoked"),
            ],
        )

    def test_with_step_accepts_metadata(self):
        trace = TraceBuilder().with_step("AgentService", "entry", metadata={"k": "v"}).build()
        self.assertEqual(dict(trace.steps[0].metadata), {"k": "v"})

    def test_with_step_without_metadata_produces_empty_step_metadata(self):
        trace = TraceBuilder().with_step("AgentService", "entry").build()
        self.assertEqual(dict(trace.steps[0].metadata), {})

    def test_with_step_rejects_empty_component(self):
        with self.assertRaises(InvalidTraceStepError):
            TraceBuilder().with_step("", "entry")

    def test_with_step_rejects_non_string_component(self):
        with self.assertRaises(InvalidTraceStepError):
            TraceBuilder().with_step(123, "entry")

    def test_with_step_rejects_empty_action(self):
        with self.assertRaises(InvalidTraceStepError):
            TraceBuilder().with_step("AgentService", "")

    def test_with_step_rejects_non_string_action(self):
        with self.assertRaises(InvalidTraceStepError):
            TraceBuilder().with_step("AgentService", None)

    def test_with_step_rejects_non_mapping_metadata(self):
        with self.assertRaises(InvalidTraceStepError):
            TraceBuilder().with_step("AgentService", "entry", metadata="not a mapping")

    def test_with_step_accepts_none_metadata(self):
        # None is the default sentinel, not itself invalid.
        trace = TraceBuilder().with_step("AgentService", "entry", metadata=None).build()
        self.assertEqual(dict(trace.steps[0].metadata), {})


class WithMetadataTests(unittest.TestCase):
    def test_with_metadata_returns_self_for_chaining(self):
        builder = TraceBuilder()
        result = builder.with_metadata("k", "v")
        self.assertIs(result, builder)

    def test_with_metadata_accumulates_distinct_keys(self):
        trace = TraceBuilder().with_metadata("a", 1).with_metadata("b", 2).build()
        self.assertEqual(dict(trace.metadata.extra), {"a": 1, "b": 2})

    def test_with_metadata_same_key_last_call_wins(self):
        trace = TraceBuilder().with_metadata("a", 1).with_metadata("a", 2).build()
        self.assertEqual(dict(trace.metadata.extra), {"a": 2})

    def test_with_metadata_rejects_empty_key(self):
        with self.assertRaises(InvalidTraceStepError):
            TraceBuilder().with_metadata("", "v")

    def test_with_metadata_rejects_non_string_key(self):
        with self.assertRaises(InvalidTraceStepError):
            TraceBuilder().with_metadata(123, "v")


class BuildTests(unittest.TestCase):
    def test_build_returns_an_execution_trace(self):
        trace = TraceBuilder().build()
        self.assertIsInstance(trace, ExecutionTrace)

    def test_trace_id_is_fixed_across_multiple_build_calls(self):
        builder = TraceBuilder()
        builder.with_step("AgentService", "entry")
        first = builder.build()
        builder.with_step("CognitivePipeline", "completed")
        second = builder.build()
        self.assertEqual(first.trace_id, second.trace_id)

    def test_independent_snapshots_earlier_build_not_mutated_by_later_steps(self):
        builder = TraceBuilder()
        builder.with_step("AgentService", "entry")
        first = builder.build()
        builder.with_step("CognitivePipeline", "completed")
        second = builder.build()
        self.assertEqual(len(first.steps), 1)
        self.assertEqual(len(second.steps), 2)

    def test_build_called_twice_with_no_new_steps_produces_equal_steps_and_trace_id(self):
        # Full object equality is not expected here - each build()
        # call constructs a fresh TraceMetadata with its own
        # created_at/correlation_id (see metadata.py's own module
        # docstring), the same "independent snapshot" behavior
        # ContextBuilder/PlanningSessionBuilder's own build() already
        # has. trace_id and steps are what stay identical.
        builder = TraceBuilder().with_step("AgentService", "entry")
        first = builder.build()
        second = builder.build()
        self.assertEqual(first.trace_id, second.trace_id)
        self.assertEqual(first.steps, second.steps)
        self.assertIsNot(first.metadata, second.metadata)

    def test_different_builders_produce_different_trace_ids(self):
        a = TraceBuilder().build()
        b = TraceBuilder().build()
        self.assertNotEqual(a.trace_id, b.trace_id)


if __name__ == "__main__":
    unittest.main()
