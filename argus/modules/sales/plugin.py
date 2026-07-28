"""
Plugin registration for the Argus Sales OS Module.

Purpose:
    Provide the one, documented entry point through which
    argus.modules.sales registers itself with Core's existing Plugin
    Manager (argus.plugins, Package 014) - per the founder's own
    framing, confirmed against the real code before building this:
    "the Sales Module should simply register itself with the core
    framework and expose workflows," and Plugin Manager already is
    that mechanism.

Correction Made Before Writing This File:
    An earlier architecture document (ARGUS_SALES_OS_V1_ARCHITECTURE.md)
    described this as "SalesPlugin(Plugin) - registration entry
    point," implying a subclass. Reading the real
    argus/plugins/plugin.py first showed that's wrong: Plugin is a
    frozen dataclass, not meant to be subclassed - the same "value
    object, no behavior" shape every other entity in this codebase
    uses (Task, Lead, Company...). The real pattern, confirmed against
    PluginManager's own register(plugin: Plugin) signature, is a
    factory function that builds and returns a Plugin instance for a
    caller to register - not a class hierarchy.

No Exported Capabilities Yet:
    Plugin.exported_capabilities lets a Plugin advertise Capability
    instances (Package 013) it makes available - Sprint 1 has no
    Capability of its own yet (Prospect Intelligence and the Email
    Engine, both of which would plausibly need one, are out of
    Sprint 1's scope per ARGUS_SALES_OS_V1_ARCHITECTURE.md). build_
    sales_plugin() therefore exports none, matching Plugin's own
    default. This is not a gap to fix now - a Capability only makes
    sense once there's real behavior to wrap.

Where Registration Actually Happens - An Open Item, Not Solved Here:
    build_sales_plugin() only builds the Plugin value; something must
    still call plugin_manager.register(build_sales_plugin()) once, at
    startup. Core's own bootstrap.py cannot be that caller - Core must
    never import argus.modules (Cognitive Architecture, CA-10), and
    main.py currently calls bootstrap() and nothing else. No
    "load Modules after Core boots" step exists anywhere in this
    repository yet. That composition-root addition belongs outside
    Core - most naturally in main.py itself, since main.py already
    sits outside the Core/Module boundary as the entry point - but
    adding it wasn't asked for as part of this slice and is flagged
    here rather than done unprompted.

Responsibilities:
    - build_sales_plugin(): construct and return the Plugin describing
      the Sales Module.

Non-Responsibilities:
    - This module does not call PluginManager.register() itself, does
      not construct a PluginManager, and does not import
      argus.bootstrap - registration is left to whatever composition
      root eventually wires Modules in, per the open item above.

Dependencies:
    argus.plugins (Plugin).
"""

from argus.plugins.plugin import Plugin

#: This Module's own version, independent of CORE_SERVICES_VERSION
#: (argus/bootstrap.py) and independent of any individual entity's own
#: *_METADATA_VERSION - this versions the Sales Module as a whole.
SALES_MODULE_VERSION = "0.1.0"


def build_sales_plugin() -> Plugin:
    """
    Build the Plugin value describing the Sales Module, ready to be
    passed to IPluginManager.register() by whatever caller performs
    Module loading.

    Returns:
        A Plugin with name="Sales", this module's own version, no
        exported_capabilities yet (see the module docstring), and
        enabled=True (Plugin's own default).
    """
    return Plugin(
        name="Sales",
        version=SALES_MODULE_VERSION,
        author="Argus Factory",
        description=(
            "AI Sales Operating System for a packaging salesperson - "
            "Lead Workspace, Work Queue, Prospect Intelligence, Email "
            "Engine. Sprint 1 scope: Lead Workspace foundation only."
        ),
    )
