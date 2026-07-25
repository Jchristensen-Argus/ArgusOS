"""Unit tests for argus.conversation.session (ConversationSession),
argus.conversation.message (ConversationMessage, ConversationRole),
and argus.conversation.state (ConversationState)."""

import unittest
from datetime import datetime, timezone
from types import MappingProxyType

from argus.conversation import (
    ConversationMessage,
    ConversationRole,
    ConversationSession,
    ConversationState,
)


class ConversationStateTests(unittest.TestCase):
    def test_expected_members_exist(self):
        self.assertEqual(
            {member.name for member in ConversationState},
            {"NEW", "ACTIVE", "WAITING", "CLOSED"},
        )

    def test_members_have_unique_string_values(self):
        values = [member.value for member in ConversationState]

        self.assertEqual(len(values), len(set(values)))
        self.assertTrue(all(isinstance(v, str) for v in values))


class ConversationRoleTests(unittest.TestCase):
    def test_expected_members_exist(self):
        self.assertEqual(
            {member.name for member in ConversationRole},
            {"USER", "ASSISTANT", "SYSTEM"},
        )

    def test_members_have_unique_string_values(self):
        values = [member.value for member in ConversationRole]

        self.assertEqual(len(values), len(set(values)))


class ConversationMessageConstructionTests(unittest.TestCase):
    def test_minimal_construction_defaults(self):
        message = ConversationMessage(role=ConversationRole.USER, content="hi")

        self.assertEqual(message.role, ConversationRole.USER)
        self.assertEqual(message.content, "hi")
        self.assertEqual(message.metadata, {})
        self.assertIsInstance(message.id, str)
        self.assertTrue(message.id)
        self.assertIsInstance(message.timestamp, datetime)

    def test_id_defaults_are_unique_per_instance(self):
        first = ConversationMessage(role=ConversationRole.USER, content="a")
        second = ConversationMessage(role=ConversationRole.USER, content="b")

        self.assertNotEqual(first.id, second.id)

    def test_timestamp_defaults_to_utc_aware_now(self):
        message = ConversationMessage(role=ConversationRole.USER, content="hi")

        self.assertIsNotNone(message.timestamp.tzinfo)
        self.assertEqual(message.timestamp.tzinfo, timezone.utc)

    def test_explicit_fields_are_honored(self):
        ts = datetime(2026, 1, 1, tzinfo=timezone.utc)

        message = ConversationMessage(
            role=ConversationRole.ASSISTANT,
            content="hello",
            id="fixed-id",
            timestamp=ts,
            metadata={"k": "v"},
        )

        self.assertEqual(message.id, "fixed-id")
        self.assertEqual(message.timestamp, ts)
        self.assertEqual(message.metadata, {"k": "v"})


class ConversationMessageImmutabilityTests(unittest.TestCase):
    def test_message_is_frozen(self):
        message = ConversationMessage(role=ConversationRole.USER, content="hi")

        with self.assertRaises(Exception):
            message.content = "changed"

    def test_metadata_is_read_only_mapping(self):
        message = ConversationMessage(
            role=ConversationRole.USER, content="hi", metadata={"k": "v"}
        )

        self.assertIsInstance(message.metadata, MappingProxyType)
        with self.assertRaises(TypeError):
            message.metadata["k"] = "changed"

    def test_mutating_source_metadata_dict_after_construction_does_not_affect_message(self):
        source = {"k": "v"}
        message = ConversationMessage(role=ConversationRole.USER, content="hi", metadata=source)

        source["k"] = "mutated"

        self.assertEqual(message.metadata["k"], "v")


class ConversationSessionConstructionTests(unittest.TestCase):
    def test_minimal_construction_defaults(self):
        session = ConversationSession()

        self.assertEqual(session.state, ConversationState.NEW)
        self.assertEqual(session.messages, ())
        self.assertEqual(session.metadata, {})
        self.assertIsInstance(session.id, str)
        self.assertTrue(session.id)
        self.assertIsInstance(session.created_at, datetime)
        self.assertIsInstance(session.updated_at, datetime)

    def test_id_defaults_are_unique_per_instance(self):
        first = ConversationSession()
        second = ConversationSession()

        self.assertNotEqual(first.id, second.id)

    def test_created_at_defaults_to_utc_aware_now(self):
        session = ConversationSession()

        self.assertIsNotNone(session.created_at.tzinfo)
        self.assertEqual(session.created_at.tzinfo, timezone.utc)

    def test_explicit_fields_are_honored(self):
        ts = datetime(2026, 1, 1, tzinfo=timezone.utc)
        message = ConversationMessage(role=ConversationRole.USER, content="hi")

        session = ConversationSession(
            id="fixed-id",
            created_at=ts,
            updated_at=ts,
            state=ConversationState.ACTIVE,
            metadata={"k": "v"},
            messages=[message],
        )

        self.assertEqual(session.id, "fixed-id")
        self.assertEqual(session.created_at, ts)
        self.assertEqual(session.updated_at, ts)
        self.assertEqual(session.state, ConversationState.ACTIVE)
        self.assertEqual(session.metadata, {"k": "v"})
        self.assertEqual(len(session.messages), 1)

    def test_multiple_messages_preserve_order(self):
        first = ConversationMessage(role=ConversationRole.USER, content="a")
        second = ConversationMessage(role=ConversationRole.ASSISTANT, content="b")

        session = ConversationSession(messages=[first, second])

        self.assertEqual([m.content for m in session.messages], ["a", "b"])


class ConversationSessionImmutabilityTests(unittest.TestCase):
    def test_session_is_frozen(self):
        session = ConversationSession()

        with self.assertRaises(Exception):
            session.state = ConversationState.ACTIVE

    def test_messages_is_a_tuple_not_the_original_list(self):
        messages_list = [ConversationMessage(role=ConversationRole.USER, content="a")]

        session = ConversationSession(messages=messages_list)

        self.assertIsInstance(session.messages, tuple)

    def test_mutating_source_messages_list_after_construction_does_not_affect_session(self):
        messages_list = [ConversationMessage(role=ConversationRole.USER, content="a")]
        session = ConversationSession(messages=messages_list)

        messages_list.append(ConversationMessage(role=ConversationRole.USER, content="b"))

        self.assertEqual(len(session.messages), 1)

    def test_metadata_is_read_only_mapping(self):
        session = ConversationSession(metadata={"k": "v"})

        self.assertIsInstance(session.metadata, MappingProxyType)
        with self.assertRaises(TypeError):
            session.metadata["k"] = "changed"

    def test_mutating_source_metadata_dict_after_construction_does_not_affect_session(self):
        source = {"k": "v"}
        session = ConversationSession(metadata=source)

        source["k"] = "mutated"

        self.assertEqual(session.metadata["k"], "v")


if __name__ == "__main__":
    unittest.main()
