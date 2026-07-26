"""
Public re-exports for the ArgusOS Cognitive Context package.

Purpose:
    Give callers a single, stable import surface
    (`from argus.context import ...`) instead of reaching into
    individual submodules, matching the convention established by
    argus/decision/__init__.py, argus/reasoning/__init__.py,
    argus/memory_integration/__init__.py,
    argus/knowledge_graph/__init__.py, argus/connectors/__init__.py,
    argus/runtime/__init__.py, argus/planner/__init__.py, and
    argus/plugins/__init__.py.

Note:
    Unlike every other package listed above, this module re-exports
    no IService implementation and no EventType additions - Package
    022 introduces neither. See interfaces.py's own Architectural Note
    for why.

Dependencies:
    argus.context.builder, argus.context.context,
    argus.context.exceptions, argus.context.interfaces,
    argus.context.metadata.
"""

from argus.context.builder import ContextBuilder
from argus.context.context import CognitiveContext
from argus.context.exceptions import ContextError, InvalidContextError
from argus.context.interfaces import ICognitiveContextBuilder
from argus.context.metadata import CONTEXT_METADATA_VERSION, ContextMetadata

__all__ = [
    "ICognitiveContextBuilder",
    "ContextBuilder",
    "CognitiveContext",
    "ContextMetadata",
    "CONTEXT_METADATA_VERSION",
    "ContextError",
    "InvalidContextError",
]
