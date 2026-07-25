"""
WorkflowState for the ArgusOS Workflow Engine.

Purpose:
    Define the closed set of lifecycle states a single Workflow can
    occupy, per factory/packages/010_WORKFLOW_ENGINE.md. This is
    distinct from argus.lifecycle.LifecycleState, which tracks the
    WorkflowEngine *service's* own IService lifecycle - WorkflowState
    tracks an individual *workflow's* progress through execution.

Responsibilities:
    - Enumerate PENDING, RUNNING, COMPLETED, FAILED, CANCELLED as the
      only valid states a Workflow may be in.

Non-Responsibilities:
    - This module implements no transition logic. Transitions are
      enforced by WorkflowEngine (argus/workflow/engine.py), not by
      WorkflowState itself.

Dependencies:
    None (standard library only).
"""

from enum import Enum


class WorkflowState(Enum):
    """The only valid states a single Workflow may occupy."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
