"""
Public re-exports for the ArgusOS Intent Router package.

Purpose:
    Give callers a single, stable import surface
    (`from argus.intent import ...`) instead of reaching into
    individual submodules, matching the convention established by
    argus/memory/__init__.py and argus/scheduler/__init__.py.

Dependencies:
    argus.intent.exceptions, argus.intent.intent, argus.intent.parser,
    argus.intent.interfaces, argus.intent.router.
"""

from argus.intent.exceptions import (
    DuplicateHandlerError,
    IntentError,
    IntentParseError,
    InvalidIntentError,
)
from argus.intent.intent import Intent, IntentType
from argus.intent.interfaces import IIntentRouter
from argus.intent.parser import ParsedText, parse_text
from argus.intent.router import IntentRouter

__all__ = [
    "Intent",
    "IntentType",
    "IIntentRouter",
    "IntentRouter",
    "ParsedText",
    "parse_text",
    "IntentError",
    "IntentParseError",
    "InvalidIntentError",
    "DuplicateHandlerError",
]
