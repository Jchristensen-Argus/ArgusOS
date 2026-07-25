"""
Public re-exports for the ArgusOS Intent Dispatcher package.

Purpose:
    Give callers a single, stable import surface
    (`from argus.dispatcher import ...`) instead of reaching into
    individual submodules, matching the convention established by
    argus/intent/__init__.py, argus/workflow/__init__.py, and
    argus/conversation/__init__.py.

Dependencies:
    argus.dispatcher.action, argus.dispatcher.exceptions,
    argus.dispatcher.interfaces, argus.dispatcher.dispatcher,
    argus.dispatcher.mapping.
"""

from argus.dispatcher.action import Action, WorkflowAction
from argus.dispatcher.dispatcher import IntentDispatcher
from argus.dispatcher.exceptions import (
    ActionExecutionError,
    DispatcherError,
    DuplicateMappingError,
    InvalidActionError,
    InvalidIntentError,
    MappingNotFoundError,
    NoMappingError,
)
from argus.dispatcher.interfaces import IIntentDispatcher
from argus.dispatcher.mapping import DEFAULT_WORKFLOW_IDS

__all__ = [
    "Action",
    "WorkflowAction",
    "IIntentDispatcher",
    "IntentDispatcher",
    "DEFAULT_WORKFLOW_IDS",
    "DispatcherError",
    "InvalidIntentError",
    "InvalidActionError",
    "NoMappingError",
    "DuplicateMappingError",
    "MappingNotFoundError",
    "ActionExecutionError",
]
