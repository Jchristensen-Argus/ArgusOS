"""
Work-item ordering for the Argus Sales OS Work Queue package.

Purpose:
    Decide what order a set of not-yet-finished WorkItems should be
    surfaced in. Pure transformation - no state, no Event Bus
    interaction, no mutation of any WorkItem - mirroring the parsing/
    orchestration split argus.modules.sales.import_pipeline established
    between row_parser.py (pure) and importer.py (orchestration): this
    module is the "pure" half for the work queue, work_queue.py is the
    "orchestration" half.

Ordering Rule:
    1. Items with a due_date sort before items without one - an
       undated item is not more urgent than a dated one by default.
    2. Among items with a due_date, earliest due_date first (overdue
       and due-soon items surface first).
    3. Items without a due_date keep a stable secondary order: earliest
       metadata.created_at first (oldest-queued-first), matching the
       plain FIFO behavior a salesperson would expect from an
       undifferentiated backlog.
    This is a first, deliberately simple rule - it does not yet
    consider WorkItemType, Lead territory, or any organizational
    priority signal. See the Non-Responsibilities note below.

Responsibilities:
    - order_work_items(): return a new list of WorkItems in the order
      above. Does not filter by status - callers decide which
      WorkItems to pass in (see WorkQueue.pending_items()).

Non-Responsibilities:
    - This module does not decide which WorkItems are eligible for the
      queue (status filtering) - that is work_queue.py's job.
    - This module does not consult Organizational Learning, Reasoning,
      or any confidence/priority score - a future slice may want
      priority-aware ordering, but Sprint 1's scope is a plain,
      explainable due-date-first queue, not a scored one.

Dependencies:
    argus.modules.sales.work_items (WorkItem).
"""

from typing import Iterable, List, Tuple

from argus.modules.sales.work_items.work_item import WorkItem


def _sort_key(work_item: WorkItem) -> Tuple[int, object]:
    if work_item.due_date is not None:
        return (0, work_item.due_date)
    return (1, work_item.metadata.created_at)


def order_work_items(work_items: Iterable[WorkItem]) -> List[WorkItem]:
    """
    Return a new list of the given WorkItems ordered per this module's
    Ordering Rule. Does not mutate or filter its input.

    Parameters:
        work_items: The WorkItems to order - typically the caller's
            still-open subset (see WorkQueue.pending_items()).

    Returns:
        A new list, sorted; the input is left unchanged.
    """
    return sorted(work_items, key=_sort_key)
