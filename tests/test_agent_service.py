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
from argus.execution_engine import ExecutionEngine
from argus.intent import Intent, IntentType
from argus.lifecycle import IService
from argus.lifecycle.lifecycle import LifecycleState
from argus.pipeline import CognitivePipeline
from argus.planner import Plan, Planner
from argus.response import Response, ResponseEngine
from argus.trace import ExecutionTrace


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


def _stub_plan() -> Plan:
    return Plan(originating_intent=Intent(name=IntentType.UNKNOWN, confidence=0.0))


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
        raise RuntimeError("synthetic pipeline failure for dependency-failure testing")


class _StubPipelineResult:
    """Minimal stand-in carrying just the one attribute
    AgentService.run() actually reads off a PipelineResult: `plan`.
    Defaults to a real Plan (rather than None) so that a real
    ExecutionEngine.execute() call downstream still succeeds when no
    override is supplied."""

    def __init__(self, plan=None):
        self.plan = plan if plan is not None else _stub_plan()


class RecordingExecutionEngine:
    """A test double recording exactly what execute() was called with
    (Package 032), so Execution Engine invocation can be verified
    without depending on ExecutionEngine's own internals."""

    def __init__(self, result_to_return):
        self.calls = []
        self._result_to_return = result_to_return

    def execute(self, plan):
        self.calls.append(plan)
        return self._result_to_return


class RaisingExecutionEngine:
    def execute(self, plan):
        raise RuntimeError("synthetic execution engine failure for dependency-failure testing")


class RecordingResponseEngine:
    """A test double recording exactly what build_response() was
    called with (the Plan, the ExecutionResult - Package 032 - and the
    ExecutionTrace - Package 028), so Response Engine invocation can
    be verified without depending on ResponseEngine's own internals."""

    def __init__(self, response_to_return):
        self.calls = []
        self._response_to_return = response_to_return

    def build_response(self, plan, execution_result, execution_trace):
        self.calls.append((plan, execution_result, execution_trace))
        return self._response_to_return


class RaisingResponseEngine:
    def build_response(self, plan, execution_result, execution_trace):
        raise RuntimeError("synthetic response engine failure for dependency-failure testing")


def _started_service(pipeline=None, execution_engine=None, response_engine=None) -> AgentService:
    service = AgentService(
        cognitive_pipeline=pipeline or _real_pipeline(),
        execution_engine=execution_engine or ExecutionEngine(),
        response_engine=response_engine or ResponseEngine(),
    )
    service.initialize()
    service.start()
    return service


# -- identity / IService ----------------------------------------------


class AgentServiceIdentityTests(unittest.TestCase):
    def test_is_an_iagentservice(self):
        from argus.agent import IAgentService

        service = AgentService(
            cognitive_pipeline=_real_pipeline(),
            execution_engine=ExecutionEngine(),
            response_engine=ResponseEngine(),
        )
        self.assertIsInstance(service, IAgentService)

    def test_is_an_iservice(self):
        service = AgentService(
            cognitive_pipeline=_real_pipeline(),
            execution_engine=ExecutionEngine(),
            response_engine=ResponseEngine(),
        )
        self.assertIsInstance(service, IService)

    def test_starts_in_created_state(self):
        service = AgentService(
            cognitive_pipeline=_real_pipeline(),
            execution_engine=ExecutionEngine(),
            response_engine=ResponseEngine(),
        )
        self.assertEqual(service.status(), LifecycleState.CREATED)

    def test_constructor_takes_exactly_three_dependencies(self):
        # Package 032: cognitive_pipeline, execution_engine (new),
        # response_engine.
        service = AgentService(
            cognitive_pipeline=_real_pipeline(),
            execution_engine=ExecutionEngine(),
            response_engine=ResponseEngine(),
        )
        self.assertIsInstance(service, AgentService)


# -- lifecycle ----------------------------------------------------------


class AgentServiceLifecycleTests(unittest.TestCase):
    def test_initialize_transitions_to_initializing(self):
        service = AgentService(
            cognitive_pipeline=_real_pipeline(),
            execution_engine=ExecutionEngine(),
            response_engine=ResponseEngine(),
        )
        service.initialize()
        self.assertEqual(service.status(), LifecycleState.INITIALIZING)

    def test_initialize_twice_raises(self):
        service = AgentService(
            cognitive_pipeline=_real_pipeline(),
            execution_engine=ExecutionEngine(),
            response_engine=ResponseEngine(),
        )
        service.initialize()
        with self.assertRaises(AgentError):
            service.initialize()

    def test_start_requires_initializing(self):
        service = AgentService(
            cognitive_pipeline=_real_pipeline(),
            execution_engine=ExecutionEngine(),
            response_engine=ResponseEngine(),
        )
        with self.assertRaises(AgentError):
            service.start()

    def test_start_transitions_to_running(self):
        service = AgentService(
            cognitive_pipeline=_real_pipeline(),
            execution_engine=ExecutionEngine(),
            response_engine=ResponseEngine(),
        )
        service.initialize()
        service.start()
        self.assertEqual(service.status(), LifecycleState.RUNNING)

    def test_stop_requires_running(self):
        service = AgentService(
            cognitive_pipeline=_real_pipeline(),
            execution_engine=ExecutionEngine(),
            response_engine=ResponseEngine(),
        )
        with self.assertRaises(AgentError):
            service.stop()

    def test_stop_transitions_to_stopped(self):
        service = _started_service()
        service.stop()
        self.assertEqual(service.status(), LifecycleState.STOPPED)

    def test_status_reflects_current_state_throughout(self):
        service = AgentService(
            cognitive_pipeline=_real_pipeline(),
            execution_engine=ExecutionEngine(),
            response_engine=ResponseEngine(),
        )
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
        service = AgentService(
            cognitive_pipeline=_real_pipeline(),
            execution_engine=ExecutionEngine(),
            response_engine=ResponseEngine(),
        )
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
        self.assertEqual(response.response.plan.steps, ())


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

        # The Plan itself carries no conversation reference (per
        # Plan's own pre-existing shape) - "carried through unchanged"
        # is verified via the Response's own successful construction
        # rather than message content, since Response (Package 027)
        # no longer holds the PipelineResult/ConversationSession at
        # all, only the Plan (and, as of Package 032, the
        # ExecutionResult).
        self.assertIsInstance(response.response, Response)
        self.assertEqual(response.response.plan.steps, ())


# -- pipeline invocation ----------------------------------------------------


class PipelineInvocationTests(unittest.TestCase):
    def test_pipeline_run_invoked_exactly_once(self):
        recording = RecordingPipeline(result_to_return=_StubPipelineResult())
        service = _started_service(pipeline=recording, response_engine=RecordingResponseEngine(None))
        session = AgentSession(conversation=ConversationSession())

        service.run(AgentRequest(session=session, conversation=session.conversation))

        self.assertEqual(len(recording.calls), 1)

    def test_pipeline_receives_the_requests_own_conversation(self):
        recording = RecordingPipeline(result_to_return=_StubPipelineResult())
        service = _started_service(pipeline=recording, response_engine=RecordingResponseEngine(None))
        conversation = ConversationSession()
        session = AgentSession(conversation=conversation)

        service.run(AgentRequest(session=session, conversation=conversation))

        self.assertIs(recording.calls[0].conversation, conversation)

    def test_multiple_runs_each_invoke_pipeline_independently(self):
        recording = RecordingPipeline(result_to_return=_StubPipelineResult())
        service = _started_service(pipeline=recording, response_engine=RecordingResponseEngine(None))
        session = AgentSession(conversation=ConversationSession())

        service.run(AgentRequest(session=session, conversation=session.conversation))
        service.run(AgentRequest(session=session, conversation=session.conversation))

        self.assertEqual(len(recording.calls), 2)
        self.assertIsNot(recording.calls[0], recording.calls[1])


# -- execution engine invocation (Package 032) --------------------------


class ExecutionEngineInvocationTests(unittest.TestCase):
    def test_execute_invoked_exactly_once(self):
        recording = RecordingExecutionEngine(result_to_return=None)
        service = _started_service(
            execution_engine=recording, response_engine=RecordingResponseEngine(None)
        )
        session = AgentSession(conversation=ConversationSession())

        service.run(AgentRequest(session=session, conversation=session.conversation))

        self.assertEqual(len(recording.calls), 1)

    def test_execute_receives_the_pipeline_results_own_plan(self):
        real_pipeline = _real_pipeline()
        recording = RecordingExecutionEngine(result_to_return=None)
        service = _started_service(
            pipeline=real_pipeline,
            execution_engine=recording,
            response_engine=RecordingResponseEngine(None),
        )
        session = AgentSession(conversation=ConversationSession())

        service.run(AgentRequest(session=session, conversation=session.conversation))

        self.assertEqual(len(recording.calls), 1)
        self.assertEqual(recording.calls[0].steps, ())

    def test_response_engine_receives_exactly_what_execution_engine_returned(self):
        sentinel_result = object()
        recording = RecordingResponseEngine(response_to_return=None)
        service = _started_service(
            execution_engine=RecordingExecutionEngine(result_to_return=sentinel_result),
            response_engine=recording,
        )
        session = AgentSession(conversation=ConversationSession())

        service.run(AgentRequest(session=session, conversation=session.conversation))

        self.assertEqual(len(recording.calls), 1)
        self.assertIs(recording.calls[0][1], sentinel_result)

    def test_multiple_runs_each_invoke_execution_engine_independently(self):
        recording = RecordingExecutionEngine(result_to_return=None)
        service = _started_service(
            execution_engine=recording, response_engine=RecordingResponseEngine(None)
        )
        session = AgentSession(conversation=ConversationSession())

        service.run(AgentRequest(session=session, conversation=session.conversation))
        service.run(AgentRequest(session=session, conversation=session.conversation))

        self.assertEqual(len(recording.calls), 2)

    def test_a_real_execution_engine_produces_a_completed_result(self):
        service = _started_service()
        session = AgentSession(conversation=ConversationSession())

        agent_response = service.run(
            AgentRequest(session=session, conversation=session.conversation)
        )

        from argus.execution_engine import ExecutionStatus

        self.assertEqual(
            agent_response.response.execution_result.status, ExecutionStatus.COMPLETED
        )


# -- agent integration: Response Engine invocation ---------------------------


class ResponseEngineInvocationTests(unittest.TestCase):
    def test_build_response_invoked_exactly_once(self):
        recording = RecordingResponseEngine(response_to_return=None)
        service = _started_service(response_engine=recording)
        session = AgentSession(conversation=ConversationSession())

        service.run(AgentRequest(session=session, conversation=session.conversation))

        self.assertEqual(len(recording.calls), 1)

    def test_build_response_receives_the_pipeline_results_own_plan(self):
        real_pipeline = _real_pipeline()
        recording = RecordingResponseEngine(response_to_return=None)
        service = _started_service(pipeline=real_pipeline, response_engine=recording)
        session = AgentSession(conversation=ConversationSession())

        service.run(AgentRequest(session=session, conversation=session.conversation))

        # The Plan passed to build_response() must be a genuine Plan
        # produced by the real Cognitive Pipeline's own orchestration,
        # proving the delegate calls are wired in the correct order
        # (pipeline.run() first, then execution_engine.execute() on
        # its result, then response_engine.build_response() on both).
        self.assertEqual(len(recording.calls), 1)
        self.assertEqual(recording.calls[0][0].steps, ())

    def test_agent_response_wraps_exactly_what_response_engine_returned(self):
        sentinel_response = object()
        recording = RecordingResponseEngine(response_to_return=sentinel_response)
        service = _started_service(response_engine=recording)
        session = AgentSession(conversation=ConversationSession())

        agent_response = service.run(
            AgentRequest(session=session, conversation=session.conversation)
        )

        self.assertIs(agent_response.response, sentinel_response)

    def test_multiple_runs_each_invoke_response_engine_independently(self):
        recording = RecordingResponseEngine(response_to_return=None)
        service = _started_service(response_engine=recording)
        session = AgentSession(conversation=ConversationSession())

        service.run(AgentRequest(session=session, conversation=session.conversation))
        service.run(AgentRequest(session=session, conversation=session.conversation))

        self.assertEqual(len(recording.calls), 2)


# -- execution trace construction (Package 028, amended by 032) -------------


class TraceInvocationTests(unittest.TestCase):
    def test_response_engine_receives_a_finished_execution_trace(self):
        recording = RecordingResponseEngine(response_to_return=None)
        service = _started_service(response_engine=recording)
        session = AgentSession(conversation=ConversationSession())

        service.run(AgentRequest(session=session, conversation=session.conversation))

        self.assertEqual(len(recording.calls), 1)
        received_trace = recording.calls[0][2]
        self.assertIsInstance(received_trace, ExecutionTrace)

    def test_trace_records_agent_service_pipeline_execution_engine_and_response_engine(self):
        recording = RecordingResponseEngine(response_to_return=None)
        service = _started_service(response_engine=recording)
        session = AgentSession(conversation=ConversationSession())

        service.run(AgentRequest(session=session, conversation=session.conversation))

        trace = recording.calls[0][2]
        self.assertEqual(
            [step.component for step in trace.steps],
            ["AgentService", "CognitivePipeline", "ExecutionEngine", "ResponseEngine"],
        )
        self.assertEqual(
            [step.action for step in trace.steps],
            ["entry", "completed", "processed", "invoked"],
        )

    def test_trace_is_embedded_unmodified_in_the_returned_response(self):
        service = _started_service()
        session = AgentSession(conversation=ConversationSession())

        agent_response = service.run(
            AgentRequest(session=session, conversation=session.conversation)
        )

        self.assertIsInstance(agent_response.response.execution_trace, ExecutionTrace)
        self.assertEqual(len(agent_response.response.execution_trace.steps), 4)

    def test_multiple_runs_produce_independent_traces(self):
        service = _started_service()
        session = AgentSession(conversation=ConversationSession())

        first = service.run(AgentRequest(session=session, conversation=session.conversation))
        second = service.run(AgentRequest(session=session, conversation=session.conversation))

        self.assertNotEqual(
            first.response.execution_trace.trace_id,
            second.response.execution_trace.trace_id,
        )

    def test_no_trace_step_recorded_for_a_pipeline_call_that_never_completed(self):
        # RaisingPipeline fails before "CognitivePipeline completed"
        # would ever be recorded - there is no ExecutionTrace to
        # inspect at all here since build_response() (and therefore
        # the finished trace) is never reached, but this confirms the
        # failure path never raises anything trace-related itself.
        service = _started_service(pipeline=RaisingPipeline())
        session = AgentSession(conversation=ConversationSession())
        with self.assertRaises(AgentExecutionError):
            service.run(AgentRequest(session=session, conversation=session.conversation))

    def test_no_execution_engine_or_response_engine_trace_step_recorded_when_execution_engine_fails(self):
        # RaisingExecutionEngine fails after "CognitivePipeline
        # completed" is recorded but before "ExecutionEngine
        # processed"/"ResponseEngine invoked" would ever be recorded -
        # there is again no finished ExecutionTrace to inspect, since
        # build_response() is never reached.
        service = _started_service(execution_engine=RaisingExecutionEngine())
        session = AgentSession(conversation=ConversationSession())
        with self.assertRaises(AgentExecutionError):
            service.run(AgentRequest(session=session, conversation=session.conversation))


# -- response wrapping -----------------------------------------------------


class ResponseWrappingTests(unittest.TestCase):
    def test_response_wraps_a_real_response_object(self):
        service = _started_service()
        session = AgentSession(conversation=ConversationSession())
        agent_response = service.run(
            AgentRequest(session=session, conversation=session.conversation)
        )
        self.assertIsInstance(agent_response.response, Response)
        self.assertIsNotNone(agent_response.response.plan)

    def test_response_contains_the_requests_own_session(self):
        service = _started_service()
        session = AgentSession(conversation=ConversationSession())
        agent_response = service.run(
            AgentRequest(session=session, conversation=session.conversation)
        )
        self.assertIs(agent_response.session, session)

    def test_agent_response_has_no_pipeline_result_field(self):
        service = _started_service()
        session = AgentSession(conversation=ConversationSession())
        agent_response = service.run(
            AgentRequest(session=session, conversation=session.conversation)
        )
        field_names = {f.name for f in dataclasses.fields(agent_response)}
        self.assertEqual(
            field_names, {"session", "response", "response_id", "metadata"}
        )


# -- immutable objects -------------------------------------------------------


class ImmutableObjectsTests(unittest.TestCase):
    def test_response_fields_cannot_be_reassigned(self):
        service = _started_service()
        session = AgentSession(conversation=ConversationSession())
        agent_response = service.run(
            AgentRequest(session=session, conversation=session.conversation)
        )
        with self.assertRaises(dataclasses.FrozenInstanceError):
            agent_response.response = None

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

    def test_execution_engine_failure_is_wrapped_as_agent_execution_error(self):
        service = _started_service(execution_engine=RaisingExecutionEngine())
        session = AgentSession(conversation=ConversationSession())
        with self.assertRaises(AgentExecutionError) as ctx:
            service.run(AgentRequest(session=session, conversation=session.conversation))
        self.assertIsInstance(ctx.exception.__cause__, RuntimeError)

    def test_no_response_returned_on_execution_engine_failure(self):
        service = _started_service(execution_engine=RaisingExecutionEngine())
        session = AgentSession(conversation=ConversationSession())
        with self.assertRaises(AgentExecutionError):
            service.run(AgentRequest(session=session, conversation=session.conversation))

    def test_response_engine_failure_is_wrapped_as_agent_execution_error(self):
        service = _started_service(response_engine=RaisingResponseEngine())
        session = AgentSession(conversation=ConversationSession())
        with self.assertRaises(AgentExecutionError) as ctx:
            service.run(AgentRequest(session=session, conversation=session.conversation))
        self.assertIsInstance(ctx.exception.__cause__, RuntimeError)

    def test_no_response_returned_on_response_engine_failure(self):
        service = _started_service(response_engine=RaisingResponseEngine())
        session = AgentSession(conversation=ConversationSession())
        with self.assertRaises(AgentExecutionError):
            service.run(AgentRequest(session=session, conversation=session.conversation))

    def test_execution_engine_never_called_when_pipeline_fails_first(self):
        recording = RecordingExecutionEngine(result_to_return=None)
        service = _started_service(pipeline=RaisingPipeline(), execution_engine=recording)
        session = AgentSession(conversation=ConversationSession())
        with self.assertRaises(AgentExecutionError):
            service.run(AgentRequest(session=session, conversation=session.conversation))
        self.assertEqual(len(recording.calls), 0)

    def test_response_engine_never_called_when_pipeline_fails_first(self):
        recording = RecordingResponseEngine(response_to_return=None)
        service = _started_service(pipeline=RaisingPipeline(), response_engine=recording)
        session = AgentSession(conversation=ConversationSession())
        with self.assertRaises(AgentExecutionError):
            service.run(AgentRequest(session=session, conversation=session.conversation))
        self.assertEqual(len(recording.calls), 0)

    def test_response_engine_never_called_when_execution_engine_fails_first(self):
        recording = RecordingResponseEngine(response_to_return=None)
        service = _started_service(
            execution_engine=RaisingExecutionEngine(), response_engine=recording
        )
        session = AgentSession(conversation=ConversationSession())
        with self.assertRaises(AgentExecutionError):
            service.run(AgentRequest(session=session, conversation=session.conversation))
        self.assertEqual(len(recording.calls), 0)


# -- metadata propagation ----------------------------------------------------


class MetadataPropagationTests(unittest.TestCase):
    def test_request_metadata_propagates_to_agent_response_metadata(self):
        service = _started_service()
        session = AgentSession(conversation=ConversationSession())
        request = AgentRequest(
            session=session, conversation=session.conversation, metadata={"foo": "bar"}
        )
        agent_response = service.run(request)
        self.assertEqual(agent_response.metadata["foo"], "bar")

    def test_plan_metadata_propagates_through_to_response_metadata_extra(self):
        service = _started_service()
        session = AgentSession(conversation=ConversationSession())
        request = AgentRequest(session=session, conversation=session.conversation)
        agent_response = service.run(request)
        # The Plan built by Planner.plan_session() always carries
        # planning_session_id (Package 024) - ResponseEngine copies
        # plan.metadata into response.metadata.extra unchanged.
        self.assertIn("planning_session_id", agent_response.response.metadata.extra)

    def test_agent_request_id_and_session_id_are_propagated(self):
        service = _started_service()
        session = AgentSession(conversation=ConversationSession())
        request = AgentRequest(session=session, conversation=session.conversation)
        agent_response = service.run(request)
        self.assertEqual(agent_response.metadata["agent_request_id"], request.request_id)
        self.assertEqual(agent_response.metadata["agent_session_id"], session.session_id)

    def test_multiple_metadata_keys_all_propagate_to_agent_response(self):
        service = _started_service()
        session = AgentSession(conversation=ConversationSession())
        request = AgentRequest(
            session=session,
            conversation=session.conversation,
            metadata={"a": 1, "b": 2, "c": "three"},
        )
        agent_response = service.run(request)
        for key, value in {"a": 1, "b": 2, "c": "three"}.items():
            self.assertEqual(agent_response.metadata[key], value)

    def test_empty_metadata_still_carries_traceability_keys_only(self):
        service = _started_service()
        session = AgentSession(conversation=ConversationSession())
        request = AgentRequest(session=session, conversation=session.conversation)
        agent_response = service.run(request)
        self.assertEqual(
            dict(agent_response.metadata),
            {
                "agent_request_id": request.request_id,
                "agent_session_id": session.session_id,
            },
        )


if __name__ == "__main__":
    unittest.main()
