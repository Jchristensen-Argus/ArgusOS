"""Unit tests for argus.agent.response.AgentResponse."""

import dataclasses
import unittest

from argus.agent import AgentResponse, AgentSession
from argus.context import ContextBuilder
from argus.conversation import ConversationSession
from argus.intent import Intent, IntentType
from argus.planner import Plan
from argus.planning import PlanningSessionBuilder
from argus.pipeline import PipelineResult


def _plan():
    return Plan(originating_intent=Intent(name=IntentType.UNKNOWN, confidence=0.0))


def _cognitive_context():
    return ContextBuilder().build()


def _planning_session(cognitive_context):
    return PlanningSessionBuilder().with_context(cognitive_context).build()


def _pipeline_result(conversation):
    cognitive_context = _cognitive_context()
    return PipelineResult(
        conversation=conversation,
        cognitive_context=cognitive_context,
        planning_session=_planning_session(cognitive_context),
        plan=_plan(),
    )


class DefaultsTests(unittest.TestCase):
    def test_defaults(self):
        conversation = ConversationSession()
        session = AgentSession(conversation=conversation)
        pipeline_result = _pipeline_result(conversation)
        response = AgentResponse(session=session, pipeline_result=pipeline_result)
        self.assertIs(response.session, session)
        self.assertIs(response.pipeline_result, pipeline_result)
        self.assertTrue(response.response_id)
        self.assertEqual(dict(response.metadata), {})

    def test_all_fields_set(self):
        conversation = ConversationSession()
        session = AgentSession(conversation=conversation)
        pipeline_result = _pipeline_result(conversation)
        response = AgentResponse(
            session=session,
            pipeline_result=pipeline_result,
            response_id="fixed-id",
            metadata={"k": "v"},
        )
        self.assertEqual(response.response_id, "fixed-id")
        self.assertEqual(dict(response.metadata), {"k": "v"})

    def test_default_response_id_is_unique_per_instance(self):
        conversation = ConversationSession()
        session = AgentSession(conversation=conversation)
        pipeline_result = _pipeline_result(conversation)
        a = AgentResponse(session=session, pipeline_result=pipeline_result)
        b = AgentResponse(session=session, pipeline_result=pipeline_result)
        self.assertNotEqual(a.response_id, b.response_id)


class MetadataTests(unittest.TestCase):
    def test_metadata_is_wrapped_in_mappingproxytype(self):
        conversation = ConversationSession()
        session = AgentSession(conversation=conversation)
        response = AgentResponse(
            session=session, pipeline_result=_pipeline_result(conversation), metadata={"a": 1}
        )
        self.assertNotIsInstance(response.metadata, dict)
        self.assertEqual(response.metadata["a"], 1)

    def test_metadata_defensive_copy_not_shared_with_caller(self):
        conversation = ConversationSession()
        session = AgentSession(conversation=conversation)
        original = {"a": 1}
        response = AgentResponse(
            session=session, pipeline_result=_pipeline_result(conversation), metadata=original
        )
        original["a"] = 999
        self.assertEqual(response.metadata["a"], 1)

    def test_metadata_is_immutable(self):
        conversation = ConversationSession()
        session = AgentSession(conversation=conversation)
        response = AgentResponse(
            session=session, pipeline_result=_pipeline_result(conversation), metadata={"a": 1}
        )
        with self.assertRaises(TypeError):
            response.metadata["a"] = 2


class ImmutabilityTests(unittest.TestCase):
    def test_immutability(self):
        conversation = ConversationSession()
        session = AgentSession(conversation=conversation)
        response = AgentResponse(session=session, pipeline_result=_pipeline_result(conversation))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            response.pipeline_result = None


class ResponseWrappingTests(unittest.TestCase):
    def test_no_natural_language_or_execution_fields_exist(self):
        # "Do not generate natural-language responses. Do not perform
        # execution. Wrap the PipelineResult only."
        field_names = {f.name for f in dataclasses.fields(AgentResponse)}
        self.assertEqual(
            field_names, {"session", "pipeline_result", "response_id", "metadata"}
        )

    def test_pipeline_result_is_wrapped_unmodified(self):
        conversation = ConversationSession()
        session = AgentSession(conversation=conversation)
        pipeline_result = _pipeline_result(conversation)
        response = AgentResponse(session=session, pipeline_result=pipeline_result)
        self.assertIs(response.pipeline_result, pipeline_result)
        self.assertIs(response.pipeline_result.conversation, conversation)


class EqualityTests(unittest.TestCase):
    def test_equality_when_all_fields_match(self):
        conversation = ConversationSession()
        session = AgentSession(conversation=conversation)
        pipeline_result = _pipeline_result(conversation)
        a = AgentResponse(
            session=session,
            pipeline_result=pipeline_result,
            response_id="r1",
            metadata={"k": "v"},
        )
        b = AgentResponse(
            session=session,
            pipeline_result=pipeline_result,
            response_id="r1",
            metadata={"k": "v"},
        )
        self.assertEqual(a, b)

    def test_not_equal_when_response_id_differs(self):
        conversation = ConversationSession()
        session = AgentSession(conversation=conversation)
        pipeline_result = _pipeline_result(conversation)
        a = AgentResponse(session=session, pipeline_result=pipeline_result, response_id="r1")
        b = AgentResponse(session=session, pipeline_result=pipeline_result, response_id="r2")
        self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main()
