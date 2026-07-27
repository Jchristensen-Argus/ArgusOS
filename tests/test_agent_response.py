"""Unit tests for argus.agent.response.AgentResponse."""

import dataclasses
import unittest

from argus.agent import AgentResponse, AgentSession
from argus.conversation import ConversationSession
from argus.intent import Intent, IntentType
from argus.planner import Plan
from argus.response import Response
from argus.trace import TraceBuilder


def _plan():
    return Plan(originating_intent=Intent(name=IntentType.UNKNOWN, confidence=0.0))


def _response():
    trace = TraceBuilder().with_step("AgentService", "entry").build()
    return Response(plan=_plan(), execution_trace=trace)


class DefaultsTests(unittest.TestCase):
    def test_defaults(self):
        session = AgentSession(conversation=ConversationSession())
        response_obj = _response()
        agent_response = AgentResponse(session=session, response=response_obj)
        self.assertIs(agent_response.session, session)
        self.assertIs(agent_response.response, response_obj)
        self.assertTrue(agent_response.response_id)
        self.assertEqual(dict(agent_response.metadata), {})

    def test_all_fields_set(self):
        session = AgentSession(conversation=ConversationSession())
        response_obj = _response()
        agent_response = AgentResponse(
            session=session,
            response=response_obj,
            response_id="fixed-id",
            metadata={"k": "v"},
        )
        self.assertEqual(agent_response.response_id, "fixed-id")
        self.assertEqual(dict(agent_response.metadata), {"k": "v"})

    def test_default_response_id_is_unique_per_instance(self):
        session = AgentSession(conversation=ConversationSession())
        response_obj = _response()
        a = AgentResponse(session=session, response=response_obj)
        b = AgentResponse(session=session, response=response_obj)
        self.assertNotEqual(a.response_id, b.response_id)

    def test_agent_response_id_is_distinct_from_wrapped_responses_own_id(self):
        session = AgentSession(conversation=ConversationSession())
        response_obj = _response()
        agent_response = AgentResponse(session=session, response=response_obj)
        self.assertNotEqual(agent_response.response_id, response_obj.response_id)


class MetadataTests(unittest.TestCase):
    def test_metadata_is_wrapped_in_mappingproxytype(self):
        session = AgentSession(conversation=ConversationSession())
        agent_response = AgentResponse(session=session, response=_response(), metadata={"a": 1})
        self.assertNotIsInstance(agent_response.metadata, dict)
        self.assertEqual(agent_response.metadata["a"], 1)

    def test_metadata_defensive_copy_not_shared_with_caller(self):
        session = AgentSession(conversation=ConversationSession())
        original = {"a": 1}
        agent_response = AgentResponse(session=session, response=_response(), metadata=original)
        original["a"] = 999
        self.assertEqual(agent_response.metadata["a"], 1)

    def test_metadata_is_immutable(self):
        session = AgentSession(conversation=ConversationSession())
        agent_response = AgentResponse(session=session, response=_response(), metadata={"a": 1})
        with self.assertRaises(TypeError):
            agent_response.metadata["a"] = 2


class ImmutabilityTests(unittest.TestCase):
    def test_immutability(self):
        session = AgentSession(conversation=ConversationSession())
        agent_response = AgentResponse(session=session, response=_response())
        with self.assertRaises(dataclasses.FrozenInstanceError):
            agent_response.response = None


class ResponseWrappingTests(unittest.TestCase):
    def test_no_pipeline_result_field_exists(self):
        # Package 027's own "Agent Integration" amendment: AgentResponse
        # now wraps a Response, not a PipelineResult.
        field_names = {f.name for f in dataclasses.fields(AgentResponse)}
        self.assertEqual(
            field_names, {"session", "response", "response_id", "metadata"}
        )

    def test_response_is_wrapped_unmodified(self):
        session = AgentSession(conversation=ConversationSession())
        response_obj = _response()
        agent_response = AgentResponse(session=session, response=response_obj)
        self.assertIs(agent_response.response, response_obj)
        self.assertIs(agent_response.response.plan, response_obj.plan)


class EqualityTests(unittest.TestCase):
    def test_equality_when_all_fields_match(self):
        session = AgentSession(conversation=ConversationSession())
        response_obj = _response()
        a = AgentResponse(
            session=session, response=response_obj, response_id="r1", metadata={"k": "v"}
        )
        b = AgentResponse(
            session=session, response=response_obj, response_id="r1", metadata={"k": "v"}
        )
        self.assertEqual(a, b)

    def test_not_equal_when_response_id_differs(self):
        session = AgentSession(conversation=ConversationSession())
        response_obj = _response()
        a = AgentResponse(session=session, response=response_obj, response_id="r1")
        b = AgentResponse(session=session, response=response_obj, response_id="r2")
        self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main()
