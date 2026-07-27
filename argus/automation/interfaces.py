"""
Interfaces for the ArgusOS Automation Framework package.

Purpose:
    Define IAutomationBuilder, the contract for a mutable, fluent
    Automation builder - per
    factory/packages/041_AUTOMATION_FRAMEWORK.md. This package
    introduces no new service; IAutomationBuilder therefore does not
    inherit IService, exactly mirroring IProjectBuilder (036),
    IWorkspaceBuilder (037), IGoalBuilder (038),
    IDecisionRecordBuilder (039), and IPolicyBuilder (040), none of
    which inherit IService either - a builder has no meaningful
    start/stop lifecycle of its own; it is a short-lived, per-use
    accumulator.

Responsibilities:
    - IAutomationBuilder: the contract implemented by
      AutomationBuilder.

Non-Responsibilities:
    - This module defines no concrete behavior - see builder.py.

Dependencies:
    argus.automation.automation (Automation), argus.automation.status
    (AutomationStatus), argus.automation.trigger (AutomationTrigger).
"""

from abc import ABC, abstractmethod
from typing import Any

from argus.automation.automation import Automation
from argus.automation.status import AutomationStatus
from argus.automation.trigger import AutomationTrigger


class IAutomationBuilder(ABC):
    """
    Contract for a mutable, fluent Automation builder. See this
    module's docstring for why IAutomationBuilder does not inherit
    IService.
    """

    @abstractmethod
    def with_name(self, name: str) -> "IAutomationBuilder":
        """Set this builder's name. A later call overwrites an
        earlier one - the last call before build() wins. Raises
        InvalidAutomationError if `name` is not a non-empty
        string."""

    @abstractmethod
    def with_description(self, description: str) -> "IAutomationBuilder":
        """Set this builder's description. A later call overwrites an
        earlier one - the last call before build() wins. Raises
        InvalidAutomationError if `description` is not a string."""

    @abstractmethod
    def with_status(self, status: AutomationStatus) -> "IAutomationBuilder":
        """Set this builder's status. A later call overwrites an
        earlier one - the last call before build() wins. Raises
        InvalidAutomationError if `status` is not an AutomationStatus
        instance."""

    @abstractmethod
    def with_trigger(self, trigger: AutomationTrigger) -> "IAutomationBuilder":
        """Set this builder's trigger. A later call overwrites an
        earlier one - the last call before build() wins. Raises
        InvalidAutomationError if `trigger` is not an
        AutomationTrigger instance."""

    @abstractmethod
    def with_metadata(self, key: str, value: Any) -> "IAutomationBuilder":
        """Set one arbitrary metadata key/value pair on the eventual
        AutomationMetadata.extra mapping. Accumulates across multiple
        calls; the same key overwrites - last call wins. Raises
        InvalidAutomationError if `key` is not a non-empty string."""

    @abstractmethod
    def build(self) -> Automation:
        """Construct and return a fresh, immutable Automation snapshot
        from this builder's current accumulated state."""
