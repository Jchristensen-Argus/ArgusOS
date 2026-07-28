"""
The Sales vertical demonstration (Sprint 1, Priority #6).

Purpose:
    The minimal UI Sprint 1's own priority list asked for: "build only
    enough UI and workflow to prove the complete vertical works
    end-to-end." Not a graphical or web interface - none exists
    anywhere in this codebase to extend, and inventing one now would
    be exactly the unnecessary infrastructure this engagement has
    consistently avoided. This is a standalone, runnable script: boot
    Argus for real, load the Sales Module for real, run the real Sales
    Lead Intake Workflow against a real CSV through the real Workflow
    Engine, and print what happened in plain text.

What This Proves, Concretely:
    Running `python sales_demo.py` exercises, in one process, through
    real Core services (not a hand-written verification script):
    Domain Models -> Import Pipeline -> Session Persistence -> Work
    Queue -> Plugin Manager (registration) -> Workflow Engine -> Event
    Bus (LeadImported/WorkItemStarted/WorkItemCompleted all publish
    for real during this run). This is the "complete vertical" Sprint
    1 set out to deliver.

Usage:
    python sales_demo.py [path/to/leads.csv]
    Defaults to samples/lead_workspace_sample.csv if no path is given.
    Safe to run more than once - the second run will dedup against
    what the first run persisted to sales_data/, exactly like any two
    real import runs would (see persistence/session.py).

Non-Responsibilities:
    - This script defines no business logic of its own - every step
      it triggers is defined in argus/modules/sales/workflows.py; this
      file only boots the application, loads Modules, executes the
      Workflow, and prints its result.
"""

import sys
from pathlib import Path

from argus.bootstrap import bootstrap
from argus.modules.sales.workflows import SALES_LEAD_INTAKE_WORKFLOW_ID
from argus.workflow.state import WorkflowState
from module_loader import load_modules

DEFAULT_SAMPLE_CSV = Path(__file__).parent / "samples" / "lead_workspace_sample.csv"


def _print_summary(summary: dict) -> None:
    print("Sales Lead Intake - Workflow Result")
    print("-" * 40)
    print(f"Rows read:           {summary['rows_read']}")
    print(f"Leads created:       {summary['leads_created']}")
    print(
        f"Companies:           {summary['companies_created']} created, "
        f"{summary['companies_reused']} reused"
    )
    print(
        f"Contacts:            {summary['contacts_created']} created, "
        f"{summary['contacts_reused']} reused"
    )
    print(
        f"Campaigns:           {summary['campaigns_created']} created, "
        f"{summary['campaigns_reused']} reused"
    )
    if summary["import_errors"]:
        print(f"Import errors:       {len(summary['import_errors'])}")
        for error in summary["import_errors"]:
            print(f"  - {error}")
    else:
        print("Import errors:       none")
    print(f"Work item created:   {summary['work_item_created']}")
    print(f"Work item completed: {summary['work_item_completed']}")
    if summary["completed_work_item_id"]:
        print(f"  work_item_id:      {summary['completed_work_item_id']}")


def main() -> int:
    csv_path = sys.argv[1] if len(sys.argv) > 1 else str(DEFAULT_SAMPLE_CSV)

    application = bootstrap()
    try:
        load_modules(application.container)
        workflow_engine = application.container.resolve("workflow_engine")

        context = workflow_engine.execute(
            SALES_LEAD_INTAKE_WORKFLOW_ID, context={"csv_path": csv_path}
        )
        workflow = workflow_engine.get_workflow(SALES_LEAD_INTAKE_WORKFLOW_ID)

        if workflow.state != WorkflowState.COMPLETED:
            print(f"Workflow ended in state {workflow.state.name}, not COMPLETED.")
            print("Context at failure:", dict(context))
            return 1

        _print_summary(context["summary"])
        return 0
    finally:
        application.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
