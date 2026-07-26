"""
Public re-exports for the ArgusOS Cognitive Pipeline package.

Purpose:
    Give callers a single, stable import surface
    (`from argus.pipeline import ...`) instead of reaching into
    individual submodules, matching the convention established by
    argus/planning/__init__.py, argus/context/__init__.py,
    argus/decision/__init__.py, argus/reasoning/__init__.py,
    argus/memory_integration/__init__.py, argus/knowledge_graph/__init__.py,
    argus/connectors/__init__.py, argus/runtime/__init__.py,
    argus/planner/__init__.py, and argus/plugins/__init__.py.

Dependencies:
    argus.pipeline.exceptions, argus.pipeline.interfaces,
    argus.pipeline.pipeline, argus.pipeline.request,
    argus.pipeline.result.
"""

from argus.pipeline.exceptions import (
    InvalidPipelineRequestError,
    PipelineError,
    PipelineExecutionError,
)
from argus.pipeline.interfaces import ICognitivePipeline
from argus.pipeline.pipeline import CognitivePipeline
from argus.pipeline.request import PipelineRequest
from argus.pipeline.result import PipelineResult

__all__ = [
    "ICognitivePipeline",
    "CognitivePipeline",
    "PipelineRequest",
    "PipelineResult",
    "PipelineError",
    "InvalidPipelineRequestError",
    "PipelineExecutionError",
]
