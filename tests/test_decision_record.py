"""Unit tests for argus.decision.decision_record.DecisionRecord.

Note: this file is named test_decision_record.py, not test_decision.py
- tests/test_decision.py already exists as Package 021's own Decision
Engine test file. See argus/decision/decision_record.py's own module
docstring for why this package's model is named DecisionRecord rather
than Decision.
"""

import copy
import dataclasses
import pickle
import unittest

from argus.decision import (
    DecisionRecord,
    DecisionRecordMetadata,
    DecisionRecordPriority,
    DecisionRecordStatus,
)


class DefaultsTests(unittest.TestCase):
    def test_defaults(self):
        record = DecisionRecord()
        self.assertTrue(record.decision_id)
        self.assertEqual(record.title, "")
        self.assertEqual(record.question, "")
        self.assertEqual(record.status, DecisionRecordStatus.PENDING)
        self.assertEqual(record.priority, DecisionRecordPriority.NORMAL)
        self.assertIsInstance(record.metadata, DecisionRecordMetadata)

    def test_all_fields_set(self):
        metadata = DecisionRecordMetadata(extra={"k": "v"})
        record = DecisionRecord(
            decision_id="fixed-id",
            title="Choose vendor",
            question="Which packaging vendor should we use for Q3?",
            status=DecisionRecordStatus.IN_REVIEW,
            priority=DecisionRecordPriority.HIGH,
            metadata=metadata,
        )
        self.assertEqual(record.decision_id, "fixed-id")
        self.assertEqual(record.title, "Choose vendor")
        self.assertEqual(
            record.question, "Which packaging vendor should we use for Q3?"
        )
        self.assertEqual(record.status, DecisionRecordStatus.IN_REVIEW)
        self.assertEqual(record.priority, DecisionRecordPriority.HIGH)
        self.assertIs(record.metadata, metadata)

    def test_default_decision_id_is_unique_per_instance(self):
        a = DecisionRecord()
        b = DecisionRecord()
        self.assertNotEqual(a.decision_id, b.decision_id)


class FieldOrderTests(unittest.TestCase):
    def test_field_order_places_metadata_last(self):
        field_names = [f.name for f in dataclasses.fields(DecisionRecord)]
        self.assertEqual(
            field_names,
            ["decision_id", "title", "question", "status", "priority", "metadata"],
        )


class DefaultStatusAndPriorityTests(unittest.TestCase):
    def test_default_status_is_pending(self):
        self.assertEqual(DecisionRecord().status, DecisionRecordStatus.PENDING)

    def test_default_priority_is_normal_not_low(self):
        # "Default should follow the same convention established in
        # the Goal framework" - see priority.py's own module
        # docstring.
        self.assertEqual(DecisionRecord().priority, DecisionRecordPriority.NORMAL)


class ImmutabilityTests(unittest.TestCase):
    def test_immutability(self):
        record = DecisionRecord()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            record.decision_id = "mutated"

    def test_title_field_immutable(self):
        record = DecisionRecord()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            record.title = "mutated"

    def test_question_field_immutable(self):
        record = DecisionRecord()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            record.question = "mutated"

    def test_priority_field_immutable(self):
        record = DecisionRecord()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            record.priority = DecisionRecordPriority.CRITICAL

    def test_metadata_field_immutable(self):
        record = DecisionRecord()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            record.metadata = DecisionRecordMetadata()


class MiscellaneousRobustnessTests(unittest.TestCase):
    def test_deepcopy_of_scalar_fields_round_trips_equal(self):
        record = DecisionRecord()
        copied_id = copy.deepcopy(record.decision_id)
        self.assertEqual(copied_id, record.decision_id)

    def test_pickle_of_scalar_fields_round_trips_equal(self):
        record = DecisionRecord()
        self.assertEqual(pickle.loads(pickle.dumps(record.decision_id)), record.decision_id)
        self.assertIs(pickle.loads(pickle.dumps(record.status)), record.status)
        self.assertIs(pickle.loads(pickle.dumps(record.priority)), record.priority)

    def test_decision_id_is_a_plain_string_suitable_for_json(self):
        record = DecisionRecord()
        self.assertIsInstance(record.decision_id, str)


class EqualityTests(unittest.TestCase):
    def test_equality_when_all_fields_match(self):
        metadata = DecisionRecordMetadata()
        a = DecisionRecord(decision_id="d1", title="Choose vendor", metadata=metadata)
        b = DecisionRecord(decision_id="d1", title="Choose vendor", metadata=metadata)
        self.assertEqual(a, b)

    def test_not_equal_when_decision_id_differs(self):
        metadata = DecisionRecordMetadata()
        a = DecisionRecord(decision_id="d1", metadata=metadata)
        b = DecisionRecord(decision_id="d2", metadata=metadata)
        self.assertNotEqual(a, b)

    def test_not_equal_when_priority_differs(self):
        metadata = DecisionRecordMetadata()
        a = DecisionRecord(decision_id="d1", priority=DecisionRecordPriority.LOW, metadata=metadata)
        b = DecisionRecord(decision_id="d1", priority=DecisionRecordPriority.CRITICAL, metadata=metadata)
        self.assertNotEqual(a, b)

    def test_not_equal_when_status_differs(self):
        metadata = DecisionRecordMetadata()
        a = DecisionRecord(decision_id="d1", status=DecisionRecordStatus.PENDING, metadata=metadata)
        b = DecisionRecord(decision_id="d1", status=DecisionRecordStatus.ARCHIVED, metadata=metadata)
        self.assertNotEqual(a, b)

    def test_not_equal_when_question_differs(self):
        metadata = DecisionRecordMetadata()
        a = DecisionRecord(decision_id="d1", question="Q1?", metadata=metadata)
        b = DecisionRecord(decision_id="d1", question="Q2?", metadata=metadata)
        self.assertNotEqual(a, b)


class NoCollisionWithDecisionEngineTests(unittest.TestCase):
    def test_decision_record_is_not_the_decision_engine_decision(self):
        # Confirms DecisionRecord and Decision (Package 021, the
        # Decision Engine's own outcome value object) are genuinely
        # distinct classes coexisting in the same package.
        from argus.decision import Decision

        self.assertIsNot(DecisionRecord, Decision)
        self.assertNotEqual(
            {f.name for f in dataclasses.fields(DecisionRecord)},
            {f.name for f in dataclasses.fields(Decision)},
        )


if __name__ == "__main__":
    unittest.main()
