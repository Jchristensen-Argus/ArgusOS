"""Unit tests for argus.response.engine.ResponseEngine."""

import dataclasses
import unittest

from argus.execution_engine import ExecutionResult, ExecutionStatus
from argus.intent import Intent, IntentType
from argus.lifecycle import IService
from argus.lifecycle.lifecycle import LifecycleState
from argus.planner import Plan, PlanStatus
from argus.response import (
    IResponseEngine,
    InvalidExecutionResultError,
    InvalidExecutionTraceError,
    InvalidPlanReferenceError,
    Response,
    ResponseEngine,
    ResponseError,
)
from argus.trace import ExecutionTrace, TraceBuilder


def _plan(**kwargs):
    return Plan(originating_intent=Intent(name=IntentType.UNKNOWN, confidence=0.0), **kwargs)


def _trace():
    return (
        TraceBuilder()
        .with_step("AgentService", "entry")
        .with_step("CognitivePipeline", "completed")
        .with_step("ExecutionEngine", "processed")
        .with_step("ResponseEngine", "invoked")
        .build()
    )


def _execution_result(**kwargs):
    return ExecutionResult(**kwargs)


# -- identity / IService ----------------------------------------------


class ResponseEngineIdentityTests(unittest.TestCase):
    def test_is_an_iresponseengine(self):
        self.assertIsInstance(ResponseEngine(), IResponseEngine)

    def test_is_an_iservice(self):
        self.assertIsInstance(ResponseEngine(), IService)

    def test_starts_in_created_state(self):
        self.assertEqual(ResponseEngine().status(), LifecycleState.CREATED)

    def test_constructor_takes_no_arguments(self):
        # "ResponseEngine may depend only on: Plan" (and, as of
        # Package 028, ExecutionTrace, and as of Package 032,
        # ExecutionResult) - all are per-call arguments, never
        # constructor dependencies.
        engine = ResponseEngine()
        self.assertIsInstance(engine, ResponseEngine)


# -- lifecycle ----------------------------------------------------------


class ResponseEngineLifecycleTests(unittest.TestCase):
    def test_initialize_transitions_to_initializing(self):
        engine = ResponseEngine()
        engine.initialize()
        self.assertEqual(engine.status(), LifecycleState.INITIALIZING)

    def test_initialize_twice_raises(self):
        engine = ResponseEngine()
        engine.initialize()
        with self.assertRaises(ResponseError):
            engine.initialize()

    def test_start_requires_initializing(self):
        engine = ResponseEngine()
        with self.assertRaises(ResponseError):
            engine.start()

    def test_start_transitions_to_running(self):
        engine = ResponseEngine()
        engine.initialize()
        engine.start()
        self.assertEqual(engine.status(), LifecycleState.RUNNING)

    def test_stop_requires_running(self):
        engine = ResponseEngine()
        with self.assertRaises(ResponseError):
            engine.stop()

    def test_stop_transitions_to_stopped(self):
        engine = ResponseEngine()
        engine.initialize()
        engine.start()
        engine.stop()
        self.assertEqual(engine.status(), LifecycleState.STOPPED)

    def test_status_reflects_current_state_throughout(self):
        engine = ResponseEngine()
        self.assertEqual(engine.status(), LifecycleState.CREATED)
        engine.initialize()
        self.assertEqual(engine.status(), LifecycleState.INITIALIZING)
        engine.start()
        self.assertEqual(engine.status(), LifecycleState.RUNNING)
        engine.stop()
        self.assertEqual(engine.status(), LifecycleState.STOPPED)


# -- build_response() is never gated -----------------------------------


class UngatedBehaviorTests(unittest.TestCase):
    def test_build_response_works_in_created_state(self):
        engine = ResponseEngine()
        self.assertEqual(engine.status(), LifecycleState.CREATED)
        response = engine.build_response(_plan(), _execution_result(), _trace())
        self.assertIsInstance(response, Response)

    def test_build_response_works_while_running(self):
        engine = ResponseEngine()
        engine.initialize()
        engine.start()
        response = engine.build_response(_plan(), _execution_result(), _trace())
        self.assertIsInstance(response, Response)

    def test_build_response_works_after_stopped(self):
        engine = ResponseEngine()
        engine.initialize()
        engine.start()
        engine.stop()
        response = engine.build_response(_plan(), _execution_result(), _trace())
        self.assertIsInstance(response, Response)


# -- valid plan / invalid plan -------------------------------------------


class ValidPlanTests(unittest.TestCase):
    def test_valid_plan_produces_a_response(self):
        engine = ResponseEngine()
        plan = _plan()
        response = engine.build_response(plan, _execution_result(), _trace())
        self.assertIs(response.plan, plan)
        self.assertEqual(response.status, plan.status)

    def test_validated_plan_status_is_carried_through(self):
        engine = ResponseEngine()
        plan = dataclasses.replace(_plan(), status=PlanStatus.VALIDATED)
        response = engine.build_response(plan, _execution_result(), _trace())
        self.assertEqual(response.status, PlanStatus.VALIDATED)


class InvalidPlanTests(unittest.TestCase):
    def test_non_plan_argument_raises(self):
        engine = ResponseEngine()
        with self.assertRaises(InvalidPlanReferenceError):
            engine.build_response("not a plan", _execution_result(), _trace())

    def test_none_argument_raises(self):
        engine = ResponseEngine()
        with self.assertRaises(InvalidPlanReferenceError):
            engine.build_response(None, _execution_result(), _trace())

    def test_dict_masquerading_as_plan_raises(self):
        engine = ResponseEngine()
        with self.assertRaises(InvalidPlanReferenceError):
            engine.build_response({"originating_intent": None}, _execution_result(), _trace())


# -- valid execution_result / invalid execution_result -------------------


class ValidExecutionResultTests(unittest.TestCase):
    def test_valid_result_is_embedded_unmodified(self):
        engine = ResponseEngine()
        result = _execution_result()
        response = engine.build_response(_plan(), result, _trace())
        self.assertIs(response.execution_result, result)

    def test_pending_result_is_accepted(self):
        engine = ResponseEngine()
        response = engine.build_response(_plan(), _execution_result(), _trace())
        self.assertEqual(response.execution_result.status, ExecutionStatus.PENDING)

    def test_completed_result_is_accepted(self):
        engine = ResponseEngine()
        result = ExecutionResult(status=ExecutionStatus.COMPLETED)
        response = engine.build_response(_plan(), result, _trace())
        self.assertEqual(response.execution_result.status, ExecutionStatus.COMPLETED)


class InvalidExecutionResultTests(unittest.TestCase):
    def test_non_result_argument_raises(self):
        engine = ResponseEngine()
        with self.assertRaises(InvalidExecutionResultError):
            engine.build_response(_plan(), "not a result", _trace())

    def test_none_argument_raises(self):
        engine = ResponseEngine()
        with self.assertRaises(InvalidExecutionResultError):
            engine.build_response(_plan(), None, _trace())

    def test_dict_masquerading_as_result_raises(self):
        engine = ResponseEngine()
        with self.assertRaises(InvalidExecutionResultError):
            engine.build_response(_plan(), {"status": "completed"}, _trace())

    def test_invalid_plan_is_checked_before_invalid_execution_result(self):
        # Both references are invalid - the Plan check runs first,
        # mirroring engine.py's own literal validation order.
        engine = ResponseEngine()
        with self.assertRaises(InvalidPlanReferenceError):
            engine.build_response("not a plan", "not a result either", _trace())


# -- valid execution_trace / invalid execution_trace ----------------------


class ValidExecutionTraceTests(unittest.TestCase):
    def test_valid_trace_is_embedded_unmodified(self):
        engine = ResponseEngine()
        trace = _trace()
        response = engine.build_response(_plan(), _execution_result(), trace)
        self.assertIs(response.execution_trace, trace)

    def test_empty_trace_is_accepted(self):
        engine = ResponseEngine()
        response = engine.build_response(_plan(), _execution_result(), ExecutionTrace())
        self.assertEqual(response.execution_trace.steps, ())


class InvalidExecutionTraceTests(unittest.TestCase):
    def test_non_trace_argument_raises(self):
        engine = ResponseEngine()
        with self.assertRaises(InvalidExecutionTraceError):
            engine.build_response(_plan(), _execution_result(), "not a trace")

    def test_none_argument_raises(self):
        engine = ResponseEngine()
        with self.assertRaises(InvalidExecutionTraceError):
            engine.build_response(_plan(), _execution_result(), None)

    def test_dict_masquerading_as_trace_raises(self):
        engine = ResponseEngine()
        with self.assertRaises(InvalidExecutionTraceError):
            engine.build_response(_plan(), _execution_result(), {"steps": ()})

    def test_invalid_plan_is_checked_before_invalid_trace(self):
        # All three references are invalid - the Plan check runs
        # first, mirroring engine.py's own literal validation order.
        engine = ResponseEngine()
        with self.assertRaises(InvalidPlanReferenceError):
            engine.build_response("not a plan", "not a result either", "not a trace either")

    def test_invalid_execution_result_is_checked_before_invalid_trace(self):
        # Plan is valid, but both execution_result and execution_trace
        # are invalid - the execution_result check runs first,
        # mirroring engine.py's own literal validation order.
        engine = ResponseEngine()
        with self.assertRaises(InvalidExecutionResultError):
            engine.build_response(_plan(), "not a result", "not a trace either")


# -- immutable response -------------------------------------------------


class ImmutableResponseTests(unittest.TestCase):
    def test_response_cannot_be_mutated(self):
        engine = ResponseEngine()
        response = engine.build_response(_plan(), _execution_result(), _trace())
        with self.assertRaises(dataclasses.FrozenInstanceError):
            response.status = PlanStatus.VALIDATED

    def test_plan_is_never_mutated(self):
        engine = ResponseEngine()
        plan = _plan()
        before = dataclasses.replace(plan)
        engine.build_response(plan, _execution_result(), _trace())
        self.assertEqual(plan, before)

    def test_execution_result_is_never_mutated(self):
        engine = ResponseEngine()
        result = _execution_result()
        completed_before = result.completed_tasks
        engine.build_response(_plan(), result, _trace())
        self.assertEqual(result.completed_tasks, completed_before)

    def test_execution_trace_is_never_mutated(self):
        engine = ResponseEngine()
        trace = _trace()
        steps_before = trace.steps
        engine.build_response(_plan(), _execution_result(), trace)
        self.assertEqual(trace.steps, steps_before)


# -- metadata propagation ----------------------------------------------


class MetadataPropagationTests(unittest.TestCase):
    def test_plan_metadata_propagates_into_response_metadata_extra(self):
        engine = ResponseEngine()
        plan = _plan(metadata={"planning_session_id": "ps-1", "constraints": ()})
        response = engine.build_response(plan, _execution_result(), _trace())
        self.assertEqual(response.metadata.extra["planning_session_id"], "ps-1")
        self.assertEqual(response.metadata.extra["constraints"], ())

    def test_empty_plan_metadata_produces_empty_extra(self):
        engine = ResponseEngine()
        response = engine.build_response(_plan(), _execution_result(), _trace())
        self.assertEqual(dict(response.metadata.extra), {})

    def test_plan_metadata_is_defensively_copied_not_shared(self):
        engine = ResponseEngine()
        plan_metadata = {"k": "v"}
        plan = _plan(metadata=plan_metadata)
        response = engine.build_response(plan, _execution_result(), _trace())
        plan_metadata["k"] = "changed"
        self.assertEqual(response.metadata.extra["k"], "v")

    def test_response_metadata_has_its_own_fresh_timestamp_and_correlation_id(self):
        engine = ResponseEngine()
        plan = _plan()
        response = engine.build_response(plan, _execution_result(), _trace())
        self.assertTrue(response.metadata.correlation_id)
        self.assertIsNotNone(response.metadata.timestamp)


# -- dependency failures (this engine has no dependency to fail on) ------


class NoDependencyToFailTests(unittest.TestCase):
    def test_engine_holds_no_collaborator_reference(self):
        # ResponseEngine may depend only on Plan, ExecutionResult, and
        # ExecutionTrace - there is no constructor-injected
        # collaborator whose failure could ever propagate through
        # build_response(); the only failure modes are invalid
        # Plan/ExecutionResult/ExecutionTrace references, covered by
        # InvalidPlanTests/InvalidExecutionResultTests/
        # InvalidExecutionTraceTests above.
        engine = ResponseEngine()
        self.assertEqual(vars(engine), {"_state": LifecycleState.CREATED})


if __name__ == "__main__":
    unittest.main()
