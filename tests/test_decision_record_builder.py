"""Unit tests for argus.decision.builder.DecisionRecordBuilder."""

import unittest

from argus.decision import (
    DecisionRecordBuilder,
    DecisionRecordPriority,
    DecisionRecordStatus,
    IDecisionRecordBuilder,
    InvalidDecisionRecordError,
)


class IdentityTests(unittest.TestCase):
    def test_is_an_idecisionrecordbuilder(self):
        self.assertIsInstance(DecisionRecordBuilder(), IDecisionRecordBuilder)

    def test_is_not_an_iservice(self):
        from argus.lifecycle import IService

        self.assertNotIsInstance(DecisionRecordBuilder(), IService)

    def test_starts_with_default_values(self):
        record = DecisionRecordBuilder().build()
        self.assertEqual(record.title, "")
        self.assertEqual(record.question, "")
        self.assertEqual(record.status, DecisionRecordStatus.PENDING)
        self.assertEqual(record.priority, DecisionRecordPriority.NORMAL)

    def test_constructor_takes_no_arguments(self):
        builder = DecisionRecordBuilder()
        self.assertIsInstance(builder, DecisionRecordBuilder)

    def test_no_with_decision_id_method_exists(self):
        self.assertFalse(hasattr(DecisionRecordBuilder(), "with_decision_id"))

    def test_no_with_owner_method_exists(self):
        self.assertFalse(hasattr(DecisionRecordBuilder(), "with_owner"))

    def test_no_with_tags_method_exists(self):
        self.assertFalse(hasattr(DecisionRecordBuilder(), "with_tags"))

    def test_has_with_priority_method(self):
        # Unlike owner/tags, priority is explicitly named in this
        # package's own Responsibilities list - see builder.py's own
        # module docstring.
        self.assertTrue(hasattr(DecisionRecordBuilder(), "with_priority"))

    def test_does_not_collide_with_decision_engine_builder_namespace(self):
        # There is no DecisionBuilder in argus.decision - Package 021
        # has no builder of its own. Confirms this package's own
        # DecisionRecordBuilder is the only builder in argus.decision.
        import argus.decision as decision_pkg

        self.assertFalse(hasattr(decision_pkg, "DecisionBuilder"))


class WithTitleTests(unittest.TestCase):
    def test_with_title_returns_self_for_chaining(self):
        builder = DecisionRecordBuilder()
        result = builder.with_title("Choose vendor")
        self.assertIs(result, builder)

    def test_with_title_is_overwritten_not_accumulated(self):
        record = (
            DecisionRecordBuilder().with_title("First").with_title("Second").build()
        )
        self.assertEqual(record.title, "Second")

    def test_with_title_rejects_empty_string(self):
        with self.assertRaises(InvalidDecisionRecordError):
            DecisionRecordBuilder().with_title("")

    def test_with_title_rejects_non_string(self):
        with self.assertRaises(InvalidDecisionRecordError):
            DecisionRecordBuilder().with_title(123)

    def test_with_title_rejects_none(self):
        with self.assertRaises(InvalidDecisionRecordError):
            DecisionRecordBuilder().with_title(None)


class WithQuestionTests(unittest.TestCase):
    def test_with_question_returns_self_for_chaining(self):
        builder = DecisionRecordBuilder()
        result = builder.with_question("Which vendor?")
        self.assertIs(result, builder)

    def test_with_question_is_overwritten_not_accumulated(self):
        record = (
            DecisionRecordBuilder()
            .with_question("First?")
            .with_question("Second?")
            .build()
        )
        self.assertEqual(record.question, "Second?")

    def test_with_question_rejects_empty_string(self):
        with self.assertRaises(InvalidDecisionRecordError):
            DecisionRecordBuilder().with_question("")

    def test_with_question_rejects_non_string(self):
        with self.assertRaises(InvalidDecisionRecordError):
            DecisionRecordBuilder().with_question(123)

    def test_with_question_rejects_none(self):
        with self.assertRaises(InvalidDecisionRecordError):
            DecisionRecordBuilder().with_question(None)


class WithStatusTests(unittest.TestCase):
    def test_with_status_returns_self_for_chaining(self):
        builder = DecisionRecordBuilder()
        result = builder.with_status(DecisionRecordStatus.APPROVED)
        self.assertIs(result, builder)

    def test_with_status_is_overwritten_not_accumulated(self):
        record = (
            DecisionRecordBuilder()
            .with_status(DecisionRecordStatus.IN_REVIEW)
            .with_status(DecisionRecordStatus.APPROVED)
            .build()
        )
        self.assertEqual(record.status, DecisionRecordStatus.APPROVED)

    def test_with_status_rejects_non_status(self):
        with self.assertRaises(InvalidDecisionRecordError):
            DecisionRecordBuilder().with_status("approved")

    def test_with_status_rejects_none(self):
        with self.assertRaises(InvalidDecisionRecordError):
            DecisionRecordBuilder().with_status(None)

    def test_default_status_is_pending(self):
        record = DecisionRecordBuilder().build()
        self.assertEqual(record.status, DecisionRecordStatus.PENDING)


class WithPriorityTests(unittest.TestCase):
    def test_with_priority_returns_self_for_chaining(self):
        builder = DecisionRecordBuilder()
        result = builder.with_priority(DecisionRecordPriority.HIGH)
        self.assertIs(result, builder)

    def test_with_priority_is_overwritten_not_accumulated(self):
        record = (
            DecisionRecordBuilder()
            .with_priority(DecisionRecordPriority.HIGH)
            .with_priority(DecisionRecordPriority.CRITICAL)
            .build()
        )
        self.assertEqual(record.priority, DecisionRecordPriority.CRITICAL)

    def test_with_priority_rejects_non_priority(self):
        with self.assertRaises(InvalidDecisionRecordError):
            DecisionRecordBuilder().with_priority("high")

    def test_with_priority_rejects_none(self):
        with self.assertRaises(InvalidDecisionRecordError):
            DecisionRecordBuilder().with_priority(None)

    def test_default_priority_is_normal(self):
        record = DecisionRecordBuilder().build()
        self.assertEqual(record.priority, DecisionRecordPriority.NORMAL)


class WithMetadataTests(unittest.TestCase):
    def test_with_metadata_returns_self_for_chaining(self):
        builder = DecisionRecordBuilder()
        result = builder.with_metadata("k", "v")
        self.assertIs(result, builder)

    def test_with_metadata_populates_extra(self):
        record = DecisionRecordBuilder().with_metadata("region", "US").build()
        self.assertEqual(record.metadata.extra["region"], "US")

    def test_with_metadata_accumulates_distinct_keys(self):
        record = (
            DecisionRecordBuilder().with_metadata("a", 1).with_metadata("b", 2).build()
        )
        self.assertEqual(dict(record.metadata.extra), {"a": 1, "b": 2})

    def test_with_metadata_same_key_overwrites(self):
        record = (
            DecisionRecordBuilder()
            .with_metadata("k", "first")
            .with_metadata("k", "second")
            .build()
        )
        self.assertEqual(record.metadata.extra["k"], "second")

    def test_with_metadata_rejects_empty_key(self):
        with self.assertRaises(InvalidDecisionRecordError):
            DecisionRecordBuilder().with_metadata("", "v")

    def test_with_metadata_rejects_non_string_key(self):
        with self.assertRaises(InvalidDecisionRecordError):
            DecisionRecordBuilder().with_metadata(123, "v")

    def test_with_metadata_cannot_set_owner_or_tags(self):
        record = DecisionRecordBuilder().with_metadata("owner", "Jane").build()
        self.assertIsNone(record.metadata.owner)
        self.assertEqual(record.metadata.extra["owner"], "Jane")


class BuildTests(unittest.TestCase):
    def test_build_with_no_calls_produces_a_default_decision_record(self):
        record = DecisionRecordBuilder().build()
        self.assertEqual(record.title, "")
        self.assertEqual(record.question, "")
        self.assertEqual(record.status, DecisionRecordStatus.PENDING)
        self.assertEqual(record.priority, DecisionRecordPriority.NORMAL)

    def test_build_produces_a_fresh_decision_id_each_call(self):
        builder = DecisionRecordBuilder().with_title("Choose vendor")
        first = builder.build()
        second = builder.build()
        self.assertNotEqual(first.decision_id, second.decision_id)

    def test_build_after_build_does_not_mutate_the_earlier_record(self):
        builder = DecisionRecordBuilder().with_title("First")
        first = builder.build()
        builder.with_title("Second")
        second = builder.build()
        self.assertEqual(first.title, "First")
        self.assertEqual(second.title, "Second")

    def test_full_chain_produces_the_expected_decision_record(self):
        record = (
            DecisionRecordBuilder()
            .with_title("Choose vendor")
            .with_question("Which packaging vendor should we use for Q3?")
            .with_status(DecisionRecordStatus.IN_REVIEW)
            .with_priority(DecisionRecordPriority.HIGH)
            .with_metadata("k", "v")
            .build()
        )
        self.assertEqual(record.title, "Choose vendor")
        self.assertEqual(
            record.question, "Which packaging vendor should we use for Q3?"
        )
        self.assertEqual(record.status, DecisionRecordStatus.IN_REVIEW)
        self.assertEqual(record.priority, DecisionRecordPriority.HIGH)
        self.assertEqual(record.metadata.extra["k"], "v")


if __name__ == "__main__":
    unittest.main()
