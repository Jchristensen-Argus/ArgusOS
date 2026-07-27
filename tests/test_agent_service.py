"""Unit tests for argus.agent.service.AgentService."""

import dataclasses
import logging
import unittest

from argus.agent import (
    AgentError,
    AgentExecutionError,
    AgentRequest,
    AgentService,
    AgentSession,
    InvalidAgentRequestError,
)
from argus.capability import CapabilityRegistry
from argus.conversation import ConversationMessage, ConversationRole, ConversationSession
from argus.events import InMemoryEventBus
from argus.lifecycle import IService
from argus.lifecycle.lifecycle import LifecycleState
from argus.pipeline import CognitivePipeline
from argus.planner import Planner


def _silent_logger() -> logging.Logger:
    logger = logging.getLogger("test_agent_service")
    logger.addHandler(logging.NullHandler())
    logger.propagate = False
    return logger


def _real_pipeline() -> CognitivePipeline:
    bus = InMemoryEventBus(logger=_silent_logger())
    registry = CapabilityRegistry(event_bus=bus)
    planner = Planner(event_bus=bus, capability_registry=registry)
    pipeline = CognitivePipeline(planner=planner)
    pipeline.initialize()
    pipeline.start()
    return pipeline


class RecordingPipeline:
    """A test double recording exactly what run() was called with, so
    pipeline invocation can be verified without depending on
    CognitivePipeline's own internals."""

    def __init__(self, result_to_return):
        self.calls = []
        self._result_to_return = result_to_return

    def run(self, request):
        self.calls.append(request)
        return self._result_to_return


class RaisingPipeline:
    def run(self, request):
        raise RuntimeError("synthetic failure for dependency-failure testing")


def _started_service(pipeline=None) -> AgentService:
    service = AgentService(cognitive_pipeline=pipeline or _real_pipeline())
    service.initialize()
    service.start()
    return service


# -- identity / IService ----------------------------------------------


class AgentServiceIdentityTests(unittest.TestCase):
    def test_is_an_iagentservice(self):
        from argus.agent import IAgentService

        self.assertIsInstance(AgentService(cognitive_pipeline=_real_pipeline()), IAgentService)

    def test_is_an_iservice(self):
        self.assertIsInstance(AgentService(cognitive_pipeline=_real_pipeline()), IService)

    def test_starts_in_created_state(self):
        service = AgentService(cognitive_pipeline=_real_pipeline())
        self.assertEqual(service.status(), LifecycleState.CREATED)


# -- lifecycle ----------------------------------------------------------


class AgentServiceLifecycleTests(unittest.TestCase):
    def test_initialize_transitions_to_initializing(self):
        service = AgentService(cognitive_pipeline=_real_pipeline())
        service.initialize()
        self.assertEqual(service.status(), LifecycleState.INITIALIZING)

    def test_initialize_twice_raises(self):
        service = AgentService(cognitive_pipeline=_real_pipeline())
        service.initialize()
        with self.assertRaises(AgentError):
            service.initialize()

    def test_start_requires_initializing(self):
        service = AgentService(cognitive_pipeline=_real_pipeline())
        with self.assertRaises(AgentError):
            service.start()

    def test_start_transitions_to_running(self):
        service = AgentService(cognitive_pipeline=_real_pipeline())
        service.initialize()
        service.start()
        self.assertEqual(service.status(), LifecycleState.RUNNING)

    def test_stop_requires_running(self):
        service = AgentService(cognitive_pipeline=_real_pipeline())
        with self.assertRaises(AgentError):
            service.stop()

    def test_stop_transitions_to_stopped(self):
        service = _started_service()
        service.stop()
        self.assertEqual(service.status(), LifecycleState.STOPPED)

    def test_status_reflects_current_state_throughout(self):
        service = AgentService(cognitive_pipeline=_real_pipeline())
        self.assertEqual(service.status(), LifecycleState.CREATED)
        service.initialize()
        self.assertEqual(service.status(), LifecycleState.INITIALIZING)
        service.start()
        self.assertEqual(service.status(), LifecycleState.RUNNING)
        service.stop()
        self.assertEqual(service.status(), LifecycleState.STOPPED)


# -- run() validation -----------------------------------------------------


class RunValidationTests(unittest.TestCase):
    def _request(self):
        session = AgentSession(conversation=ConversationSession())
        return AgentRequest(session=session, conversation=session.conversation)

    def test_run_before_started_raises_agent_error(self):
        service = AgentService(cognitive_pipeline=_real_pipeline())
        with self.assertRaises(AgentError):
            service.run(self._request())

    def test_run_after_stopped_raises_agent_error(self):
        service = _started_service()
        service.stop()
        with self.assertRaises(AgentError):
            service.run(self._request())

    def test_run_rejects_non_agent_request(self):
        service = _started_service()
        with self.assertRaises(InvalidAgentRequestError):
            service.run("not a request")

    def test_run_rejects_none(self):
        service = _started_service()
        with self.assertRaises(InvalidAgentRequestError):
            service.run(None)

    def test_run_rejects_request_with_non_agent_session(self):
        service = _started_service()
        # AgentRequest performs no field validation of its own (see
        # request.py's "No Validation Here" note) - constructing one
        # with a bogus `session` is legal at the dataclass level.
        bad_request = AgentRequest(
            session="not a session", conversation=ConversationSession()
        )
        with self.assertRaises(InvalidAgentRequestError):
            service.run(bad_request)

    def test_run_rejects_request_with_non_conversation_session(self):
        service = _started_service()
        session = AgentSession(conversation=ConversationSession())
        bad_request = AgentRequest(session=session, conversation="not a conversation")
        with self.assertRaises(InvalidAgentRequestError):
            service.run(bad_request)


# -- empty and populated sessions -------------------------------------


class EmptySessionTests(unittest.TestCase):
    def test_empty_session_produces_a_response(self):
        service = _started_service()
        session = AgentSession(conversation=ConversationSession())
        self.assertEqual(session.conversation.messages, ())
        request = AgentRequest(session=session, conversation=session.conversation)

        response = service.run(request)

        self.assertIs(response.session, session)
        self.assertEqual(response.pipeline_result.plan.steps, ())


class PopulatedSessionTests(unittest.TestCase):
    def test_populated_session_is_carried_through_unchanged(self):
        service = _started_service()
        conversation = ConversationSession(
            messages=[
                ConversationMessage(role=ConversationRole.USER, content="hello"),
                ConversationMessage(role=ConversationRole.ASSISTANT, content="hi there"),
            ]
        )
        session = AgentSession(conversation=conversation)
        request = AgentRequest(session=session, conversation=conversation)

        response = service.run(request)

        self.assertEqual(len(response.pipeline_result.conversation.messages), 2)
        self.assertEqual(response.pipeline_result.conversation.messages[0].content, "hello")


# -- pipeline invocation ----------------------------------------------------


class PipelineInvocationTests(unittest.TestCase):
    def test_pipeline_run_invoked_exactly_once(self):
        recording = RecordingPipeline(result_to_return=None)
        service = _started_service(pipeline=recording)
        session = AgentSession(conversation=ConversationSession())

        service.run(AgentRequest(session=session, conversation=session.conversation))

        self.assertEqual(len(recording.calls), 1)

    def test_pipeline_receives_the_requests_own_conversation(self):
        recording = RecordingPipeline(result_to_return=None)
        service = _started_service(pipeline=recording)
        conversation = ConversationSession()
        session = AgentSession(conversation=conversation)

        service.run(AgentRequest(session=session, conversation=conversation))

        self.assertIs(recording.calls[0].conversation, conversation)

    def test_response_pipeline_result_is_exactly_what_pipeline_returned(self):
        sentinel_result = object()
        recording = RecordingPipeline(result_to_return=sentinel_result)
        service = _started_service(pipeline=recording)
        session = AgentSession(conversation=ConversationSession())

        response = service.run(
            AgentRequest(session=session, conversation=session.conversation)
        )

        self.assertIs(response.pipeline_result, sentinel_result)

    def test_multiple_runs_each_invoke_pipeline_independently(self):
        recording = RecordingPipeline(result_to_return=None)
        service = _started_service(pipeline=recording)
        session = AgentSession(conversation=ConversationSession())

        service.run(AgentRequest(session=session, conversation=session.conversation))
        service.run(AgentRequest(session=session, conversation=session.conversation))

        self.assertEqual(len(recording.calls), 2)
        self.assertIsNot(recording.calls[0], recording.calls[1])


# -- response wrapping -----------------------------------------------------


class ResponseWrappingTests(unittest.TestCase):
    def test_response_wraps_pipeline_result_unmodified(self):
        service = _started_service()
        session = AgentSession(conversation=ConversationSession())
        response = service.run(
            AgentRequest(session=session, conversation=session.conversation)
        )
        self.assertIsNotNone(response.pipeline_result)
        self.assertIsNotNone(response.pipeline_result.plan)
        self.assertIsNotNone(response.pipeline_result.cognitive_context)
        self.assertIsNotNone(response.pipeline_result.planning_session)

    def test_response_contains_the_requests_own_session(self):
        service = _started_service()
        session = AgentSession(conversation=ConversationSession())
        response = service.run(
            AgentRequest(session=session, conversation=session.conversation)
        )
        self.assertIs(response.session, session)

    def test_response_has_no_natural_language_or_execution_fields(self):
        service = _started_service()
        session = AgentSession(conversation=ConversationSession())
        response = service.run(
            AgentRequest(session=session, conversation=session.conversation)
        )
        field_names = {f.name for f in dataclasses.fields(response)}
        self.assertEqual(
            field_names, {"session", "pipeline_result", "response_id", "metadata"}
        )


# -- immutable objects -------------------------------------------------------


class ImmutableObjectsTests(unittest.TestCase):
    def test_response_fields_cannot_be_reassigned(self):
        service = _started_service()
        session = AgentSession(conversation=ConversationSession())
        response = service.run(
            AgentRequest(session=session, conversation=session.conversation)
        )
        with self.assertRaises(dataclasses.FrozenInstanceError):
            response.pipeline_result = None

    def test_request_is_never_mutated(self):
        service = _started_service()
        session = AgentSession(conversation=ConversationSession())
        request = AgentRequest(
            session=session, conversation=session.conversation, metadata={"k": "v"}
        )
        before = dataclasses.replace(request)

        service.run(request)

        self.assertEqual(request, before)

    def test_session_is_never_mutated(self):
        service = _started_service()
        session = AgentSession(conversation=ConversationSession())
        before = dataclasses.replace(session)

        service.run(AgentRequest(session=session, conversation=session.conversation))

        self.assertEqual(session, before)


# -- dependency failures ----------------------------------------------------


class DependencyFailureTests(unittest.TestCase):
    def test_pipeline_failure_is_wrapped_as_agent_execution_error(self):
        service = _started_service(pipeline=RaisingPipeline())
        session = AgentSession(conversation=ConversationSession())
        with self.assertRaises(AgentExecutionError) as ctx:
            service.run(AgentRequest(session=session, conversation=session.conversation))
        self.assertIsInstance(ctx.exception.__cause__, RuntimeError)

    def test_no_response_returned_on_pipeline_failure(self):
        service = _started_service(pipeline=RaisingPipeline())
        session = AgentSession(conversation=ConversationSession())
        with self.assertRaises(AgentExecutionError):
            service.run(AgentRequest(session=session, conversation=session.conversation))


# -- metadata propagation ----------------------------------------------------


class MetadataPropagationTests(unittest.TestCase):
    def test_request_metadata_propagates_to_response_metadata(self):
        service = _started_service()
        session = AgentSession(conversation=ConversationSession())
        request = AgentRequest(
            session=session, conversation=session.conversation, metadata={"foo": "bar"}
        )
        response = service.run(request)
        self.assertEqual(response.metadata["foo"], "bar")

    def test_request_metadata_propagates_through_to_pipeline_result_metadata(self):
        service = _started_service()
        session = AgentSession(conversation=ConversationSession())
        request = AgentRequest(
            session=session, conversation=session.conversation, metadata={"foo": "bar"}
        )
        response = service.run(request)
        self.assertEqual(response.pipeline_result.metadata["foo"], "bar")

    def test_request_metadata_propagates_through_to_cognitive_context(self):
        service = _started_service()
        session = AgentSession(conversation=ConversationSession())
        request = AgentRequest(
            session=session, conversation=session.conversation, metadata={"foo": "bar"}
        )
        response = service.run(request)
        self.assertEqual(
            response.pipeline_result.cognitive_context.metadata.extra["foo"], "bar"
        )

    def test_agent_request_id_and_session_id_are_propagated(self):
        service = _started_service()
        session = AgentSession(conversation=ConversationSession())
        request = AgentRequest(session=session, conversation=session.conversation)
        response = service.run(request)
        self.assertEqual(response.metadata["agent_request_id"], request.request_id)
        self.assertEqual(response.metadata["agent_session_id"], session.session_id)

    def test_multiple_metadata_keys_all_propagate(self):
        service = _started_service()
        session = AgentSession(conversation=ConversationSession())
        request = AgentRequest(
            session=session,
            conversation=session.conversation,
            metadata={"a": 1, "b": 2, "c": "three"},
        )
        response = service.run(request)
        for key, value in {"a": 1, "b": 2, "c": "three"}.items():
            self.assertEqual(response.metadata[key], value)
            self.assertEqual(response.pipeline_result.metadata[key], value)

    def test_empty_metadata_still_carries_traceability_keys_only(self):
        service = _started_service()
        session = AgentSession(conversation=ConversationSession())
        request = AgentRequest(session=session, conversation=session.conversation)
        response = service.run(request)
        self.assertEqual(
            dict(response.metadata),
            {
                "agent_request_id": request.request_id,
                "agent_session_id": session.session_id,
            },
        )


if __name__ == "__main__":
    unittest.main()
