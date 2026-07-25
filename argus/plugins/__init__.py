"""
Public re-exports for the ArgusOS Plugin Manager package.

Purpose:
    Give callers a single, stable import surface
    (`from argus.plugins import ...`) instead of reaching into
    individual submodules, matching the convention established by
    argus/capability/__init__.py, argus/workflow/__init__.py, and
    argus/dispatcher/__init__.py.

Dependencies:
    argus.plugins.plugin, argus.plugins.exceptions,
    argus.plugins.interfaces, argus.plugins.manager.
"""

from argus.plugins.exceptions import (
    DuplicatePluginError,
    InvalidPluginError,
    PluginError,
    PluginNotFoundError,
)
from argus.plugins.interfaces import IPluginManager
from argus.plugins.manager import PluginManager
from argus.plugins.plugin import Plugin

__all__ = [
    "Plugin",
    "IPluginManager",
    "PluginManager",
    "PluginError",
    "InvalidPluginError",
    "DuplicatePluginError",
    "PluginNotFoundError",
]
