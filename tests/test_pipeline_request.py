"""Unit tests for argus.pipeline.request.PipelineRequest."""

import dataclasses
import unittest
from types import MappingProxyType

from argus.conversation import ConversationSession
from argus.pipeline import PipelineRequest


class PipelineRequestTests(unittest.TestCase):
    def test_defaults(self):
        conversation = ConversationSession()
        request = PipelineRequest(conversation=conversation)
        self.assertIs(request.conversation, conversation)
        self.assertTrue(request.request_id)
        self.assertIsInstance(request.request_id, str)
        self.assertEqual(dict(request.metadata), {})

    def test_all_fields_set(self):
        conversation = ConversationSession()
        request = PipelineRequest(
            conversation=conversation,
            request_id="req-1",
            metadata={"foo": "bar"},
        )
        self.assertIs(request.conversation, conversation)
        self.assertEqual(request.request_id, "req-1")
        self.assertEqual(dict(request.metadata), {"foo": "bar"})

    def test_default_request_id_is_unique_per_instance(self):
        conversation = ConversationSession()
        first = PipelineRequest(conversation=conversation)
        second = PipelineRequest(conversation=conversation)
        self.assertNotEqual(first.request_id, second.request_id)

    def test_metadata_is_wrapped_in_mappingproxytype(self):
        request = PipelineRequest(conversation=ConversationSession(), metadata={"a": 1})
        self.assertIsInstance(request.metadata, MappingProxyType)

    def test_metadata_defensive_copy_not_shared_with_caller(self):
        source = {"a": 1}
        request = PipelineRequest(conversation=ConversationSession(), metadata=source)
        source["a"] = 999
        source["b"] = 2
        self.assertEqual(dict(request.metadata), {"a": 1})

    def test_metadata_is_immutable(self):
        request = PipelineRequest(conversation=ConversationSession(), metadata={"a": 1})
        with self.assertRaises(TypeError):
            request.metadata["a"] = 2

    def test_immutability(self):
        request = PipelineRequest(conversation=ConversationSession())
        with self.assertRaises(dataclasses.FrozenInstanceError):
            request.request_id = "changed"
        with self.assertRaises(dataclasses.FrozenInstanceError):
            request.conversation = ConversationSession()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            request.metadata = {}

    def test_empty_conversation_is_a_valid_conversation(self):
        conversation = ConversationSession()
        self.assertEqual(conversation.messages, ())
        request = PipelineRequest(conversation=conversation)
        self.assertEqual(request.conversation.messages, ())

    def test_equality_when_all_fields_match(self):
        conversation = ConversationSession()
        first = PipelineRequest(conversation=conversation, request_id="same", metadata={"a": 1})
        second = PipelineRequest(conversation=conversation, request_id="same", metadata={"a": 1})
        self.assertEqual(first, second)

    def test_inequality_by_request_id(self):
        conversation = ConversationSession()
        first = PipelineRequest(conversation=conversation, request_id="a")
        second = PipelineRequest(conversation=conversation, request_id="b")
        self.assertNotEqual(first, second)

    def test_two_default_constructed_requests_are_not_equal(self):
        conversation = ConversationSession()
        first = PipelineRequest(conversation=conversation)
        second = PipelineRequest(conversation=conversation)
        self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
