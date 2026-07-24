"""
IntentRouter: deterministic parsing and Event-Bus-mediated routing for
the ArgusOS Intent Router.

Purpose:
    Implement IIntentRouter: classify text via argus.intent.parser,
    wrap the result in a full Intent, and publish it on the Event Bus
    for interested services to react to, per
    factory/packages/009_INTENT_ROUTER.md.

Responsibilities:
    - parse(text): validate input, delegate classification to
      argus.intent.parser.parse_text, wrap the result in an Intent,
      publish IntentParsed, and return it.
    - route(intent): validate input, publish IntentRouted. This is the
      *only* thing route() does - it never calls a service, or even a
      locally-registered handler, directly. "Interested services
      respond" exclusively by subscribing to the Event Bus.
    - register_handler(intent_name, handler): sugar over
      IEventBus.subscribe. Wraps `handler` in an adapter that
      subscribes to IntentRouted, filters by intent_name, reconstructs
      the routed Intent from the event payload, and invokes `handler`
      with it - catching and isolating any exception `handler` raises
      so one failing handler cannot prevent other IntentRouted
      subscribers (registered via this method or otherwise) from
      running. A caught handler failure publishes IntentFailed rather
      than propagating.
    - initialize / start / stop / status, per the inherited IService
      contract. Unlike Scheduler (Package 008), none of
      parse()/route()/register_handler() are gated by lifecycle state:
      IntentRouter has no background execution for start()/stop() to
      meaningfully enable or disable, so IService is implemented here
      to satisfy this package's explicit interface requirement and for
      consistency with the established lifecycle bookkeeping pattern,
      not because genuine phased behavior exists. This mirrors the
      exact duplicate-state risk already identified for Scheduler in
      ADR-0002 (design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md);
      see that document rather than repeating its analysis here.

Non-Responsibilities:
    - IntentRouter contains no service-specific knowledge: it never
      imports or references KnowledgeService, MemoryService, or
      Scheduler, and no intent classification branches into
      service-specific code anywhere in this module. Loose coupling is
      structural, not just documented.
    - No AI, no machine learning, no external libraries - all
      classification logic lives in argus.intent.parser, which is
      itself free of any of these.

Dependencies:
    argus.events (Event, EventType, IEventBus), argus.intent
    (Intent, IntentType, parse_text, and the intent exceptions),
    argus.lifecycle (LifecycleState).
"""

from datetime import datetime
from typing import Any, Callable, Dict, Tuple

from argus.events.event import Event
from argus.events.event_types import EventType
from argus.events.interfaces import IEventBus
from argus.intent.exceptions import (
    DuplicateHandlerError,
    IntentError,
    IntentParseError,
    InvalidIntentError,
)
from argus.intent.intent import Intent, IntentType
from argus.intent.interfaces import IIntentRouter
from argus.intent.parser import parse_text
from argus.lifecycle.lifecycle import LifecycleState


class IntentRouter(IIntentRouter):
    """
    Event-Bus-mediated implementation of IIntentRouter.

    Purpose:
        Translate natural-language text into a structured Intent and
        let interested services react to it, without the router
        knowing anything about which services exist or what they do.

    Responsibilities:
        - parse / route / register_handler, per IIntentRouter.
        - Track its own IService lifecycle state (see the module
          docstring's note on why this is not a genuine behavioral
          gate for this particular service).

    Dependencies:
        An IEventBus implementation, injected by the caller
        (bootstrap.py).
    """

    def __init__(self, event_bus: IEventBus) -> None:
        self._event_bus = event_bus
        self._state: LifecycleState = LifecycleState.CREATED
        # Keyed by (intent_name, handler) for duplicate detection;
        # values are the adapter functions actually subscribed to the
        # Event Bus, kept only so the mapping is inspectable/testable.
        self._handlers: Dict[Tuple[IntentType, Callable[[Intent], Any]], Callable[[Event], None]] = {}

    # -- IService -----------------------------------------------------

    def initialize(self) -> None:
        if self._state != LifecycleState.CREATED:
            raise IntentError(
                f"Cannot initialize: IntentRouter is {self._state.name}, expected CREATED."
            )
        self._state = LifecycleState.INITIALIZING

    def start(self) -> None:
        if self._state != LifecycleState.INITIALIZING:
            raise IntentError(
                f"Cannot start: IntentRouter is {self._state.name}, expected INITIALIZING."
            )
        self._state = LifecycleState.RUNNING

    def stop(self) -> None:
        if self._state != LifecycleState.RUNNING:
            raise IntentError(
                f"Cannot stop: IntentRouter is {self._state.name}, expected RUNNING."
            )
        self._state = LifecycleState.STOPPING
        self._state = LifecycleState.STOPPED

    def status(self) -> LifecycleState:
        return self._state

    # -- IIntentRouter --------------------------------------------------

    def parse(self, text: str) -> Intent:
        if not isinstance(text, str):
            error = IntentParseError(f"parse() requires a string, got {text!r}.")
            self._publish_failed("parse", str(error))
            raise error

        parsed = parse_text(text)
        intent = Intent(
            name=parsed.name,
            confidence=parsed.confidence,
            entities=parsed.entities,
            parameters=parsed.parameters,
        )
        self._event_bus.publish(
            Event(
                type=EventType.INTENT_PARSED,
                source="intent_router",
                payload=self._intent_to_payload(intent),
            )
        )
        return intent

    def route(self, intent: Intent) -> None:
        if not isinstance(intent, Intent):
            error = InvalidIntentError(f"route() requires an Intent, got {intent!r}.")
            self._publish_failed("route", str(error))
            raise error

        self._event_bus.publish(
            Event(
                type=EventType.INTENT_ROUTED,
                source="intent_router",
                payload=self._intent_to_payload(intent),
            )
        )

    def register_handler(
        self, intent_name: IntentType, handler: Callable[[Intent], Any]
    ) -> None:
        if not isinstance(intent_name, IntentType):
            raise InvalidIntentError(
                f"intent_name must be an IntentType, got {intent_name!r}."
            )
        if not callable(handler):
            raise InvalidIntentError(f"handler must be callable, got {handler!r}.")

        key = (intent_name, handler)
        if key in self._handlers:
            raise DuplicateHandlerError(
                f"Handler {handler!r} is already registered for {intent_name.name}."
            )

        def _adapter(event: Event) -> None:
            if event.payload.get("name") != intent_name.value:
                return
            try:
                handler(self._intent_from_payload(event.payload))
            except Exception as error:  # noqa: BLE001 - isolate one handler's failure
                self._publish_failed(
                    "handler",
                    f"Handler {handler!r} failed for intent {intent_name.name}: {error}",
                )

        self._event_bus.subscribe(EventType.INTENT_ROUTED, _adapter)
        self._handlers[key] = _adapter

    # -- internals ------------------------------------------------------

    def _publish_failed(self, stage: str, message: str) -> None:
        self._event_bus.publish(
            Event(
                type=EventType.INTENT_FAILED,
                source="intent_router",
                payload={"stage": stage, "error": message},
            )
        )

    @staticmethod
    def _intent_to_payload(intent: Intent) -> Dict[str, Any]:
        return {
            "id": intent.id,
            "name": intent.name.value,
            "confidence": intent.confidence,
            "entities": dict(intent.entities),
            "parameters": dict(intent.parameters),
            "timestamp": intent.timestamp.isoformat(),
        }

    @staticmethod
    def _intent_from_payload(payload) -> Intent:
        return Intent(
            id=payload["id"],
            name=IntentType(payload["name"]),
            confidence=payload["confidence"],
            entities=payload["entities"],
            parameters=payload["parameters"],
            timestamp=datetime.fromisoformat(payload["timestamp"]),
        )
