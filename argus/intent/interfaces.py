"""
Public interface contract for the ArgusOS Intent Router.

Purpose:
    Define IIntentRouter, the contract other modules depend on, per
    factory/packages/009_INTENT_ROUTER.md. IIntentRouter inherits
    IService, per this package's explicit requirement - Intent Router
    is the second class in this codebase (after Scheduler, Package
    008) to genuinely implement it. See this package's
    IMPLEMENTATION_REPORT.md for a note on how IntentRouter's
    IService adoption differs from Scheduler's: unlike Scheduler's
    tick(), none of parse()/route()/register_handler() are gated by
    lifecycle state, because IntentRouter has no background execution
    for start()/stop() to genuinely enable or disable.

Responsibilities:
    - IIntentRouter: parse / route / register_handler, plus the
      inherited initialize / start / stop / status from IService.

Non-Responsibilities:
    - This module implements no behavior; see
      argus.intent.router.IntentRouter.

Dependencies:
    argus.lifecycle.interfaces (IService), argus.intent.intent
    (Intent, IntentType).
"""

from abc import abstractmethod
from typing import Any, Callable

from argus.intent.intent import Intent, IntentType
from argus.lifecycle.interfaces import IService


class IIntentRouter(IService):
    """
    Parsing-and-routing contract for ArgusOS's deterministic intent
    infrastructure.

    Purpose:
        Let ArgusOS subsystems translate natural-language text into a
        structured Intent, and let interested services react to it via
        the Event Bus, without the router itself knowing anything
        about which services exist.
    """

    @abstractmethod
    def parse(self, text: str) -> Intent:
        """Classify `text` into an Intent, deterministically. Never
        raises for any string input, including unrecognized text
        (which resolves to IntentType.UNKNOWN) or an empty string.
        Raises IntentParseError if `text` is not a string at all.
        Publishes IntentParsed on success."""

    @abstractmethod
    def route(self, intent: Intent) -> None:
        """Publish `intent` on the Event Bus (EventType.INTENT_ROUTED)
        for any interested subscriber to react to, including handlers
        registered via register_handler(). Does not directly invoke
        any service. Raises InvalidIntentError if `intent` is not an
        Intent instance. Publishes IntentRouted on success."""

    @abstractmethod
    def register_handler(
        self, intent_name: IntentType, handler: Callable[[Intent], Any]
    ) -> None:
        """Register `handler` to be called (with the routed Intent)
        whenever route() routes an Intent whose name is `intent_name`.
        Implemented as a filtered subscription to the Event Bus's
        IntentRouted event, not a separate direct-dispatch path - see
        the module docstring. Raises DuplicateHandlerError if this
        exact (intent_name, handler) pair is already registered."""
