"""
Public re-exports for the ArgusOS Intent Dispatcher package.

Purpose:
    Give callers a single, stable import surface
    (`from argus.dispatcher import ...`) instead of reaching into
    individual submodules, matching the convention established by
    argus/intent/__init__.py, argus/workflow/__init__.py, and
    argus/conversation/__init__.py.

Dependencies:
    argus.dispatcher.action, argus.dispatcher.dispatcher,
    argus.dispatcher.exceptions, argus.dispatcher.interfaces,
    argus.dispatcher.mapping.
"""

from argus.dispatcher.action import Action, WorkflowAction, build_action_from_capability
from argus.dispatcher.dispatcher import ActionFactory, IntentDispatcher
from argus.dispatcher.exceptions import (
    ActionExecutionError,
    DispatcherError,
    InvalidActionError,
    InvalidIntentError,
    NoCapabilityError,
)
from argus.dispatcher.interfaces import IIntentDispatcher
from argus.dispatcher.mapping import DEFAULT_WORKFLOW_IDS

__all__ = [
    "Action",
    "WorkflowAction",
    "build_action_from_capability",
    "IIntentDispatcher",
    "IntentDispatcher",
    "ActionFactory",
    "DEFAULT_WORKFLOW_IDS",
    "DispatcherError",
    "InvalidIntentError",
    "InvalidActionError",
    "NoCapabilityError",
    "ActionExecutionError",
]
