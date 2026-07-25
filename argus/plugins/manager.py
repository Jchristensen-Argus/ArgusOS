"""
PluginManager: in-memory, metadata-and-lifecycle-only implementation
of IPluginManager for the ArgusOS Plugin Manager.

Purpose:
    Implement IPluginManager: store, validate, and let callers
    discover and enable/disable Plugin metadata, per
    factory/packages/014_PLUGIN_MANAGER.md. The manager performs NO
    execution and NO intent dispatch - it never constructs, obtains,
    or calls an Action, never touches IWorkflowEngine or
    IIntentDispatcher, and never registers anything with the
    Capability Registry itself (see this module's Capability
    Integration note below).

Responsibilities:
    - register / unregister / enable / disable / get / list_plugins /
      list_exported_capabilities / contains: an in-memory registry of
      Plugin objects, keyed by id. All eight methods are always
      available - PluginManager is not an IService adopter (see
      argus/plugins/interfaces.py's Architectural Note), so there is
      no lifecycle state to gate any of them on.
    - register() validates a Plugin's fields before accepting it
      (non-empty id/name/version/author, and that every
      exported_capabilities entry is a Capability instance) - the one
      piece of business logic this module contains, and it is
      validation, not execution, matching the precedent set by
      CapabilityRegistry.register()'s own inline validation (Package
      013).
    - enable()/disable() replace the stored Plugin with a copy whose
      `enabled` flag has been flipped (via dataclasses.replace,
      since Plugin is frozen), keyed under the same id. Both are
      idempotent in effect: calling enable() on an already-enabled
      plugin (or disable() on an already-disabled one) still succeeds
      and still publishes the corresponding event, keeping the
      implementation simple rather than adding conditional
      no-op-detection this package's work order does not ask for.
    - Publishes PluginRegistered on every successful register(),
      PluginUnregistered on every successful unregister(),
      PluginEnabled on every successful enable(), and PluginDisabled
      on every successful disable() - mirroring
      CapabilityRegistry's CapabilityRegistered/CapabilityUnregistered
      precedent (Package 013) for a metadata CRUD store, extended with
      two more events for this package's two additional lifecycle
      operations.

Capability Integration:
    list_exported_capabilities() is the sole integration point with
    the Capability Registry, and it is one-directional and read-only:
    PluginManager exposes the Capabilities its registered Plugins
    export; it never imports argus.capability.registry and never
    calls ICapabilityRegistry.register() itself. Actually registering
    a plugin's exported Capabilities with the Capability Registry is
    left to the caller (bootstrap.py in Version 1) - see this
    package's Bootstrap Integration guidance and
    factory/packages/014_PLUGIN_MANAGER.md's Architectural Decisions.
    This keeps CapabilityRegistry unmodified and un-redesigned, per
    this package's explicit "Do not redesign the Capability Registry.
    Integrate only where necessary" instruction.

Non-Responsibilities:
    - PluginManager never dispatches intents, never selects "the"
      plugin or capability for anything, and never filters by the
      `enabled` flag on either Plugin or Capability in
      list_plugins()/list_exported_capabilities() - both are pure
      enumerations. Any such policy belongs to whichever future
      caller needs it, not to this registry - matching
      CapabilityRegistry.find_by_intent_type()'s identical
      no-policy precedent (Package 013).
    - No AI, no LLM, no networking, no persistence, no plugin
      discovery from disk/entry points - Plugins are held only in
      memory and registered explicitly by a caller, exactly like
      CapabilityRegistry's Capabilities and WorkflowEngine's
      Workflows. Version 1 plugins are not required to execute real
      business logic - this module never attempts to call into one.

Dependencies:
    argus.plugins (Plugin, IPluginManager, and the plugin
    exceptions), argus.capability.capability (Capability, for typing
    list_exported_capabilities()'s return value only), argus.events
    (Event, EventType, IEventBus).
"""

from dataclasses import replace
from typing import Dict, List, Sequence

from argus.capability.capability import Capability
from argus.events.event import Event
from argus.events.event_types import EventType
from argus.events.interfaces import IEventBus
from argus.plugins.exceptions import (
    DuplicatePluginError,
    InvalidPluginError,
    PluginNotFoundError,
)
from argus.plugins.interfaces import IPluginManager
from argus.plugins.plugin import Plugin


class PluginManager(IPluginManager):
    """
    In-memory implementation of IPluginManager.

    Purpose:
        Be the central mechanism for extending ArgusOS without
        modifying the core application, as metadata and lifecycle
        state only. See the module docstring for the full design
        rationale.

    Dependencies:
        An IEventBus implementation, injected by the caller
        (bootstrap.py).
    """

    def __init__(self, event_bus: IEventBus) -> None:
        self._event_bus = event_bus
        self._plugins: Dict[str, Plugin] = {}

    def register(self, plugin: Plugin) -> None:
        self._validate_plugin(plugin)
        if plugin.id in self._plugins:
            raise DuplicatePluginError(
                f"A plugin with id {plugin.id!r} is already registered."
            )
        self._plugins[plugin.id] = plugin
        self._publish(
            EventType.PLUGIN_REGISTERED,
            {"plugin_id": plugin.id, "name": plugin.name},
        )

    def unregister(self, plugin_id: str) -> None:
        plugin = self._require_plugin(plugin_id)
        del self._plugins[plugin_id]
        self._publish(
            EventType.PLUGIN_UNREGISTERED,
            {"plugin_id": plugin.id, "name": plugin.name},
        )

    def enable(self, plugin_id: str) -> None:
        plugin = self._require_plugin(plugin_id)
        self._plugins[plugin_id] = replace(plugin, enabled=True)
        self._publish(
            EventType.PLUGIN_ENABLED,
            {"plugin_id": plugin.id, "name": plugin.name},
        )

    def disable(self, plugin_id: str) -> None:
        plugin = self._require_plugin(plugin_id)
        self._plugins[plugin_id] = replace(plugin, enabled=False)
        self._publish(
            EventType.PLUGIN_DISABLED,
            {"plugin_id": plugin.id, "name": plugin.name},
        )

    def get(self, plugin_id: str) -> Plugin:
        return self._require_plugin(plugin_id)

    def list_plugins(self) -> Sequence[Plugin]:
        return tuple(self._plugins.values())

    def list_exported_capabilities(self) -> Sequence[Capability]:
        capabilities: List[Capability] = []
        for plugin in self._plugins.values():
            capabilities.extend(plugin.exported_capabilities)
        return tuple(capabilities)

    def contains(self, plugin_id: str) -> bool:
        return isinstance(plugin_id, str) and plugin_id in self._plugins

    # -- internals ------------------------------------------------------

    def _require_plugin(self, plugin_id: str) -> Plugin:
        if not isinstance(plugin_id, str):
            raise InvalidPluginError(
                f"plugin_id must be a string, got {plugin_id!r}."
            )
        try:
            return self._plugins[plugin_id]
        except KeyError:
            raise PluginNotFoundError(
                f"No plugin registered with id {plugin_id!r}."
            ) from None

    @staticmethod
    def _validate_plugin(plugin: Plugin) -> None:
        if not isinstance(plugin, Plugin):
            raise InvalidPluginError(
                f"register() requires a Plugin, got {plugin!r}."
            )
        if not plugin.id:
            raise InvalidPluginError("Plugin.id must be non-empty.")
        if not plugin.name:
            raise InvalidPluginError("Plugin.name must be non-empty.")
        if not plugin.version:
            raise InvalidPluginError("Plugin.version must be non-empty.")
        if not plugin.author:
            raise InvalidPluginError("Plugin.author must be non-empty.")
        for capability in plugin.exported_capabilities:
            if not isinstance(capability, Capability):
                raise InvalidPluginError(
                    f"Every entry in Plugin.exported_capabilities must be a "
                    f"Capability, got {capability!r}."
                )

    def _publish(self, event_type: EventType, payload: dict) -> None:
        self._event_bus.publish(
            Event(type=event_type, source="plugin_manager", payload=payload)
        )
