"""
argus.automation - The ArgusOS Automation Framework package.

Re-exports the public surface of the Automation Framework: the
immutable value objects (Automation, AutomationStatus,
AutomationTrigger, AutomationMetadata), the mutable builder
(AutomationBuilder) and its interface (IAutomationBuilder), and this
package's own exceptions. See
factory/packages/041_AUTOMATION_FRAMEWORK.md for the full architectural
rationale. "An Automation defines what should run, when it should run,
and under what conditions. It is a passive definition only. No
scheduler or execution engine belongs in this package." This package
introduces the Automation model only - no runtime behavior, no
scheduler, no automation engine, no bootstrap changes.
"""

from argus.automation.automation import Automation
from argus.automation.builder import AutomationBuilder
from argus.automation.exceptions import AutomationError, InvalidAutomationError
from argus.automation.interfaces import IAutomationBuilder
from argus.automation.metadata import (
    AUTOMATION_METADATA_VERSION,
    AutomationMetadata,
)
from argus.automation.status import AutomationStatus
from argus.automation.trigger import AutomationTrigger

__all__ = [
    "Automation",
    "AutomationStatus",
    "AutomationTrigger",
    "AutomationMetadata",
    "AUTOMATION_METADATA_VERSION",
    "AutomationBuilder",
    "IAutomationBuilder",
    "AutomationError",
    "InvalidAutomationError",
]
