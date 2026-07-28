"""
Session orchestration for the Argus Sales OS persistence package
(Sprint 1, Slice 5).

Purpose:
    Tie SalesRepository (storage) to Importer and WorkQueue (behavior)
    at exactly the moments persistence needs to happen: before an
    import (load existing Companies/Contacts/Campaigns/Leads to seed
    dedup), after an import (save the updated collections), at
    startup (rehydrate a WorkQueue from stored WorkItems), and after a
    WorkQueue mutation (save its current WorkItems back).
    Importer and WorkQueue themselves stay exactly as persistence-
    unaware as they were in Slice 4 - neither imports
    SalesRepository or anything in this package - so both remain
    fully testable without a filesystem, unchanged. This module is
    where the two sides meet.

Responsibilities:
    - import_and_persist(): load existing dedup-relevant entities,
      run an Importer, and save the resulting collections, correctly
      handling the companies/contacts/campaigns (full-set) vs. leads
      (this-run-only) asymmetry documented in
      import_pipeline/result.py.
    - load_work_queue(): rehydrate a WorkQueue from every stored
      WorkItem.
    - save_work_queue(): persist a WorkQueue's current WorkItems
      (including COMPLETED/SKIPPED ones - all_items(), not
      pending_items(), so history is not lost on save).

Non-Responsibilities:
    - This module does not implement storage itself (see
      repository.py) or entity (de)serialization (see
      serialization.py).
    - This module does not decide the import/queue business logic -
      Importer and WorkQueue still own that entirely.

Dependencies:
    argus.modules.sales.persistence.repository (SalesRepository),
    argus.modules.sales.import_pipeline (Importer, ImportResult),
    argus.modules.sales.work_queue (WorkQueue),
    argus.events (IEventBus) - typing only, optional at runtime.
"""

from typing import Mapping, Optional

from argus.events.interfaces import IEventBus
from argus.modules.sales.import_pipeline.importer import Importer
from argus.modules.sales.import_pipeline.result import ImportResult
from argus.modules.sales.persistence.repository import SalesRepository
from argus.modules.sales.work_queue.work_queue import WorkQueue


def import_and_persist(
    repository: SalesRepository,
    path: str,
    *,
    column_mapping: Optional[Mapping[str, str]] = None,
    event_bus: Optional[IEventBus] = None,
) -> ImportResult:
    """
    Import a Lead Workspace CSV, deduplicating against previously
    stored Companies/Contacts/Campaigns, then persist the result.

    Parameters:
        repository: Where existing entities are loaded from and the
            updated collections are saved to.
        path: Filesystem path to the CSV file - passed through to
            Importer.import_file().
        column_mapping: Passed through to Importer.
        event_bus: Passed through to Importer - if supplied,
            LeadImported is published per new Lead, exactly as in
            Slice 4.

    Returns:
        The ImportResult from Importer.import_file(), unmodified -
        callers that want counts or per-row errors read it exactly as
        before Slice 5.
    """
    importer = Importer(
        column_mapping=column_mapping,
        event_bus=event_bus,
        existing_companies=repository.load_companies(),
        existing_contacts=repository.load_contacts(),
        existing_campaigns=repository.load_campaigns(),
    )
    result = importer.import_file(path)

    # companies/contacts/campaigns are each the FULL current set
    # (seeded + created this run) - safe to save directly, replacing
    # the entire stored collection. leads is THIS RUN ONLY - must be
    # merged with what was already stored, or previously-imported
    # Leads would be silently lost. See result.py's Asymmetry note.
    repository.save_companies(result.companies)
    repository.save_contacts(result.contacts)
    repository.save_campaigns(result.campaigns)
    existing_leads = repository.load_leads()
    repository.save_leads(list(existing_leads) + list(result.leads))

    return result


def load_work_queue(
    repository: SalesRepository, *, event_bus: Optional[IEventBus] = None
) -> WorkQueue:
    """
    Rehydrate a WorkQueue from every WorkItem the repository holds.

    Every stored WorkItem is added, regardless of status - a
    previously COMPLETED or SKIPPED WorkItem is restored as such
    (all_items() reflects true history); pending_items() then
    naturally recomputes the correct open, ordered subset from
    whichever of those items are still PENDING or IN_PROGRESS. No
    separate "queue state" is stored or needs to be - the WorkItems
    themselves are the entire source of truth.

    Parameters:
        repository: Where WorkItems are loaded from.
        event_bus: Passed through to the new WorkQueue - subsequent
            start()/complete()/skip() calls publish events exactly as
            in Slice 4.

    Returns:
        A new WorkQueue populated with every stored WorkItem.
    """
    queue = WorkQueue(event_bus=event_bus)
    for work_item in repository.load_work_items():
        queue.add(work_item)
    return queue


def save_work_queue(repository: SalesRepository, work_queue: WorkQueue) -> None:
    """
    Persist a WorkQueue's current WorkItems.

    Saves all_items() (every WorkItem the queue holds, in every
    status), not pending_items() - saving only the open subset would
    permanently lose the record of every completed and skipped item on
    the next restart.

    Parameters:
        repository: Where the WorkItems are saved to.
        work_queue: The WorkQueue whose current state should be
            persisted - call this after every start()/complete()/
            skip()/add() the caller wants durable.
    """
    repository.save_work_items(work_queue.all_items())
