"""
Unit tests for argus.modules.sales.events (publish_sales_event) and
the domain events actually published by Importer and WorkQueue.

Covers: the payload shape publish_sales_event() constructs, and that
each real Sales call site (import, start/complete/skip) publishes
exactly the expected event(s) with the expected payload fields -
using the real Core InMemoryEventBus and EventType, not a mock.
"""

import logging
import tempfile
import unittest
from pathlib import Path

from argus.events.event_bus import InMemoryEventBus
from argus.events.event_types import EventType
from argus.modules.sales.events import SALES_EVENT_SOURCE, publish_sales_event
from argus.modules.sales.import_pipeline import Importer
from argus.modules.sales.work_items import WorkItemBuilder
from argus.modules.sales.work_queue import WorkQueue


def _bus():
    return InMemoryEventBus(logging.getLogger("test.sales.events"))


class PublishSalesEventPayloadTests(unittest.TestCase):
    def setUp(self):
        self.bus = _bus()
        self.received = []
        self.bus.subscribe(EventType.SALES_MODULE_EVENT, self.received.append)

    def test_publishes_on_the_sales_module_event_type(self):
        publish_sales_event(
            self.bus, event_name="LeadCreated", entity_type="Lead", entity_id="lead-1"
        )
        self.assertEqual(len(self.received), 1)
        self.assertEqual(self.received[0].type, EventType.SALES_MODULE_EVENT)

    def test_payload_contains_event_name_entity_type_entity_id(self):
        publish_sales_event(
            self.bus, event_name="LeadCreated", entity_type="Lead", entity_id="lead-1"
        )
        payload = self.received[0].payload
        self.assertEqual(payload["event_name"], "LeadCreated")
        self.assertEqual(payload["entity_type"], "Lead")
        self.assertEqual(payload["entity_id"], "lead-1")

    def test_extra_fields_are_merged_into_payload(self):
        publish_sales_event(
            self.bus,
            event_name="LeadCreated",
            entity_type="Lead",
            entity_id="lead-1",
            extra={"row_number": 3},
        )
        self.assertEqual(self.received[0].payload["row_number"], 3)

    def test_source_is_sales_module(self):
        publish_sales_event(
            self.bus, event_name="LeadCreated", entity_type="Lead", entity_id="lead-1"
        )
        self.assertEqual(self.received[0].source, SALES_EVENT_SOURCE)

    def test_rejects_empty_event_name(self):
        with self.assertRaises(ValueError):
            publish_sales_event(self.bus, event_name="", entity_type="Lead", entity_id="x")

    def test_rejects_empty_entity_id(self):
        with self.assertRaises(ValueError):
            publish_sales_event(
                self.bus, event_name="LeadCreated", entity_type="Lead", entity_id=""
            )


class ImporterEventPublishingTests(unittest.TestCase):
    def setUp(self):
        self.bus = _bus()
        self.received = []
        self.bus.subscribe(EventType.SALES_MODULE_EVENT, self.received.append)
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp_dir.cleanup)
        self.dir = Path(self._tmp_dir.name)

    def test_lead_imported_published_once_per_successful_lead(self):
        path = self.dir / "leads.csv"
        path.write_text("Company Name\nAcme\nBeta\n", encoding="utf-8")
        Importer(event_bus=self.bus).import_file(str(path))
        event_names = [e.payload["event_name"] for e in self.received]
        self.assertEqual(event_names, ["LeadImported", "LeadImported"])

    def test_lead_imported_payload_has_expected_shape(self):
        path = self.dir / "leads.csv"
        path.write_text("Company Name\nAcme\n", encoding="utf-8")
        result = Importer(event_bus=self.bus).import_file(str(path))
        payload = self.received[0].payload
        self.assertEqual(payload["entity_type"], "Lead")
        self.assertEqual(payload["entity_id"], result.leads[0].lead_id)
        self.assertEqual(payload["row_number"], 1)
        self.assertEqual(payload["source_file"], str(path))

    def test_no_event_published_for_a_failed_row(self):
        # A genuinely blank CSV line is skipped by csv.DictReader
        # before Importer sees it - use a row with content in another
        # column and a blank Company Name to actually exercise the
        # failed-row path.
        path = self.dir / "leads.csv"
        path.write_text("Company Name,Notes\n,missing company\n", encoding="utf-8")
        Importer(event_bus=self.bus).import_file(str(path))
        self.assertEqual(self.received, [])

    def test_no_events_published_when_no_event_bus_supplied(self):
        path = self.dir / "leads.csv"
        path.write_text("Company Name\nAcme\n", encoding="utf-8")
        # Should not raise, and obviously nothing is received since no
        # bus was even subscribed to this Importer.
        result = Importer().import_file(str(path))
        self.assertEqual(result.leads_created, 1)
        self.assertEqual(self.received, [])


class WorkQueueEventPublishingTests(unittest.TestCase):
    def setUp(self):
        self.bus = _bus()
        self.received = []
        self.bus.subscribe(EventType.SALES_MODULE_EVENT, self.received.append)
        self.queue = WorkQueue(event_bus=self.bus)
        self.item = WorkItemBuilder().with_lead_id("lead-1").build()
        self.queue.add(self.item)

    def test_start_publishes_work_item_started(self):
        self.queue.start(self.item.work_item_id)
        self.assertEqual(self.received[0].payload["event_name"], "WorkItemStarted")

    def test_complete_publishes_work_item_completed(self):
        self.queue.complete(self.item.work_item_id)
        self.assertEqual(self.received[0].payload["event_name"], "WorkItemCompleted")

    def test_skip_publishes_work_item_skipped(self):
        self.queue.skip(self.item.work_item_id)
        self.assertEqual(self.received[0].payload["event_name"], "WorkItemSkipped")

    def test_event_payload_has_expected_shape(self):
        self.queue.complete(self.item.work_item_id)
        payload = self.received[0].payload
        self.assertEqual(payload["entity_type"], "WorkItem")
        self.assertEqual(payload["entity_id"], self.item.work_item_id)
        self.assertEqual(payload["lead_id"], "lead-1")

    def test_start_then_complete_publishes_two_events_in_order(self):
        self.queue.start(self.item.work_item_id)
        self.queue.complete(self.item.work_item_id)
        event_names = [e.payload["event_name"] for e in self.received]
        self.assertEqual(event_names, ["WorkItemStarted", "WorkItemCompleted"])

    def test_no_event_published_on_failed_transition(self):
        self.queue.complete(self.item.work_item_id)
        self.received.clear()
        with self.assertRaises(Exception):
            self.queue.complete(self.item.work_item_id)
        self.assertEqual(self.received, [])

    def test_no_events_published_when_no_event_bus_supplied(self):
        queue = WorkQueue()
        item = WorkItemBuilder().build()
        queue.add(item)
        # Should not raise even with no bus at all.
        queue.complete(item.work_item_id)
        self.assertEqual(self.received, [])


if __name__ == "__main__":
    unittest.main()
