"""
Exceptions raised by the ArgusOS Capability Registry.

Purpose:
    Give callers explicit, catchable failure modes for capability
    registration and lookup, per the coding standard's "raise
    meaningful exceptions... never silently ignore errors" and
    factory/packages/013_CAPABILITY_REGISTRY.md.

Responsibilities:
    - Provide a general capability-subsystem error base, and more
      specific subtypes for "invalid capability," "duplicate," and
      "not found" failures, matching the exception hierarchy shape
      already established by argus.workflow.exceptions,
      argus.conversation.exceptions, and argus.dispatcher.exceptions.

Non-Responsibilities:
    - These exceptions carry no behavior beyond a message; they do
      not log, retry, or recover.

Dependencies:
    None.
"""


class CapabilityError(Exception):
    """Base exception for the capability subsystem. Raised directly
    for failures that are not one of the more specific subtypes
    below."""


class InvalidCapabilityError(CapabilityError):
    """Raised when register() is given something that is not a
    Capability instance, or a Capability with invalid field values
    (empty id/name, empty intent_types, empty action_kind, or a
    "workflow" action_kind with no workflow_id) - or when any lookup
    method is given something that is not the expected type
    (a non-string capability_id, a non-IntentType intent_type)."""


class DuplicateCapabilityError(CapabilityError):
    """Raised when register() is called with a capability_id that is
    already registered. Callers must call unregister() first to
    replace an existing capability."""


class CapabilityNotFoundError(CapabilityError):
    """Raised when get() or unregister() references a capability_id
    with no corresponding registered Capability."""
