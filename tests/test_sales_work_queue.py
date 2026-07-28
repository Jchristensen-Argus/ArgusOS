"""
Unit tests for argus.modules.sales.work_queue (ordering, WorkQueue).

Covers: due-date ordering, start/complete/skip transitions, and
invalid-transition/unknown-id error paths. Event publishing from
WorkQueue is covered by test_sales_events.py, not duplicated here.
"""

import unittest
from datetime import datetime, timedelta, timezone

from argus.modules.sales.work_items import WorkItemBuilder, WorkItemStatus
from argus.modules.sales.work_queue import WorkItemNotFoundError, WorkQueue, WorkQueueError
from argus.modules.sales.work_queue.ordering import order_work_items

_NOW = datetime(2026, 7, 27, 12, 0, tzinfo=timezone.utc)


class OrderingTests(unittest.TestCase):
    def test_earlier_due_date_sorts_before_later_due_date(self):
        soon = WorkItemBuilder().with_due_date(_NOW + timedelta(hours=1)).build()
        later = WorkItemBuilder().with_due_date(_NOW + timedelta(days=1)).build()
        ordered = order_work_items([later, soon])
        self.assertEqual([i.work_item_id for i in ordered], [soon.work_item_id, later.work_item_id])

    def test_dated_items_sort_before_undated_items(self):
        dated = WorkItemBuilder().with_due_date(_NOW + timedelta(days=5)).build()
        undated = WorkItemBuilder().build()
        ordered = order_work_items([undated, dated])
        self.assertEqual([i.work_item_id for i in ordered], [dated.work_item_id, undated.work_item_id])

    def test_undated_items_tiebreak_by_creation_order(self):
        first = WorkItemBuilder().build()
        second = WorkItemBuilder().build()
        ordered = order_work_items([second, first])
        self.assertEqual(
            [i.work_item_id for i in ordered], [first.work_item_id, second.work_item_id]
        )

    def test_ordering_does_not_mutate_input_list(self):
        items = [WorkItemBuilder().build(), WorkItemBuilder().build()]
        original_order = list(items)
        order_work_items(items)
        self.assertEqual(items, original_order)

    def test_empty_input_returns_empty_list(self):
        self.assertEqual(order_work_items([]), [])


class WorkQueueAddAndPendingTests(unittest.TestCase):
    def test_all_items_starts_empty(self):
        self.assertEqual(WorkQueue().all_items(), [])

    def test_add_makes_item_visible_in_all_items(self):
        queue = WorkQueue()
        item = WorkItemBuilder().build()
        queue.add(item)
        self.assertEqual([i.work_item_id for i in queue.all_items()], [item.work_item_id])

    def test_pending_items_excludes_completed_and_skipped(self):
        queue = WorkQueue()
        pending = WorkItemBuilder().build()
        completed = WorkItemBuilder().with_status(WorkItemStatus.COMPLETED).build()
        skipped = WorkItemBuilder().with_status(WorkItemStatus.SKIPPED).build()
        for item in (pending, completed, skipped):
            queue.add(item)
        self.assertEqual(
            [i.work_item_id for i in queue.pending_items()], [pending.work_item_id]
        )

    def test_pending_items_includes_in_progress(self):
        queue = WorkQueue()
        item = WorkItemBuilder().with_status(WorkItemStatus.IN_PROGRESS).build()
        queue.add(item)
        self.assertEqual(len(queue.pending_items()), 1)

    def test_pending_items_is_ordered(self):
        queue = WorkQueue()
        soon = WorkItemBuilder().with_due_date(_NOW + timedelta(hours=1)).build()
        later = WorkItemBuilder().with_due_date(_NOW + timedelta(days=1)).build()
        queue.add(later)
        queue.add(soon)
        self.assertEqual(
            [i.work_item_id for i in queue.pending_items()],
            [soon.work_item_id, later.work_item_id],
        )


class WorkQueueTransitionTests(unittest.TestCase):
    def test_start_transitions_pending_to_in_progress(self):
        queue = WorkQueue()
        item = WorkItemBuilder().build()
        queue.add(item)
        updated = queue.start(item.work_item_id)
        self.assertEqual(updated.status, WorkItemStatus.IN_PROGRESS)

    def test_complete_transitions_to_completed_and_sets_completed_at(self):
        queue = WorkQueue()
        item = WorkItemBuilder().build()
        queue.add(item)
        updated = queue.complete(item.work_item_id, notes="talked to them")
        self.assertEqual(updated.status, WorkItemStatus.COMPLETED)
        self.assertIsNotNone(updated.completed_at)
        self.assertEqual(updated.notes, "talked to them")

    def test_complete_can_be_called_directly_from_pending(self):
        # start() is not a required intermediate step.
        queue = WorkQueue()
        item = WorkItemBuilder().build()
        queue.add(item)
        updated = queue.complete(item.work_item_id)
        self.assertEqual(updated.status, WorkItemStatus.COMPLETED)

    def test_skip_transitions_to_skipped(self):
        queue = WorkQueue()
        item = WorkItemBuilder().build()
        queue.add(item)
        updated = queue.skip(item.work_item_id, notes="not a fit")
        self.assertEqual(updated.status, WorkItemStatus.SKIPPED)
        self.assertEqual(updated.notes, "not a fit")

    def test_transition_updates_the_stored_item(self):
        queue = WorkQueue()
        item = WorkItemBuilder().build()
        queue.add(item)
        queue.complete(item.work_item_id)
        stored = next(i for i in queue.all_items() if i.work_item_id == item.work_item_id)
        self.assertEqual(stored.status, WorkItemStatus.COMPLETED)


class WorkQueueInvalidTransitionTests(unittest.TestCase):
    def test_complete_on_unknown_id_raises_not_found(self):
        with self.assertRaises(WorkItemNotFoundError):
            WorkQueue().complete("does-not-exist")

    def test_start_on_unknown_id_raises_not_found(self):
        with self.assertRaises(WorkItemNotFoundError):
            WorkQueue().start("does-not-exist")

    def test_completing_an_already_completed_item_raises(self):
        queue = WorkQueue()
        item = WorkItemBuilder().build()
        queue.add(item)
        queue.complete(item.work_item_id)
        with self.assertRaises(WorkQueueError):
            queue.complete(item.work_item_id)

    def test_skipping_an_already_skipped_item_raises(self):
        queue = WorkQueue()
        item = WorkItemBuilder().build()
        queue.add(item)
        queue.skip(item.work_item_id)
        with self.assertRaises(WorkQueueError):
            queue.skip(item.work_item_id)

    def test_starting_an_already_completed_item_raises(self):
        queue = WorkQueue()
        item = WorkItemBuilder().build()
        queue.add(item)
        queue.complete(item.work_item_id)
        with self.assertRaises(WorkQueueError):
            queue.start(item.work_item_id)

    def test_work_item_not_found_error_is_a_work_queue_error(self):
        self.assertTrue(issubclass(WorkItemNotFoundError, WorkQueueError))


if __name__ == "__main__":
    unittest.main()
