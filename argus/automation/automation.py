"""
The Automation value object for the ArgusOS Automation Framework.

Purpose:
    Represent a single, immutable definition of what should run, when
    it should run, and under what conditions - "An Automation defines
    what should run, when it should run, and under what conditions. It
    is a passive definition only." per
    factory/packages/041_AUTOMATION_FRAMEWORK.md. "No scheduler or
    execution engine belongs in this package." This package introduces
    the Automation model only - no ownership relationship to
    Policy/Capability/Workspace/Project/Goal/Plan/Task/DecisionRecord/
    Events/Schedules is implemented yet; see "Future Relationship"
    below.

Every Field Defaults - Automation() Is Always Valid:
    Automation has its own dedicated AutomationBuilder - the same
    "value object with a dedicated builder" shape Project (036),
    Workspace (037), Goal (038), DecisionRecord (039), and Policy
    (040) all use, each of which lets every field default and leaves
    construction-time validation to the builder's own with_*() methods
    (see builder.py's own module docstring). `automation_id` defaults
    to a fresh uuid4 string, `name` and `description` both default to
    `""`, `status` defaults to `AutomationStatus.ACTIVE`, `trigger`
    defaults to `AutomationTrigger.MANUAL`, `metadata` defaults to a
    fresh `AutomationMetadata()`. `Automation()` with no arguments is
    therefore always valid.

A Sixth Field - trigger - Not Present On Project Or Workspace:
    Like `priority` on Goal (038)/DecisionRecord (039) and `scope` on
    Policy (040), `trigger` is a genuinely new top-level field,
    declared between `status` and `metadata` - continuing the "insert
    a new non-collection field before metadata, so metadata stays the
    last-declared field" positioning already used at Packages
    030/031/038/039/040. This package's own explicit field list names
    it directly - not an inference.

No Validation Here - See builder.py:
    Like every other value object in this codebase, Automation
    performs no validation of its own fields - it has no
    `__post_init__` at all.

Future Relationship - An Automation May Eventually Reference Policies,
Capabilities, Workspaces, Projects, Goals, Plans, Tasks, DecisionRecord,
Events, Schedules:
    Per this package's own explicit "Future Relationship" section:
    "Document these relationships only." Automation therefore holds no
    field referencing any of these in Version 1 - no `policies`
    collection, no `capability_id`, no scheduling hook of any kind.

Responsibilities:
    - Automation: hold identity (`automation_id`), a human-readable
      `name` and `description`, its own `status` and `trigger`, and
      descriptive `AutomationMetadata`, as an immutable value object.

Non-Responsibilities:
    - Automation performs no scheduling, event handling, condition
      evaluation, or execution of any kind - "It is a passive
      definition only."
    - Automation references nothing in Version 1 - see "Future
      Relationship" above.
    - This module depends only on argus.automation.status
      (AutomationStatus), argus.automation.trigger
      (AutomationTrigger), and argus.automation.metadata
      (AutomationMetadata) to type its own fields. It has no
      dependency on argus.automation.builder, matching the "pure,
      dependency-free leaf" precedent set by every other value object
      in this codebase.

Dependencies:
    argus.automation.status (AutomationStatus),
    argus.automation.trigger (AutomationTrigger),
    argus.automation.metadata (AutomationMetadata).
"""

import uuid
from dataclasses import dataclass, field

from argus.automation.metadata import AutomationMetadata
from argus.automation.status import AutomationStatus
from argus.automation.trigger import AutomationTrigger


@dataclass(frozen=True)
class Automation:
    """
    An immutable definition of what should run, when it should run,
    and under what conditions. See the module docstring for the full
    field semantics.

    Fields:
        automation_id: Unique identifier for this Automation. Defaults
            to a fresh uuid4 string.
        name: A short, human-readable label for this Automation.
            Defaults to an empty string.
        description: A longer, human-readable elaboration of what this
            Automation does. Defaults to an empty string.
        status: This Automation's current AutomationStatus. Defaults
            to AutomationStatus.ACTIVE.
        trigger: This Automation's current AutomationTrigger. Defaults
            to AutomationTrigger.MANUAL.
        metadata: Descriptive bookkeeping about this Automation.
            Defaults to a fresh AutomationMetadata.
    """

    automation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    status: AutomationStatus = AutomationStatus.ACTIVE
    trigger: AutomationTrigger = AutomationTrigger.MANUAL
    metadata: AutomationMetadata = field(default_factory=AutomationMetadata)
