"""
Default intent-to-workflow mapping table for the ArgusOS Intent
Dispatcher.

Purpose:
    Hold the five Version 1 "Initial mappings" required by
    factory/packages/012_INTENT_DISPATCHER.md as pure data, separate
    from dispatcher.py - so dispatcher.py's own source never contains
    a literal mapping value, per that work order's explicit "Mappings
    must not be hard-coded inside dispatcher.py" requirement.

Responsibilities:
    - DEFAULT_WORKFLOW_IDS: a closed table pairing each IntentType
      with the conventional workflow_id bootstrap.py registers a
      WorkflowAction against for that intent (see
      argus/bootstrap.py). This module does not construct any
      WorkflowAction itself, and does not import argus.workflow at
      all - it has no way to know whether a workflow with a given id
      is actually registered in a live IWorkflowEngine, and does not
      need to: that is resolved at dispatch() time (a workflow_id
      with nothing registered against it in IWorkflowEngine fails with
      WorkflowNotFoundError when actually dispatched, exactly as it
      would for ConversationManager.receive() - see
      argus/conversation/manager.py's Non-Responsibilities for the
      identical assumption).

Non-Responsibilities:
    - This module registers nothing. It is a pure lookup table;
      whoever wires the dispatcher (bootstrap.py in Version 1) is
      responsible for actually calling register_mapping() with it.
    - This module does not validate that any workflow_id here
      corresponds to a workflow that has been, or ever will be,
      registered with a live IWorkflowEngine.

Dependencies:
    argus.intent.intent (IntentType).
"""

from types import MappingProxyType
from typing import Mapping

from argus.intent.intent import IntentType

# The Version 1 "Initial mappings," per
# factory/packages/012_INTENT_DISPATCHER.md:
#     QUESTION -> Answer Workflow
#     COMMAND  -> Command Workflow
#     MEMORY   -> Memory Workflow
#     SCHEDULE -> Reminder Workflow
#     UNKNOWN  -> Unknown Handler Workflow
#
# These workflow_id strings are a naming convention only - no workflow
# actually implementing "answer," "command," "memory," "reminder," or
# "unknown handling" business logic is created by this package (doing
# so would mean inventing unspecified Workflow step content, which is
# out of this package's scope). bootstrap.py registers a WorkflowAction
# for each of these five workflow_ids at startup; until some other
# component actually calls IWorkflowEngine.register_workflow() with a
# matching workflow_id, dispatching any of these five intents will
# raise (wrapped as ActionExecutionError) via IWorkflowEngine's own
# WorkflowNotFoundError, exactly like an unregistered workflow_id
# passed to ConversationManager.receive() today.
DEFAULT_WORKFLOW_IDS: Mapping[IntentType, str] = MappingProxyType(
    {
        IntentType.QUESTION: "answer_workflow",
        IntentType.COMMAND: "command_workflow",
        IntentType.MEMORY: "memory_workflow",
        IntentType.SCHEDULE: "reminder_workflow",
        IntentType.UNKNOWN: "unknown_handler_workflow",
    }
)
