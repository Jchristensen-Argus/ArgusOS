"""
Domain event publishing for the Argus Sales OS Module.

Purpose:
    Provide the one, documented way argus.modules.sales publishes
    domain events onto the existing Core Event Bus (argus.events,
    Package 003) - reusing Event/IEventBus entirely as-is, adding
    nothing to Core beyond the single EventType.SALES_MODULE_EVENT
    member (see argus/events/event_types.py's own comment block for
    the full rationale on why a Module gets one generic EventType, not
    one per domain event).

Payload Shape - The Convention Every Caller Must Follow:
    Every event published through publish_sales_event() carries:
      - "event_name": a short PascalCase string identifying the
        specific domain event (e.g. "LeadCreated",
        "WorkItemCompleted") - this is what a subscriber filters on,
        since EventType alone only says "something happened in
        Sales."
      - "entity_type": the kind of entity involved (e.g. "Lead").
      - "entity_id": that entity's own id.
      - any additional caller-supplied fields, merged in as-is.
    This module does not enforce a closed set of event_name values -
    unlike EventType itself, which is a closed enum Core owns, the
    specific vocabulary of Sales domain events belongs to Sales, and
    growing it never requires touching this file or any Core file
    again. This is the entire point of the design.

Who Calls This:
    Not the value objects (Lead, Company, Contact, Campaign, WorkItem)
    themselves - they stay pure, dependency-free leaves, per every
    value object's own module docstring in this codebase. This
    function is meant to be called by whatever orchestrating code
    actually performs a create/complete/assign operation - the future
    spreadsheet importer (Slice 4) and work queue (Slice 4), not yet
    built. No call sites exist yet for entity-lifecycle events; this
    slice delivers the mechanism, ready for those slices to use.

Responsibilities:
    - publish_sales_event(): construct a well-formed Event and publish
      it via the caller's IEventBus.

Non-Responsibilities:
    - This module does not decide *when* a domain event should fire -
      that's each call site's own responsibility, mirroring how
      PluginManager.register() (not Plugin itself) decides when
      PLUGIN_REGISTERED fires (Package 014).
    - This module holds no state and constructs no IEventBus of its
      own - the bus is always supplied by the caller, matching
      PluginManager's own "IEventBus injected, never constructed"
      precedent.

Dependencies:
    argus.events (Event, EventType, IEventBus).
"""

from typing import Any, Mapping, Optional

from argus.events.event import Event
from argus.events.event_types import EventType
from argus.events.interfaces import IEventBus

#: The source string every Sales domain event is published under,
#: matching the "source=<lowercase_manager_name>" convention
#: PluginManager (argus/plugins/manager.py) and every other Core
#: publisher already uses.
SALES_EVENT_SOURCE = "sales_module"


def publish_sales_event(
    event_bus: IEventBus,
    *,
    event_name: str,
    entity_type: str,
    entity_id: str,
    extra: Optional[Mapping[str, Any]] = None,
) -> None:
    """
    Publish one Sales domain event on the given Event Bus.

    Parameters:
        event_bus: The IEventBus to publish on - supplied by the
            caller, never constructed here.
        event_name: A short PascalCase string identifying the specific
            domain event (e.g. "LeadCreated"). Required, non-empty.
        entity_type: The kind of entity involved (e.g. "Lead").
            Required, non-empty.
        entity_id: That entity's own id. Required, non-empty.
        extra: Any additional fields to merge into the event's
            payload. Optional.

    Raises:
        ValueError: If event_name, entity_type, or entity_id is not a
            non-empty string.
    """
    for label, value in (
        ("event_name", event_name),
        ("entity_type", entity_type),
        ("entity_id", entity_id),
    ):
        if not isinstance(value, str) or not value:
            raise ValueError(f"{label} must be a non-empty string, got {value!r}.")

    payload = {
        "event_name": event_name,
        "entity_type": entity_type,
        "entity_id": entity_id,
    }
    if extra:
        payload.update(extra)

    event_bus.publish(
        Event(
            type=EventType.SALES_MODULE_EVENT,
            source=SALES_EVENT_SOURCE,
            payload=payload,
        )
    )
