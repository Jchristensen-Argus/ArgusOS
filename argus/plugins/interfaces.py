"""
Public interface contract for the ArgusOS Plugin Manager.

Purpose:
    Define IPluginManager, the contract other modules depend on, per
    factory/packages/014_PLUGIN_MANAGER.md.

Architectural Note - Why IPluginManager Does NOT Inherit IService:
    Unlike Scheduler, IntentRouter, WorkflowEngine, ConversationManager,
    and IntentDispatcher (Packages 008-012), PluginManager has no
    genuine multi-phase behavior: register/unregister/enable/disable/
    get/list_plugins/list_exported_capabilities/contains are all fully
    usable the instant the manager is constructed, with no background
    thread, no connection to open or close, and nothing meaningful for
    start()/stop() to enable or disable. enable()/disable() toggle the
    `enabled` flag on an individual, already-registered Plugin - they
    are registry-style operations on data the manager owns, exactly
    like Scheduler.pause()/resume() toggling an individual
    ScheduledTask's state (Package 008) without that implying anything
    about Scheduler's own IService lifecycle. Version 1 plugins are
    not required to execute real business logic ("Plugins are NOT
    required to execute real business logic yet" - this package's
    work order), so there is no "active work" phase for start()/stop()
    to gate either. Per ADR-0002's proposed criterion ("adopt
    IService only when start()/stop() would do real, distinct work"),
    this is architecturally identical to Knowledge Service (Package
    006), Memory Service (Package 007), and CapabilityRegistry
    (Package 013) - see design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md's
    Empirical Finding for this package. PluginManager is registered
    with the Lifecycle Manager as LifecycleState.REGISTERED only,
    exactly like those three, not as a fully-lifecycled IService
    adopter.

Responsibilities:
    - IPluginManager: register / unregister / enable / disable / get /
      list_plugins / list_exported_capabilities / contains.

Non-Responsibilities:
    - This module implements no behavior; see
      argus.plugins.manager.PluginManager.
    - IPluginManager does not dispatch intents and does not store
      capability metadata - see this package's Architectural Guidance
      and argus.dispatcher.dispatcher.IntentDispatcher /
      argus.capability.registry.CapabilityRegistry for those
      responsibilities.

Dependencies:
    argus.plugins.plugin (Plugin), argus.capability.capability
    (Capability).
"""

from abc import ABC, abstractmethod
from typing import Sequence

from argus.capability.capability import Capability
from argus.plugins.plugin import Plugin


class IPluginManager(ABC):
    """
    Metadata-and-lifecycle-only registry contract for everything
    installed into ArgusOS as a plugin.

    Purpose:
        Let callers register, discover, enumerate, and enable/disable
        Plugins, and expose the Capabilities those plugins export,
        without the manager itself executing anything or dispatching
        intents - see this module's Architectural Note for why this
        interface is a plain ABC rather than an IService.
    """

    @abstractmethod
    def register(self, plugin: Plugin) -> None:
        """Register `plugin`. Raises InvalidPluginError if plugin is
        not a Plugin instance, or has an empty id, empty name, empty
        version, empty author, or an exported_capabilities entry that
        is not a Capability instance. Raises DuplicatePluginError if
        plugin.id is already registered - call unregister() first to
        replace it."""

    @abstractmethod
    def unregister(self, plugin_id: str) -> None:
        """Remove the Plugin currently registered under plugin_id.
        Raises InvalidPluginError if plugin_id is not a string.
        Raises PluginNotFoundError if plugin_id has no registered
        Plugin."""

    @abstractmethod
    def enable(self, plugin_id: str) -> None:
        """Set enabled=True on the Plugin registered under plugin_id,
        replacing it in place. Raises InvalidPluginError if plugin_id
        is not a string. Raises PluginNotFoundError if plugin_id has
        no registered Plugin. Safe to call on an already-enabled
        plugin."""

    @abstractmethod
    def disable(self, plugin_id: str) -> None:
        """Set enabled=False on the Plugin registered under
        plugin_id, replacing it in place. Raises InvalidPluginError if
        plugin_id is not a string. Raises PluginNotFoundError if
        plugin_id has no registered Plugin. Safe to call on an
        already-disabled plugin."""

    @abstractmethod
    def get(self, plugin_id: str) -> Plugin:
        """Return the Plugin registered under plugin_id. Raises
        InvalidPluginError if plugin_id is not a string. Raises
        PluginNotFoundError if plugin_id has no registered Plugin."""

    @abstractmethod
    def list_plugins(self) -> Sequence[Plugin]:
        """Return every registered Plugin (enabled or disabled), in
        registration order."""

    @abstractmethod
    def list_exported_capabilities(self) -> Sequence[Capability]:
        """Return every Capability exported by every registered
        Plugin (enabled or disabled), in plugin-registration order
        and, within each plugin, in that plugin's own
        exported_capabilities order. A pure aggregation: applies no
        enabled/disabled policy on either the Plugin or the
        Capability - a caller wanting only enabled plugins' exports
        must filter list_plugins() itself. Does not register anything
        with the Capability Registry - see this package's Capability
        Integration guidance."""

    @abstractmethod
    def contains(self, plugin_id: str) -> bool:
        """Return True if plugin_id is currently registered, False
        otherwise. Never raises for any input, including a
        non-string plugin_id."""
