"""Unit tests for argus.response.response.Response."""

import dataclasses
import unittest

from argus.intent import Intent, IntentType
from argus.planner import Plan, PlanStatus
from argus.response import Response, ResponseMetadata
from argus.trace import ExecutionTrace, TraceBuilder


def _plan(**kwargs):
    return Plan(originating_intent=Intent(name=IntentType.UNKNOWN, confidence=0.0), **kwargs)


def _trace():
    return TraceBuilder().with_step("AgentService", "entry").build()


class DefaultsTests(unittest.TestCase):
    def test_defaults(self):
        plan = _plan()
        trace = _trace()
        response = Response(plan=plan, execution_trace=trace)
        self.assertIs(response.plan, plan)
        self.assertIs(response.execution_trace, trace)
        self.assertTrue(response.response_id)
        self.assertEqual(response.status, PlanStatus.CREATED)
        self.assertIsInstance(response.metadata, ResponseMetadata)

    def test_all_fields_set(self):
        plan = _plan()
        trace = _trace()
        metadata = ResponseMetadata(extra={"k": "v"})
        response = Response(
            plan=plan,
            execution_trace=trace,
            response_id="fixed-id",
            status=PlanStatus.VALIDATED,
            metadata=metadata,
        )
        self.assertIs(response.plan, plan)
        self.assertIs(response.execution_trace, trace)
        self.assertEqual(response.response_id, "fixed-id")
        self.assertEqual(response.status, PlanStatus.VALIDATED)
        self.assertIs(response.metadata, metadata)

    def test_default_response_id_is_unique_per_instance(self):
        plan = _plan()
        trace = _trace()
        a = Response(plan=plan, execution_trace=trace)
        b = Response(plan=plan, execution_trace=trace)
        self.assertNotEqual(a.response_id, b.response_id)

    def test_default_metadata_is_a_fresh_instance_per_response(self):
        plan = _plan()
        trace = _trace()
        a = Response(plan=plan, execution_trace=trace)
        b = Response(plan=plan, execution_trace=trace)
        self.assertIsNot(a.metadata, b.metadata)


class NoNaturalLanguageOrRenderingTests(unittest.TestCase):
    def test_no_natural_language_markdown_or_rendering_fields_exist(self):
        # "Do not include natural-language text. Do not include
        # markdown. Do not include rendering. The Response object
        # represents a completed cognitive result only."
        field_names = {f.name for f in dataclasses.fields(Response)}
        self.assertEqual(
            field_names,
            {"plan", "execution_trace", "response_id", "status", "metadata"},
        )


class ExecutionTraceFieldTests(unittest.TestCase):
    def test_execution_trace_is_required(self):
        with self.assertRaises(TypeError):
            Response(plan=_plan())  # type: ignore[call-arg]

    def test_execution_trace_accepts_empty_trace(self):
        response = Response(plan=_plan(), execution_trace=ExecutionTrace())
        self.assertEqual(response.execution_trace.steps, ())

    def test_execution_trace_accepts_populated_trace(self):
        trace = (
            TraceBuilder()
            .with_step("AgentService", "entry")
            .with_step("CognitivePipeline", "completed")
            .with_step("ResponseEngine", "invoked")
            .build()
        )
        response = Response(plan=_plan(), execution_trace=trace)
        self.assertEqual(len(response.execution_trace.steps), 3)


class StatusTests(unittest.TestCase):
    def test_valid_plan_produces_created_status_response(self):
        plan = _plan()
        response = Response(plan=plan, execution_trace=_trace(), status=plan.status)
        self.assertEqual(response.status, PlanStatus.CREATED)

    def test_validated_plan_status_can_be_carried_through(self):
        plan = dataclasses.replace(_plan(), status=PlanStatus.VALIDATED)
        response = Response(plan=plan, execution_trace=_trace(), status=plan.status)
        self.assertEqual(response.status, PlanStatus.VALIDATED)

    def test_failed_plan_status_can_be_carried_through(self):
        plan = dataclasses.replace(_plan(), status=PlanStatus.FAILED)
        response = Response(plan=plan, execution_trace=_trace(), status=plan.status)
        self.assertEqual(response.status, PlanStatus.FAILED)


class ImmutabilityTests(unittest.TestCase):
    def test_immutability(self):
        response = Response(plan=_plan(), execution_trace=_trace())
        with self.assertRaises(dataclasses.FrozenInstanceError):
            response.status = PlanStatus.VALIDATED

    def test_plan_field_cannot_be_reassigned(self):
        response = Response(plan=_plan(), execution_trace=_trace())
        with self.assertRaises(dataclasses.FrozenInstanceError):
            response.plan = None

    def test_execution_trace_field_cannot_be_reassigned(self):
        response = Response(plan=_plan(), execution_trace=_trace())
        with self.assertRaises(dataclasses.FrozenInstanceError):
            response.execution_trace = ExecutionTrace()


class EqualityTests(unittest.TestCase):
    def test_equality_when_all_fields_match(self):
        plan = _plan()
        trace = _trace()
        metadata = ResponseMetadata()
        a = Response(
            plan=plan, execution_trace=trace, response_id="r1",
            status=PlanStatus.CREATED, metadata=metadata,
        )
        b = Response(
            plan=plan, execution_trace=trace, response_id="r1",
            status=PlanStatus.CREATED, metadata=metadata,
        )
        self.assertEqual(a, b)

    def test_not_equal_when_response_id_differs(self):
        plan = _plan()
        trace = _trace()
        metadata = ResponseMetadata()
        a = Response(plan=plan, execution_trace=trace, response_id="r1", metadata=metadata)
        b = Response(plan=plan, execution_trace=trace, response_id="r2", metadata=metadata)
        self.assertNotEqual(a, b)

    def test_not_equal_when_execution_trace_differs(self):
        plan = _plan()
        metadata = ResponseMetadata()
        a = Response(plan=plan, execution_trace=_trace(), response_id="r1", metadata=metadata)
        b = Response(plan=plan, execution_trace=_trace(), response_id="r1", metadata=metadata)
        self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main()
