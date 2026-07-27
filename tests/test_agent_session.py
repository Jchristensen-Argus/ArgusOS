"""Unit tests for argus.agent.session.AgentSession."""

import dataclasses
import unittest

from argus.agent import AgentSession
from argus.conversation import ConversationMessage, ConversationRole, ConversationSession


class DefaultsTests(unittest.TestCase):
    def test_defaults(self):
        conversation = ConversationSession()
        session = AgentSession(conversation=conversation)
        self.assertIs(session.conversation, conversation)
        self.assertTrue(session.session_id)
        self.assertEqual(dict(session.metadata), {})

    def test_all_fields_set(self):
        conversation = ConversationSession()
        session = AgentSession(
            conversation=conversation, session_id="fixed-id", metadata={"k": "v"}
        )
        self.assertIs(session.conversation, conversation)
        self.assertEqual(session.session_id, "fixed-id")
        self.assertEqual(dict(session.metadata), {"k": "v"})

    def test_default_session_id_is_unique_per_instance(self):
        a = AgentSession(conversation=ConversationSession())
        b = AgentSession(conversation=ConversationSession())
        self.assertNotEqual(a.session_id, b.session_id)


class MetadataTests(unittest.TestCase):
    def test_metadata_is_wrapped_in_mappingproxytype(self):
        session = AgentSession(conversation=ConversationSession(), metadata={"a": 1})
        self.assertNotIsInstance(session.metadata, dict)
        self.assertEqual(session.metadata["a"], 1)

    def test_metadata_defensive_copy_not_shared_with_caller(self):
        original = {"a": 1}
        session = AgentSession(conversation=ConversationSession(), metadata=original)
        original["a"] = 999
        self.assertEqual(session.metadata["a"], 1)

    def test_metadata_is_immutable(self):
        session = AgentSession(conversation=ConversationSession(), metadata={"a": 1})
        with self.assertRaises(TypeError):
            session.metadata["a"] = 2


class ImmutabilityTests(unittest.TestCase):
    def test_immutability(self):
        session = AgentSession(conversation=ConversationSession())
        with self.assertRaises(dataclasses.FrozenInstanceError):
            session.session_id = "changed"


class EmptyAndPopulatedSessionTests(unittest.TestCase):
    def test_empty_session_is_a_valid_session(self):
        session = AgentSession(conversation=ConversationSession())
        self.assertEqual(session.conversation.messages, ())

    def test_populated_session_carries_its_conversations_messages(self):
        conversation = ConversationSession(
            messages=[ConversationMessage(role=ConversationRole.USER, content="hi")]
        )
        session = AgentSession(conversation=conversation)
        self.assertEqual(len(session.conversation.messages), 1)
        self.assertEqual(session.conversation.messages[0].content, "hi")


class EqualityTests(unittest.TestCase):
    def test_equality_when_all_fields_match(self):
        conversation = ConversationSession()
        a = AgentSession(conversation=conversation, session_id="s1", metadata={"k": "v"})
        b = AgentSession(conversation=conversation, session_id="s1", metadata={"k": "v"})
        self.assertEqual(a, b)

    def test_inequality_by_session_id(self):
        conversation = ConversationSession()
        a = AgentSession(conversation=conversation, session_id="s1")
        b = AgentSession(conversation=conversation, session_id="s2")
        self.assertNotEqual(a, b)

    def test_two_default_constructed_sessions_are_not_equal(self):
        a = AgentSession(conversation=ConversationSession())
        b = AgentSession(conversation=ConversationSession())
        self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main()
