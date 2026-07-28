"""
The Sales Lead Intake workflow for the Argus Sales OS Module (Sprint
1, Priority #6 - the complete vertical demonstration).

Purpose:
    Define the one Workflow Sprint 1 needs to prove the Sales vertical
    works end-to-end through Core's real Workflow Engine
    (argus.workflow, Package 010): import a CSV, put at least one
    Lead's work in front of a salesperson, advance it, and persist the
    result. This is orchestration glue across five already-independent
    Sales packages (import_pipeline, work_items, work_queue,
    persistence) - exactly what a Workflow's steps are for, per
    argus/workflow/workflow.py's own module docstring ("WorkflowEngine
    imposes no base class on actions - they are plain callables").

Not A New Business Rule - A Demonstration Choice, Named As Such:
    Step 2 below ("create_work_item_for_first_new_lead") creates one
    CALL WorkItem for the first Lead this run actually created. This
    is this workflow's own choice for proving the vertical end-to-end,
    NOT a claimed Sales business rule that every new Lead automatically
    gets a WorkItem. No such rule has been decided. A future slice
    should make that decision deliberately, with its own reasoning -
    this workflow should not be read as having quietly made it here.

Honesty Note - These Steps Are Not Strictly Deterministic:
    workflow.py's own module docstring says a step's action is
    "[d]eterministic by requirement... the same context must always
    produce the same result." The steps below read a real CSV file
    from disk, write real JSON files to disk, and construct
    entities/timestamps via `datetime.now()` and `uuid4()` - the same
    input file will not byte-for-byte reproduce the same output twice
    (fresh ids, fresh timestamps), the same way any real system's
    workflow step that touches the outside world cannot be pure. No
    other Workflow has been built yet in this codebase to establish
    real precedent either way; this is named explicitly rather than
    silently treated as compliant.

Responsibilities:
    - SALES_LEAD_INTAKE_WORKFLOW_ID: the stable id this Workflow is
      registered under, so callers can execute it by a known name
      rather than a random uuid.
    - build_sales_lead_intake_steps(): construct the ordered
      WorkflowStep sequence, closing over a SalesRepository and
      optional IEventBus supplied by the caller (registration.py).

Non-Responsibilities:
    - This module does not register the Workflow with a WorkflowEngine
      or construct a SalesRepository/IEventBus of its own - see
      registration.py, which is the only caller.
    - This module does not read command-line arguments or print
      anything - see sales_demo.py (repo root) for the minimal UI
      layer that reads the final context and presents it to a human.

Dependencies:
    argus.workflow (WorkflowStep), argus.events (IEventBus) - typing
    only, argus.modules.sales.import_pipeline (import_and_persist),
    argus.modules.sales.persistence (SalesRepository, load_work_queue,
    save_work_queue), argus.modules.sales.work_items (WorkItemBuilder,
    WorkItemType).
"""

from typing import Any, Mapping, Optional, Sequence

from argus.events.interfaces import IEventBus
from argus.modules.sales.persistence.repository import SalesRepository
from argus.modules.sales.persistence.session import (
    import_and_persist,
    load_work_queue,
    save_work_queue,
)
from argus.modules.sales.work_items.builder import WorkItemBuilder
from argus.modules.sales.work_items.work_type import WorkItemType
from argus.workflow.workflow import WorkflowStep

#: The stable id the Sales Lead Intake Workflow is registered under -
#: see registration.py's call to workflow_engine.register_workflow().
SALES_LEAD_INTAKE_WORKFLOW_ID = "sales_lead_intake"


def _import_leads(
    repository: SalesRepository,
    event_bus: Optional[IEventBus],
    context: Mapping[str, Any],
) -> Mapping[str, Any]:
    """
    Step 1: import context["csv_path"] and persist the result.

    Raises KeyError if context["csv_path"] is missing - this is a
    workflow *input* contract violation, and per IWorkflowEngine's own
    execute() contract, a step exception is caught by the engine
    (WorkflowFailed is published, the Workflow is marked FAILED) rather
    than propagating to the caller.
    """
    result = import_and_persist(repository, context["csv_path"], event_bus=event_bus)
    return {**context, "import_result": result}


def _create_work_item_for_first_new_lead(
    repository: SalesRepository,
    event_bus: Optional[IEventBus],
    context: Mapping[str, Any],
) -> Mapping[str, Any]:
    """
    Step 2: if this run created at least one new Lead, add one CALL
    WorkItem for the first of them to a freshly-loaded WorkQueue. See
    the module docstring's "Not A New Business Rule" note.

    event_bus is threaded through here (not just to
    _advance_top_work_item) because the WorkQueue itself, not the
    step, is what publishes WorkItemStarted/Completed - a WorkQueue
    built without an event_bus never publishes anything for its own
    lifetime, per work_queue.py's own "event_bus... optional" design.
    """
    import_result = context["import_result"]
    queue = load_work_queue(repository, event_bus=event_bus)
    work_item = None
    if import_result.leads:
        first_new_lead = import_result.leads[0]
        work_item = (
            WorkItemBuilder()
            .with_lead_id(first_new_lead.lead_id)
            .with_work_type(WorkItemType.CALL)
            .with_notes("Sales Lead Intake workflow: first-touch call")
            .build()
        )
        queue.add(work_item)
    return {**context, "work_queue": queue, "new_work_item": work_item}


def _advance_top_work_item(
    event_bus: Optional[IEventBus], context: Mapping[str, Any]
) -> Mapping[str, Any]:
    """
    Step 3: start() then complete() the queue's top pending item, if
    any - proving the full WorkItem transition surface, not just
    creation. A queue with nothing pending (e.g. an import that
    created no new Leads) is not an error; this step simply does
    nothing further.
    """
    queue = context["work_queue"]
    pending = queue.pending_items()
    completed_item = None
    if pending:
        top = pending[0]
        queue.start(top.work_item_id)
        completed_item = queue.complete(
            top.work_item_id, notes="Advanced by Sales Lead Intake workflow"
        )
    return {**context, "completed_work_item": completed_item}


def _persist_work_queue(
    repository: SalesRepository, context: Mapping[str, Any]
) -> Mapping[str, Any]:
    """Step 4: save the WorkQueue's current state - see
    work_queue.py's own "In-Memory Only" note; nothing durable happens
    to a WorkItem's status until this runs."""
    save_work_queue(repository, context["work_queue"])
    return context


def _summarize(context: Mapping[str, Any]) -> Mapping[str, Any]:
    """Step 5: build a plain, human-readable summary dict for
    sales_demo.py to print - kept separate from the live objects above
    so the UI layer never has to know about Importer/WorkQueue
    internals, only this flat summary."""
    import_result = context["import_result"]
    completed_item = context.get("completed_work_item")
    summary = {
        "rows_read": import_result.total_rows,
        "leads_created": import_result.leads_created,
        "companies_created": import_result.companies_created,
        "companies_reused": import_result.companies_reused,
        "contacts_created": import_result.contacts_created,
        "contacts_reused": import_result.contacts_reused,
        "campaigns_created": import_result.campaigns_created,
        "campaigns_reused": import_result.campaigns_reused,
        "import_errors": list(import_result.errors),
        "work_item_created": bool(context.get("new_work_item")),
        "work_item_completed": completed_item is not None,
        "completed_work_item_id": (
            completed_item.work_item_id if completed_item else None
        ),
    }
    return {**context, "summary": summary}


def build_sales_lead_intake_steps(
    *,
    repository: SalesRepository,
    event_bus: Optional[IEventBus] = None,
) -> Sequence[WorkflowStep]:
    """
    Build the Sales Lead Intake Workflow's ordered steps.

    Parameters:
        repository: Where imported entities and the WorkQueue are
            persisted. Constructed once by registration.py and closed
            over by every step below.
        event_bus: Passed through to import_and_persist() - if
            supplied, LeadImported/WorkItemStarted/WorkItemCompleted
            events publish exactly as they do outside a Workflow.

    Returns:
        Five WorkflowSteps in execution order: import_leads,
        create_work_item_for_first_new_lead, advance_top_work_item,
        persist_work_queue, summarize. Pass to
        IWorkflowEngine.register_workflow(steps=...).
    """
    return (
        WorkflowStep(
            name="import_leads",
            action=lambda context: _import_leads(repository, event_bus, context),
        ),
        WorkflowStep(
            name="create_work_item_for_first_new_lead",
            action=lambda context: _create_work_item_for_first_new_lead(
                repository, event_bus, context
            ),
        ),
        WorkflowStep(
            name="advance_top_work_item",
            action=lambda context: _advance_top_work_item(event_bus, context),
        ),
        WorkflowStep(
            name="persist_work_queue",
            action=lambda context: _persist_work_queue(repository, context),
        ),
        WorkflowStep(name="summarize", action=_summarize),
    )
