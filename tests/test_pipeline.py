"""Unit tests for argus.pipeline.pipeline.CognitivePipeline."""

import dataclasses
import logging
import unittest

from argus.capability import CapabilityRegistry
from argus.conversation import ConversationMessage, ConversationRole, ConversationSession
from argus.events import InMemoryEventBus
from argus.lifecycle import IService
from argus.lifecycle.lifecycle import LifecycleState
from argus.pipeline import (
    CognitivePipeline,
    ICognitivePipeline,
    InvalidPipelineRequestError,
    PipelineError,
    PipelineExecutionError,
    PipelineRequest,
)
from argus.planner import InvalidPlanError, Planner


def _silent_logger() -> logging.Logger:
    logger = logging.getLogger("test_pipeline")
    logger.addHandler(logging.NullHandler())
    logger.propagate = False
    return logger


def _real_planner():
    bus = InMemoryEventBus(logger=_silent_logger())
    registry = CapabilityRegistry(event_bus=bus)
    return Planner(event_bus=bus, capability_registry=registry)


class RecordingPlanner:
    """A test double recording exactly what plan_session() was called
    with, so orchestration order and delegation can be verified
    without depending on Planner's own internals."""

    def __init__(self, plan_to_return):
        self.calls = []
        self._plan_to_return = plan_to_return

    def plan_session(self, planning_session):
        self.calls.append(planning_session)
        return self._plan_to_return


class RaisingPlanner:
    def plan_session(self, planning_session):
        raise InvalidPlanError("synthetic failure for dependency-failure testing")


def _started_pipeline(planner=None) -> CognitivePipeline:
    pipeline = CognitivePipeline(planner=planner or _real_planner())
    pipeline.initialize()
    pipeline.start()
    return pipeline


class PipelineTestCase(unittest.TestCase):
    def tearDown(self):
        # Best-effort cleanup for any pipeline a test started but did
        # not explicitly stop.
        pass


# -- identity / IService ----------------------------------------------


class CognitivePipelineIdentityTests(unittest.TestCase):
    def test_is_an_icognitivepipeline(self):
        self.assertIsInstance(CognitivePipeline(planner=_real_planner()), ICognitivePipeline)

    def test_is_an_iservice(self):
        self.assertIsInstance(CognitivePipeline(planner=_real_planner()), IService)

    def test_starts_in_created_state(self):
        pipeline = CognitivePipeline(planner=_real_planner())
        self.assertEqual(pipeline.status(), LifecycleState.CREATED)


# -- lifecycle ----------------------------------------------------------


class CognitivePipelineLifecycleTests(unittest.TestCase):
    def test_initialize_transitions_to_initializing(self):
        pipeline = CognitivePipeline(planner=_real_planner())
        pipeline.initialize()
        self.assertEqual(pipeline.status(), LifecycleState.INITIALIZING)

    def test_initialize_twice_raises(self):
        pipeline = CognitivePipeline(planner=_real_planner())
        pipeline.initialize()
        with self.assertRaises(PipelineError):
            pipeline.initialize()

    def test_start_requires_initializing(self):
        pipeline = CognitivePipeline(planner=_real_planner())
        with self.assertRaises(PipelineError):
            pipeline.start()

    def test_start_transitions_to_running(self):
        pipeline = CognitivePipeline(planner=_real_planner())
        pipeline.initialize()
        pipeline.start()
        self.assertEqual(pipeline.status(), LifecycleState.RUNNING)

    def test_stop_requires_running(self):
        pipeline = CognitivePipeline(planner=_real_planner())
        with self.assertRaises(PipelineError):
            pipeline.stop()

    def test_stop_transitions_to_stopped(self):
        pipeline = _started_pipeline()
        pipeline.stop()
        self.assertEqual(pipeline.status(), LifecycleState.STOPPED)

    def test_status_reflects_current_state_throughout(self):
        pipeline = CognitivePipeline(planner=_real_planner())
        self.assertEqual(pipeline.status(), LifecycleState.CREATED)
        pipeline.initialize()
        self.assertEqual(pipeline.status(), LifecycleState.INITIALIZING)
        pipeline.start()
        self.assertEqual(pipeline.status(), LifecycleState.RUNNING)
        pipeline.stop()
        self.assertEqual(pipeline.status(), LifecycleState.STOPPED)


# -- run() validation -----------------------------------------------------


class RunValidationTests(unittest.TestCase):
    def test_run_before_started_raises_pipeline_error(self):
        pipeline = CognitivePipeline(planner=_real_planner())
        with self.assertRaises(PipelineError):
            pipeline.run(PipelineRequest(conversation=ConversationSession()))

    def test_run_after_stopped_raises_pipeline_error(self):
        pipeline = _started_pipeline()
        pipeline.stop()
        with self.assertRaises(PipelineError):
            pipeline.run(PipelineRequest(conversation=ConversationSession()))

    def test_run_rejects_non_pipeline_request(self):
        pipeline = _started_pipeline()
        with self.assertRaises(InvalidPipelineRequestError):
            pipeline.run("not a request")

    def test_run_rejects_none(self):
        pipeline = _started_pipeline()
        with self.assertRaises(InvalidPipelineRequestError):
            pipeline.run(None)

    def test_run_rejects_request_with_non_conversation_session(self):
        pipeline = _started_pipeline()

        # PipelineRequest performs no field validation of its own (see
        # request.py's "No Validation Here" note) - constructing one
        # with a bogus `conversation` is legal at the dataclass level,
        # so this exercises run()'s *second* isinstance check
        # specifically, distinct from the "not a PipelineRequest at
        # all" case covered above.
        bad_request = PipelineRequest(conversation="not a conversation session")

        with self.assertRaises(InvalidPipelineRequestError):
            pipeline.run(bad_request)


# -- empty and populated conversations -------------------------------------


class EmptyConversationTests(unittest.TestCase):
    def test_empty_conversation_produces_a_result(self):
        pipeline = _started_pipeline()
        conversation = ConversationSession()
        self.assertEqual(conversation.messages, ())

        result = pipeline.run(PipelineRequest(conversation=conversation))

        self.assertIs(result.conversation, conversation)
        self.assertEqual(result.cognitive_context.conversation_id, conversation.id)
        self.assertEqual(result.planning_session.goals, ())
        self.assertEqual(result.planning_session.constraints, ())
        self.assertEqual(result.plan.steps, ())


class PopulatedConversationTests(unittest.TestCase):
    def test_populated_conversation_is_carried_through_unchanged(self):
        pipeline = _started_pipeline()
        conversation = ConversationSession(
            messages=[
                ConversationMessage(role=ConversationRole.USER, content="hello"),
                ConversationMessage(role=ConversationRole.ASSISTANT, content="hi there"),
            ]
        )

        result = pipeline.run(PipelineRequest(conversation=conversation))

        self.assertEqual(len(result.conversation.messages), 2)
        self.assertEqual(result.conversation.messages[0].content, "hello")
        self.assertEqual(result.cognitive_context.conversation_id, conversation.id)


# -- orchestration order / planner invocation ------------------------------


class OrchestrationOrderTests(unittest.TestCase):
    def test_cognitive_context_is_built_before_planning_session(self):
        recording = RecordingPlanner(plan_to_return=None)
        pipeline = _started_pipeline(planner=recording)
        conversation = ConversationSession()

        result = pipeline.run(PipelineRequest(conversation=conversation))

        # The PlanningSession handed to plan_session() must already
        # embed the exact CognitiveContext returned in the result -
        # proof the context was built first and passed forward, not
        # built in parallel or after.
        self.assertEqual(len(recording.calls), 1)
        self.assertIs(recording.calls[0].cognitive_context, result.cognitive_context)

    def test_planner_plan_session_invoked_exactly_once(self):
        recording = RecordingPlanner(plan_to_return=None)
        pipeline = _started_pipeline(planner=recording)

        pipeline.run(PipelineRequest(conversation=ConversationSession()))

        self.assertEqual(len(recording.calls), 1)

    def test_result_plan_is_exactly_what_planner_returned(self):
        sentinel_plan = object()
        recording = RecordingPlanner(plan_to_return=sentinel_plan)
        pipeline = _started_pipeline(planner=recording)

        result = pipeline.run(PipelineRequest(conversation=ConversationSession()))

        self.assertIs(result.plan, sentinel_plan)

    def test_multiple_runs_each_invoke_planner_independently(self):
        recording = RecordingPlanner(plan_to_return=None)
        pipeline = _started_pipeline(planner=recording)

        pipeline.run(PipelineRequest(conversation=ConversationSession()))
        pipeline.run(PipelineRequest(conversation=ConversationSession()))

        self.assertEqual(len(recording.calls), 2)
        self.assertIsNot(recording.calls[0], recording.calls[1])


# -- immutable results / pipeline output -----------------------------------


class ImmutableResultsTests(unittest.TestCase):
    def test_result_fields_cannot_be_reassigned(self):
        pipeline = _started_pipeline()
        result = pipeline.run(PipelineRequest(conversation=ConversationSession()))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            result.plan = None

    def test_request_conversation_is_never_mutated(self):
        pipeline = _started_pipeline()
        conversation = ConversationSession()
        before = dataclasses.replace(conversation)

        pipeline.run(PipelineRequest(conversation=conversation))

        self.assertEqual(conversation, before)

    def test_request_itself_is_never_mutated(self):
        pipeline = _started_pipeline()
        request = PipelineRequest(conversation=ConversationSession(), metadata={"k": "v"})
        before = dataclasses.replace(request)

        pipeline.run(request)

        self.assertEqual(request, before)


class PipelineOutputTests(unittest.TestCase):
    def test_output_contains_every_documented_field(self):
        pipeline = _started_pipeline()
        result = pipeline.run(PipelineRequest(conversation=ConversationSession()))
        self.assertTrue(result.pipeline_id)
        self.assertIsNotNone(result.conversation)
        self.assertIsNotNone(result.cognitive_context)
        self.assertIsNotNone(result.planning_session)
        self.assertIsNotNone(result.plan)
        self.assertIsInstance(dict(result.metadata), dict)

    def test_planning_session_embeds_the_same_cognitive_context_instance(self):
        pipeline = _started_pipeline()
        result = pipeline.run(PipelineRequest(conversation=ConversationSession()))
        self.assertIs(result.planning_session.cognitive_context, result.cognitive_context)


# -- dependency failures ----------------------------------------------------


class DependencyFailureTests(unittest.TestCase):
    def test_planner_failure_is_wrapped_as_pipeline_execution_error(self):
        pipeline = _started_pipeline(planner=RaisingPlanner())
        with self.assertRaises(PipelineExecutionError) as ctx:
            pipeline.run(PipelineRequest(conversation=ConversationSession()))
        self.assertIsInstance(ctx.exception.__cause__, InvalidPlanError)

    def test_no_result_returned_on_planner_failure(self):
        # The failure must propagate, not be swallowed into a
        # partial/empty PipelineResult.
        pipeline = _started_pipeline(planner=RaisingPlanner())
        with self.assertRaises(PipelineExecutionError):
            pipeline.run(PipelineRequest(conversation=ConversationSession()))


# -- metadata propagation ----------------------------------------------------


class MetadataPropagationTests(unittest.TestCase):
    def test_request_metadata_propagates_to_cognitive_context(self):
        pipeline = _started_pipeline()
        request = PipelineRequest(conversation=ConversationSession(), metadata={"foo": "bar"})
        result = pipeline.run(request)
        self.assertEqual(result.cognitive_context.metadata.extra["foo"], "bar")

    def test_request_metadata_propagates_to_planning_session(self):
        pipeline = _started_pipeline()
        request = PipelineRequest(conversation=ConversationSession(), metadata={"foo": "bar"})
        result = pipeline.run(request)
        self.assertEqual(result.planning_session.metadata.extra["foo"], "bar")

    def test_request_metadata_propagates_to_result_metadata(self):
        pipeline = _started_pipeline()
        request = PipelineRequest(conversation=ConversationSession(), metadata={"foo": "bar"})
        result = pipeline.run(request)
        self.assertEqual(result.metadata["foo"], "bar")

    def test_request_id_is_propagated_everywhere_metadata_is(self):
        pipeline = _started_pipeline()
        request = PipelineRequest(conversation=ConversationSession())
        result = pipeline.run(request)
        self.assertEqual(result.metadata["request_id"], request.request_id)
        self.assertEqual(
            result.cognitive_context.metadata.extra["request_id"], request.request_id
        )
        self.assertEqual(
            result.planning_session.metadata.extra["request_id"], request.request_id
        )

    def test_multiple_metadata_keys_all_propagate(self):
        pipeline = _started_pipeline()
        request = PipelineRequest(
            conversation=ConversationSession(), metadata={"a": 1, "b": 2, "c": "three"}
        )
        result = pipeline.run(request)
        for key, value in {"a": 1, "b": 2, "c": "three"}.items():
            self.assertEqual(result.metadata[key], value)
            self.assertEqual(result.cognitive_context.metadata.extra[key], value)
            self.assertEqual(result.planning_session.metadata.extra[key], value)

    def test_empty_metadata_still_carries_request_id_only(self):
        pipeline = _started_pipeline()
        request = PipelineRequest(conversation=ConversationSession())
        result = pipeline.run(request)
        self.assertEqual(dict(result.metadata), {"request_id": request.request_id})


if __name__ == "__main__":
    unittest.main()
