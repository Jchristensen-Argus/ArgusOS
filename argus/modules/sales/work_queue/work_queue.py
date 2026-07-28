"""
The WorkQueue for the Argus Sales OS Work Items package.

Purpose:
    Hold a working set of WorkItems and surface them to a salesperson
    in a sensible order, per ARGUS_SALES_OS_V1_ARCHITECTURE.md's
    Sprint 1 scope: "build the work queue" - the second half of
    priority #5, alongside the spreadsheet importer. A Lead describes
    who; a WorkItem describes what to do about them next (see
    work_items/work_item.py's own module docstring); WorkQueue is what
    actually decides "what's next" and records that something was
    done.

In-Memory Only, Same Limitation As The Importer:
    WorkQueue holds its WorkItems in a plain in-memory dict, exactly
    like Importer's within-run-only Company/Contact dedup maps - there
    is no persistent WorkItem store yet for this class to load from or
    write through. A WorkQueue instance's contents do not survive past
    the process that created it. Session Persistence (Slice 5, not yet
    built) is where that gap gets closed; naming it here rather than
    silently working around it matches this engagement's own
    established practice (see importer.py's Deduplication Within One
    Import Run Only note).

Status Transitions This Class Performs:
    start():    PENDING     -> IN_PROGRESS
    complete(): PENDING/IN_PROGRESS -> COMPLETED (sets completed_at)
    skip():     PENDING/IN_PROGRESS -> SKIPPED
    No other transition is permitted - calling complete() or skip() on
    an already-COMPLETED or already-SKIPPED item raises WorkQueueError,
    since re-completing or re-skipping a finished item is almost always
    a caller bug, not a legitimate state change.

Where Domain Events Are Published:
    Exactly like Importer, every successful start()/complete()/skip()
    publishes a Sales domain event (WorkItemStarted, WorkItemCompleted,
    WorkItemSkipped respectively) via publish_sales_event(), if an
    event_bus was supplied - optional, so this class remains fully
    testable without a live Application, matching every other Sales
    class's own precedent.

Responsibilities:
    - WorkQueue: hold WorkItems, surface the still-open ones in
      priority order (via ordering.order_work_items()), and transition
      a WorkItem's status on start/complete/skip, publishing the
      corresponding domain event.

Non-Responsibilities:
    - WorkQueue does not decide ordering itself - it delegates to
      ordering.order_work_items(), keeping the "what order" question
      pure and independently testable.
    - WorkQueue does not create WorkItems - callers construct them via
      WorkItemBuilder and add() them; WorkQueue only ever sequences and
      transitions items it's given.
    - WorkQueue does not persist anything - see the In-Memory Only note
      above.

Dependencies:
    argus.modules.sales.work_items (WorkItem, WorkItemStatus),
    argus.modules.sales.work_queue (ordering, exceptions),
    argus.modules.sales.events (publish_sales_event),
    argus.events (IEventBus) - typing only, optional at runtime.
"""

from dataclasses import replace
from datetime import datetime, timezone
from typing import Dict, List, Optional

from argus.events.interfaces import IEventBus
from argus.modules.sales.events import publish_sales_event
from argus.modules.sales.work_items.status import WorkItemStatus
from argus.modules.sales.work_items.work_item import WorkItem
from argus.modules.sales.work_queue.exceptions import WorkItemNotFoundError, WorkQueueError
from argus.modules.sales.work_queue.ordering import order_work_items

#: Statuses a WorkItem may be transitioned out of by start()/complete()/
#: skip() - a WorkItem already in a terminal status is not eligible.
_OPEN_STATUSES = (WorkItemStatus.PENDING, WorkItemStatus.IN_PROGRESS)


class WorkQueue:
    """
    An in-memory, ordered collection of WorkItems, with the
    start/complete/skip lifecycle a salesperson works through. See the
    module docstring for the full design rationale.
    """

    def __init__(self, *, event_bus: Optional[IEventBus] = None) -> None:
        """
        Parameters:
            event_bus: If supplied, a domain event is published for
                every successful start()/complete()/skip() call. If
                omitted, no events are published - the queue still
                works, for testing or offline use.
        """
        self._event_bus = event_bus
        self._items: Dict[str, WorkItem] = {}

    def add(self, work_item: WorkItem) -> None:
        """Add a WorkItem to the queue, keyed by its own work_item_id.
        Adding a WorkItem that shares an id with one already held
        overwrites it - callers are expected to add each WorkItem
        once."""
        self._items[work_item.work_item_id] = work_item

    def all_items(self) -> List[WorkItem]:
        """Every WorkItem the queue holds, in no particular order,
        including COMPLETED and SKIPPED ones."""
        return list(self._items.values())

    def pending_items(self) -> List[WorkItem]:
        """The queue's still-open WorkItems (PENDING or IN_PROGRESS),
        ordered per ordering.order_work_items() - what a salesperson
        should work through next, in order."""
        open_items = [
            item for item in self._items.values() if item.status in _OPEN_STATUSES
        ]
        return order_work_items(open_items)

    def start(self, work_item_id: str) -> WorkItem:
        """Transition a WorkItem to IN_PROGRESS. Publishes
        WorkItemStarted if an event_bus was supplied."""
        return self._transition(
            work_item_id,
            new_status=WorkItemStatus.IN_PROGRESS,
            event_name="WorkItemStarted",
        )

    def complete(self, work_item_id: str, *, notes: Optional[str] = None) -> WorkItem:
        """Transition a WorkItem to COMPLETED and set its completed_at
        to now. Publishes WorkItemCompleted if an event_bus was
        supplied."""
        return self._transition(
            work_item_id,
            new_status=WorkItemStatus.COMPLETED,
            event_name="WorkItemCompleted",
            notes=notes,
            set_completed_at=True,
        )

    def skip(self, work_item_id: str, *, notes: Optional[str] = None) -> WorkItem:
        """Transition a WorkItem to SKIPPED. Publishes WorkItemSkipped
        if an event_bus was supplied."""
        return self._transition(
            work_item_id,
            new_status=WorkItemStatus.SKIPPED,
            event_name="WorkItemSkipped",
            notes=notes,
        )

    def _transition(
        self,
        work_item_id: str,
        *,
        new_status: WorkItemStatus,
        event_name: str,
        notes: Optional[str] = None,
        set_completed_at: bool = False,
    ) -> WorkItem:
        current = self._items.get(work_item_id)
        if current is None:
            raise WorkItemNotFoundError(
                f"No WorkItem with work_item_id {work_item_id!r} is held by "
                f"this WorkQueue."
            )
        if current.status not in _OPEN_STATUSES:
            raise WorkQueueError(
                f"WorkItem {work_item_id!r} is already {current.status.value!r} "
                f"and cannot be transitioned to {new_status.value!r}."
            )

        changes = {"status": new_status}
        if notes is not None:
            changes["notes"] = notes
        if set_completed_at:
            changes["completed_at"] = datetime.now(timezone.utc)

        updated = replace(current, **changes)
        self._items[work_item_id] = updated

        if self._event_bus is not None:
            publish_sales_event(
                self._event_bus,
                event_name=event_name,
                entity_type="WorkItem",
                entity_id=work_item_id,
                extra={"lead_id": updated.lead_id},
            )

        return updated
