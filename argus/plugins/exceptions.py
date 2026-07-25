"""
Exceptions raised by the ArgusOS Plugin Manager.

Purpose:
    Give callers explicit, catchable failure modes for plugin
    registration and lookup, per the coding standard's "raise
    meaningful exceptions... never silently ignore errors" and
    factory/packages/014_PLUGIN_MANAGER.md. Mirrors the exception
    hierarchy shape already established by
    argus.capability.exceptions (Package 013),
    argus.dispatcher.exceptions (Package 012), and
    argus.workflow.exceptions (Package 010).

Responsibilities:
    - Provide a general plugin-subsystem error base, and more
      specific subtypes for "invalid plugin," "duplicate," and
      "not found" failures.

Non-Responsibilities:
    - These exceptions carry no behavior beyond a message; they do
      not log, retry, or recover.

Dependencies:
    None.
"""


class PluginError(Exception):
    """Base exception for the plugin subsystem. Raised directly for
    failures that are not one of the more specific subtypes below."""


class InvalidPluginError(PluginError):
    """Raised when register() is given something that is not a
    Plugin instance, or a Plugin with invalid field values (empty
    id/name/version/author, or an exported_capabilities entry that is
    not a Capability instance) - or when any lookup or lifecycle
    method is given something that is not the expected type (a
    non-string plugin_id)."""


class DuplicatePluginError(PluginError):
    """Raised when register() is called with a plugin_id that is
    already registered. Callers must call unregister() first to
    replace an existing plugin."""


class PluginNotFoundError(PluginError):
    """Raised when get(), unregister(), enable(), or disable()
    references a plugin_id with no corresponding registered
    Plugin."""
