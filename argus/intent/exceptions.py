"""
Exceptions raised by the ArgusOS Intent Router.

Purpose:
    Give callers explicit, catchable failure modes for intent parsing
    and routing operations, per the coding standard's "explicit
    exceptions instead of silent failures" and
    factory/packages/009_INTENT_ROUTER.md.

Responsibilities:
    - Provide a general intent-subsystem error base, and more specific
      subtypes for parse-input, route-input, and duplicate-handler
      failures, so callers can catch either the broad or the precise
      failure mode.

Non-Responsibilities:
    - These exceptions carry no behavior beyond a message; they do not
      log, retry, or recover.
    - A handler raising during dispatch does not use any of these
      types - IntentRouter catches the handler's own exception as-is
      and reports it via an IntentFailed event; see
      argus/intent/router.py.

Dependencies:
    None.
"""


class IntentError(Exception):
    """Base exception for the intent subsystem. Raised directly for
    failures that are not one of the more specific subtypes below."""


class IntentParseError(IntentError):
    """Raised by IIntentRouter.parse() when given input that is not a
    string at all (for example None, or a non-str object). Any actual
    string content, however unrecognized, resolves to a valid UNKNOWN
    Intent instead of raising - see argus/intent/parser.py."""


class InvalidIntentError(IntentError):
    """Raised by IIntentRouter.route() when given an object that is
    not an Intent instance."""


class DuplicateHandlerError(IntentError):
    """Raised by IIntentRouter.register_handler() when the exact same
    (intent_name, handler) pair is already registered."""
