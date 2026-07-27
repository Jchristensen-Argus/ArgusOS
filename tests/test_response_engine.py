"""Unit tests for argus.response.engine.ResponseEngine."""

import dataclasses
import unittest

from argus.intent import Intent, IntentType
from argus.lifecycle import IService
from argus.lifecycle.lifecycle import LifecycleState
from argus.planner import Plan, PlanStatus
from argus.response import (
    IResponseEngine,
    InvalidPlanReferenceError,
    Response,
    ResponseEngine,
    ResponseError,
)


def _plan(**kwargs):
    return Plan(originating_intent=Intent(name=IntentType.UNKNOWN, confidence=0.0), **kwargs)


# -- identity / IService ----------------------------------------------


class ResponseEngineIdentityTests(unittest.TestCase):
    def test_is_an_iresponseengine(self):
        self.assertIsInstance(ResponseEngine(), IResponseEngine)

    def test_is_an_iservice(self):
        self.assertIsInstance(ResponseEngine(), IService)

    def test_starts_in_created_state(self):
        self.assertEqual(ResponseEngine().status(), LifecycleState.CREATED)

    def test_constructor_takes_no_arguments(self):
        # "ResponseEngine may depend only on: Plan" - and Plan is a
        # per-call argument, never a constructor dependency.
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
        response = engine.build_response(_plan())
        self.assertIsInstance(response, Response)

    def test_build_response_works_while_running(self):
        engine = ResponseEngine()
        engine.initialize()
        engine.start()
        response = engine.build_response(_plan())
        self.assertIsInstance(response, Response)

    def test_build_response_works_after_stopped(self):
        engine = ResponseEngine()
        engine.initialize()
        engine.start()
        engine.stop()
        response = engine.build_response(_plan())
        self.assertIsInstance(response, Response)


# -- valid plan / invalid plan -------------------------------------------


class ValidPlanTests(unittest.TestCase):
    def test_valid_plan_produces_a_response(self):
        engine = ResponseEngine()
        plan = _plan()
        response = engine.build_response(plan)
        self.assertIs(response.plan, plan)
        self.assertEqual(response.status, plan.status)

    def test_validated_plan_status_is_carried_through(self):
        engine = ResponseEngine()
        plan = dataclasses.replace(_plan(), status=PlanStatus.VALIDATED)
        response = engine.build_response(plan)
        self.assertEqual(response.status, PlanStatus.VALIDATED)


class InvalidPlanTests(unittest.TestCase):
    def test_non_plan_argument_raises(self):
        engine = ResponseEngine()
        with self.assertRaises(InvalidPlanReferenceError):
            engine.build_response("not a plan")

    def test_none_argument_raises(self):
        engine = ResponseEngine()
        with self.assertRaises(InvalidPlanReferenceError):
            engine.build_response(None)

    def test_dict_masquerading_as_plan_raises(self):
        engine = ResponseEngine()
        with self.assertRaises(InvalidPlanReferenceError):
            engine.build_response({"originating_intent": None})


# -- immutable response -------------------------------------------------


class ImmutableResponseTests(unittest.TestCase):
    def test_response_cannot_be_mutated(self):
        engine = ResponseEngine()
        response = engine.build_response(_plan())
        with self.assertRaises(dataclasses.FrozenInstanceError):
            response.status = PlanStatus.VALIDATED

    def test_plan_is_never_mutated(self):
        engine = ResponseEngine()
        plan = _plan()
        before = dataclasses.replace(plan)
        engine.build_response(plan)
        self.assertEqual(plan, before)


# -- metadata propagation ----------------------------------------------


class MetadataPropagationTests(unittest.TestCase):
    def test_plan_metadata_propagates_into_response_metadata_extra(self):
        engine = ResponseEngine()
        plan = _plan(metadata={"planning_session_id": "ps-1", "constraints": ()})
        response = engine.build_response(plan)
        self.assertEqual(response.metadata.extra["planning_session_id"], "ps-1")
        self.assertEqual(response.metadata.extra["constraints"], ())

    def test_empty_plan_metadata_produces_empty_extra(self):
        engine = ResponseEngine()
        response = engine.build_response(_plan())
        self.assertEqual(dict(response.metadata.extra), {})

    def test_plan_metadata_is_defensively_copied_not_shared(self):
        engine = ResponseEngine()
        plan_metadata = {"k": "v"}
        plan = _plan(metadata=plan_metadata)
        response = engine.build_response(plan)
        plan_metadata["k"] = "changed"
        self.assertEqual(response.metadata.extra["k"], "v")

    def test_response_metadata_has_its_own_fresh_timestamp_and_correlation_id(self):
        engine = ResponseEngine()
        plan = _plan()
        response = engine.build_response(plan)
        self.assertTrue(response.metadata.correlation_id)
        self.assertIsNotNone(response.metadata.timestamp)


# -- dependency failures (this engine has no dependency to fail on) ------


class NoDependencyToFailTests(unittest.TestCase):
    def test_engine_holds_no_collaborator_reference(self):
        # ResponseEngine may depend only on Plan - there is no
        # constructor-injected collaborator whose failure could ever
        # propagate through build_response(); the only failure mode is
        # an invalid Plan reference, covered by InvalidPlanTests above.
        engine = ResponseEngine()
        self.assertEqual(vars(engine), {"_state": LifecycleState.CREATED})


if __name__ == "__main__":
    unittest.main()
