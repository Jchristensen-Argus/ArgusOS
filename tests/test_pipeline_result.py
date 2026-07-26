"""Unit tests for argus.pipeline.result.PipelineResult."""

import dataclasses
import unittest
from types import MappingProxyType

from argus.context import ContextBuilder
from argus.conversation import ConversationSession
from argus.intent import Intent, IntentType
from argus.planner import Plan
from argus.pipeline import PipelineResult
from argus.planning import PlanningSessionBuilder


def _plan():
    return Plan(originating_intent=Intent(name=IntentType.UNKNOWN, confidence=0.0))


def _cognitive_context():
    return ContextBuilder().build()


def _planning_session(cognitive_context):
    return PlanningSessionBuilder().with_context(cognitive_context).build()


class PipelineResultTests(unittest.TestCase):
    def test_defaults(self):
        conversation = ConversationSession()
        cognitive_context = _cognitive_context()
        planning_session = _planning_session(cognitive_context)
        plan = _plan()

        result = PipelineResult(
            conversation=conversation,
            cognitive_context=cognitive_context,
            planning_session=planning_session,
            plan=plan,
        )
        self.assertIs(result.conversation, conversation)
        self.assertIs(result.cognitive_context, cognitive_context)
        self.assertIs(result.planning_session, planning_session)
        self.assertIs(result.plan, plan)
        self.assertTrue(result.pipeline_id)
        self.assertIsInstance(result.pipeline_id, str)
        self.assertEqual(dict(result.metadata), {})

    def test_all_fields_set(self):
        conversation = ConversationSession()
        cognitive_context = _cognitive_context()
        planning_session = _planning_session(cognitive_context)
        plan = _plan()

        result = PipelineResult(
            conversation=conversation,
            cognitive_context=cognitive_context,
            planning_session=planning_session,
            plan=plan,
            pipeline_id="pipeline-1",
            metadata={"foo": "bar"},
        )
        self.assertEqual(result.pipeline_id, "pipeline-1")
        self.assertEqual(dict(result.metadata), {"foo": "bar"})

    def test_default_pipeline_id_is_unique_per_instance(self):
        conversation = ConversationSession()
        cognitive_context = _cognitive_context()
        planning_session = _planning_session(cognitive_context)
        plan = _plan()

        first = PipelineResult(
            conversation=conversation,
            cognitive_context=cognitive_context,
            planning_session=planning_session,
            plan=plan,
        )
        second = PipelineResult(
            conversation=conversation,
            cognitive_context=cognitive_context,
            planning_session=planning_session,
            plan=plan,
        )
        self.assertNotEqual(first.pipeline_id, second.pipeline_id)

    def test_metadata_is_wrapped_in_mappingproxytype(self):
        cognitive_context = _cognitive_context()
        result = PipelineResult(
            conversation=ConversationSession(),
            cognitive_context=cognitive_context,
            planning_session=_planning_session(cognitive_context),
            plan=_plan(),
            metadata={"a": 1},
        )
        self.assertIsInstance(result.metadata, MappingProxyType)

    def test_metadata_defensive_copy_not_shared_with_caller(self):
        cognitive_context = _cognitive_context()
        source = {"a": 1}
        result = PipelineResult(
            conversation=ConversationSession(),
            cognitive_context=cognitive_context,
            planning_session=_planning_session(cognitive_context),
            plan=_plan(),
            metadata=source,
        )
        source["a"] = 999
        self.assertEqual(dict(result.metadata), {"a": 1})

    def test_metadata_is_immutable(self):
        cognitive_context = _cognitive_context()
        result = PipelineResult(
            conversation=ConversationSession(),
            cognitive_context=cognitive_context,
            planning_session=_planning_session(cognitive_context),
            plan=_plan(),
            metadata={"a": 1},
        )
        with self.assertRaises(TypeError):
            result.metadata["a"] = 2

    def test_immutability(self):
        cognitive_context = _cognitive_context()
        result = PipelineResult(
            conversation=ConversationSession(),
            cognitive_context=cognitive_context,
            planning_session=_planning_session(cognitive_context),
            plan=_plan(),
        )
        with self.assertRaises(dataclasses.FrozenInstanceError):
            result.pipeline_id = "changed"
        with self.assertRaises(dataclasses.FrozenInstanceError):
            result.conversation = ConversationSession()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            result.plan = _plan()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            result.metadata = {}

    def test_no_execution_or_runtime_fields_exist(self):
        # "No execution results. No runtime state." - confirm the
        # dataclass's own field set is exactly what the work order
        # specifies, nothing more.
        field_names = {f.name for f in dataclasses.fields(PipelineResult)}
        self.assertEqual(
            field_names,
            {
                "conversation",
                "cognitive_context",
                "planning_session",
                "plan",
                "pipeline_id",
                "metadata",
            },
        )

    def test_equality_when_all_fields_match(self):
        conversation = ConversationSession()
        cognitive_context = _cognitive_context()
        planning_session = _planning_session(cognitive_context)
        plan = _plan()

        first = PipelineResult(
            conversation=conversation,
            cognitive_context=cognitive_context,
            planning_session=planning_session,
            plan=plan,
            pipeline_id="same",
        )
        second = PipelineResult(
            conversation=conversation,
            cognitive_context=cognitive_context,
            planning_session=planning_session,
            plan=plan,
            pipeline_id="same",
        )
        self.assertEqual(first, second)

    def test_not_equal_when_pipeline_id_differs(self):
        conversation = ConversationSession()
        cognitive_context = _cognitive_context()
        planning_session = _planning_session(cognitive_context)
        plan = _plan()

        first = PipelineResult(
            conversation=conversation,
            cognitive_context=cognitive_context,
            planning_session=planning_session,
            plan=plan,
            pipeline_id="a",
        )
        second = PipelineResult(
            conversation=conversation,
            cognitive_context=cognitive_context,
            planning_session=planning_session,
            plan=plan,
            pipeline_id="b",
        )
        self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
