"""Unit tests for argus.modules.sales.work_items (WorkItem, WorkItemBuilder)."""

import dataclasses
import unittest
from datetime import datetime, timezone

from argus.modules.sales.work_items import (
    IWorkItemBuilder,
    InvalidWorkItemError,
    WorkItem,
    WorkItemBuilder,
    WorkItemMetadata,
    WorkItemStatus,
    WorkItemType,
)


class WorkItemDefaultsTests(unittest.TestCase):
    def test_defaults(self):
        work_item = WorkItem()
        self.assertTrue(work_item.work_item_id)
        self.assertEqual(work_item.lead_id, "")
        self.assertEqual(work_item.work_type, WorkItemType.OTHER)
        self.assertEqual(work_item.status, WorkItemStatus.PENDING)
        self.assertIsNone(work_item.due_date)
        self.assertIsNone(work_item.completed_at)
        self.assertEqual(work_item.notes, "")
        self.assertIsInstance(work_item.metadata, WorkItemMetadata)

    def test_default_work_item_id_is_unique_per_instance(self):
        self.assertNotEqual(WorkItem().work_item_id, WorkItem().work_item_id)


class WorkItemImmutabilityTests(unittest.TestCase):
    def test_status_field_immutable(self):
        work_item = WorkItem()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            work_item.status = WorkItemStatus.COMPLETED


class WorkItemBuilderIdentityTests(unittest.TestCase):
    def test_is_an_iworkitembuilder(self):
        self.assertIsInstance(WorkItemBuilder(), IWorkItemBuilder)


class WithLeadIdTests(unittest.TestCase):
    def test_with_lead_id_returns_self_for_chaining(self):
        builder = WorkItemBuilder()
        self.assertIs(builder.with_lead_id("lead-1"), builder)

    def test_with_lead_id_rejects_non_string(self):
        with self.assertRaises(InvalidWorkItemError):
            WorkItemBuilder().with_lead_id(123)


class WithWorkTypeTests(unittest.TestCase):
    def test_with_work_type_returns_self_for_chaining(self):
        builder = WorkItemBuilder()
        self.assertIs(builder.with_work_type(WorkItemType.CALL), builder)

    def test_with_work_type_is_overwritten_not_accumulated(self):
        work_item = (
            WorkItemBuilder()
            .with_work_type(WorkItemType.CALL)
            .with_work_type(WorkItemType.EMAIL)
            .build()
        )
        self.assertEqual(work_item.work_type, WorkItemType.EMAIL)

    def test_with_work_type_rejects_non_type(self):
        with self.assertRaises(InvalidWorkItemError):
            WorkItemBuilder().with_work_type("call")


class WithStatusTests(unittest.TestCase):
    def test_with_status_rejects_non_status(self):
        with self.assertRaises(InvalidWorkItemError):
            WorkItemBuilder().with_status("completed")

    def test_with_status_rejects_none(self):
        with self.assertRaises(InvalidWorkItemError):
            WorkItemBuilder().with_status(None)

    def test_default_status_is_pending(self):
        self.assertEqual(WorkItemBuilder().build().status, WorkItemStatus.PENDING)


class WithDatesTests(unittest.TestCase):
    def test_with_due_date_accepts_datetime(self):
        due = datetime(2026, 8, 1, tzinfo=timezone.utc)
        work_item = WorkItemBuilder().with_due_date(due).build()
        self.assertEqual(work_item.due_date, due)

    def test_with_due_date_rejects_non_datetime(self):
        with self.assertRaises(InvalidWorkItemError):
            WorkItemBuilder().with_due_date("2026-08-01")

    def test_with_completed_at_accepts_none(self):
        work_item = WorkItemBuilder().with_completed_at(None).build()
        self.assertIsNone(work_item.completed_at)

    def test_with_completed_at_rejects_non_datetime(self):
        with self.assertRaises(InvalidWorkItemError):
            WorkItemBuilder().with_completed_at("2026-08-01")


class WithMetadataTests(unittest.TestCase):
    def test_with_metadata_populates_extra(self):
        work_item = WorkItemBuilder().with_metadata("source", "import").build()
        self.assertEqual(work_item.metadata.extra["source"], "import")

    def test_with_metadata_rejects_empty_key(self):
        with self.assertRaises(InvalidWorkItemError):
            WorkItemBuilder().with_metadata("", "v")


class BuildTests(unittest.TestCase):
    def test_full_chain_produces_the_expected_work_item(self):
        due = datetime(2026, 8, 1, tzinfo=timezone.utc)
        work_item = (
            WorkItemBuilder()
            .with_lead_id("lead-1")
            .with_work_type(WorkItemType.CALL)
            .with_status(WorkItemStatus.PENDING)
            .with_due_date(due)
            .with_notes("Call about pricing")
            .build()
        )
        self.assertEqual(work_item.lead_id, "lead-1")
        self.assertEqual(work_item.work_type, WorkItemType.CALL)
        self.assertEqual(work_item.status, WorkItemStatus.PENDING)
        self.assertEqual(work_item.due_date, due)
        self.assertEqual(work_item.notes, "Call about pricing")

    def test_build_produces_a_fresh_work_item_id_each_call(self):
        builder = WorkItemBuilder().with_lead_id("lead-1")
        self.assertNotEqual(
            builder.build().work_item_id, builder.build().work_item_id
        )


if __name__ == "__main__":
    unittest.main()
