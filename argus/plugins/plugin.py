"""
The Plugin value object for the ArgusOS Plugin Manager.

Purpose:
    Represent a single, immutable description of one installable unit
    of extension for ArgusOS - metadata only, per
    factory/packages/014_PLUGIN_MANAGER.md. A Plugin is pure data: it
    does not execute anything, does not hold a live service reference,
    and does not register itself anywhere - that is
    PluginManager.register()'s and, separately, bootstrap.py's
    responsibility (see this package's module docstring for
    argus.plugins.manager) - matching the precedent set by every
    other value object in this codebase (Capability, Workflow, Intent,
    ConversationSession) holding no live service reference of its
    own.

Responsibilities:
    - Hold identity (id), descriptive metadata (name, version, author,
      description), whether the plugin is currently enabled, the
      Capabilities this plugin exports (exported_capabilities), and
      arbitrary caller metadata.
    - Auto-generate `id` when not supplied. Guarantee immutability
      (frozen dataclass) and prevent mutation of the
      `exported_capabilities` sequence or `metadata` mapping after
      construction.

Non-Responsibilities:
    - Plugin does not validate its own fields (for example, that name
      is non-empty, or that every exported_capabilities entry is a
      Capability) - that is PluginManager.register()'s
      responsibility, matching the validation precedent set by
      Capability/Intent/Workflow: data objects across this codebase
      contain no business logic.
    - Plugin does not register its exported_capabilities with the
      Capability Registry, and does not construct, obtain, or
      reference any IPluginManager, ICapabilityRegistry, Action, or
      IWorkflowEngine - it is pure, serializable-shaped data.

Dependencies:
    argus.capability.capability (Capability), for typing
    exported_capabilities.
"""

import uuid
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from argus.capability.capability import Capability


@dataclass(frozen=True)
class Plugin:
    """
    An immutable record describing one installable unit of extension
    for ArgusOS.

    Purpose:
        Let the Plugin Manager (and, later, the Capability Registry
        via a caller such as bootstrap.py) describe and discover
        installed plugins and the Capabilities they export, without
        any of them executing anything - see the module docstring.

    Responsibilities:
        - Store name, version, author, description, id, enabled,
          exported_capabilities, and metadata.
        - Auto-generate `id` when not supplied, default `enabled` to
          True, `exported_capabilities` to an empty sequence, and
          `metadata` to an empty mapping, and make
          `exported_capabilities` and `metadata` immutable
          containers.

    Dependencies:
        None.
    """

    name: str
    version: str
    author: str
    description: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    enabled: bool = True
    exported_capabilities: Sequence[Capability] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Frozen dataclasses require object.__setattr__ during
        # __post_init__. Wrapping `exported_capabilities` in a tuple
        # and `metadata` in MappingProxyType makes the containers
        # themselves read-only, not just the attribute reference -
        # the same pattern used by Capability.intent_types/metadata
        # (Package 013) and Workflow.steps/metadata (Package 010).
        object.__setattr__(
            self, "exported_capabilities", tuple(self.exported_capabilities)
        )
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
