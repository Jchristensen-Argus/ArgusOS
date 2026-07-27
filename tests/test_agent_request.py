"""Unit tests for argus.agent.request.AgentRequest."""

import dataclasses
import unittest

from argus.agent import AgentRequest, AgentSession
from argus.conversation import ConversationMessage, ConversationRole, ConversationSession


class DefaultsTests(unittest.TestCase):
    def test_defaults(self):
        conversation = ConversationSession()
        session = AgentSession(conversation=conversation)
        request = AgentRequest(session=session, conversation=conversation)
        self.assertIs(request.session, session)
        self.assertIs(request.conversation, conversation)
        self.assertTrue(request.request_id)
        self.assertEqual(dict(request.metadata), {})

    def test_all_fields_set(self):
        session = AgentSession(conversation=ConversationSession())
        conversation = ConversationSession()
        request = AgentRequest(
            session=session,
            conversation=conversation,
            request_id="fixed-id",
            metadata={"k": "v"},
        )
        self.assertIs(request.session, session)
        self.assertIs(request.conversation, conversation)
        self.assertEqual(request.request_id, "fixed-id")
        self.assertEqual(dict(request.metadata), {"k": "v"})

    def test_default_request_id_is_unique_per_instance(self):
        session = AgentSession(conversation=ConversationSession())
        a = AgentRequest(session=session, conversation=ConversationSession())
        b = AgentRequest(session=session, conversation=ConversationSession())
        self.assertNotEqual(a.request_id, b.request_id)

    def test_conversation_need_not_be_the_sessions_own_conversation(self):
        # See request.py's own "References An AgentSession - And
        # Separately Carries A Conversation" note: the two are
        # independent fields, never cross-validated.
        session = AgentSession(conversation=ConversationSession())
        newer_conversation = ConversationSession(
            messages=[ConversationMessage(role=ConversationRole.USER, content="new")]
        )
        request = AgentRequest(session=session, conversation=newer_conversation)
        self.assertIsNot(request.conversation, session.conversation)


class MetadataTests(unittest.TestCase):
    def test_metadata_is_wrapped_in_mappingproxytype(self):
        session = AgentSession(conversation=ConversationSession())
        request = AgentRequest(
            session=session, conversation=ConversationSession(), metadata={"a": 1}
        )
        self.assertNotIsInstance(request.metadata, dict)
        self.assertEqual(request.metadata["a"], 1)

    def test_metadata_defensive_copy_not_shared_with_caller(self):
        session = AgentSession(conversation=ConversationSession())
        original = {"a": 1}
        request = AgentRequest(
            session=session, conversation=ConversationSession(), metadata=original
        )
        original["a"] = 999
        self.assertEqual(request.metadata["a"], 1)

    def test_metadata_is_immutable(self):
        session = AgentSession(conversation=ConversationSession())
        request = AgentRequest(
            session=session, conversation=ConversationSession(), metadata={"a": 1}
        )
        with self.assertRaises(TypeError):
            request.metadata["a"] = 2


class ImmutabilityTests(unittest.TestCase):
    def test_immutability(self):
        session = AgentSession(conversation=ConversationSession())
        request = AgentRequest(session=session, conversation=ConversationSession())
        with self.assertRaises(dataclasses.FrozenInstanceError):
            request.request_id = "changed"


class EmptyConversationTests(unittest.TestCase):
    def test_empty_conversation_is_a_valid_conversation(self):
        session = AgentSession(conversation=ConversationSession())
        request = AgentRequest(session=session, conversation=ConversationSession())
        self.assertEqual(request.conversation.messages, ())


class EqualityTests(unittest.TestCase):
    def test_equality_when_all_fields_match(self):
        session = AgentSession(conversation=ConversationSession())
        conversation = ConversationSession()
        a = AgentRequest(
            session=session, conversation=conversation, request_id="r1", metadata={"k": "v"}
        )
        b = AgentRequest(
            session=session, conversation=conversation, request_id="r1", metadata={"k": "v"}
        )
        self.assertEqual(a, b)

    def test_inequality_by_request_id(self):
        session = AgentSession(conversation=ConversationSession())
        conversation = ConversationSession()
        a = AgentRequest(session=session, conversation=conversation, request_id="r1")
        b = AgentRequest(session=session, conversation=conversation, request_id="r2")
        self.assertNotEqual(a, b)

    def test_two_default_constructed_requests_are_not_equal(self):
        session = AgentSession(conversation=ConversationSession())
        a = AgentRequest(session=session, conversation=ConversationSession())
        b = AgentRequest(session=session, conversation=ConversationSession())
        self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main()
