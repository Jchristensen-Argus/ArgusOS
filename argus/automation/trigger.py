"""
The AutomationTrigger enumeration for the ArgusOS Automation
Framework.

Purpose:
    Represent the closed set of ways an Automation may eventually
    start, per factory/packages/041_AUTOMATION_FRAMEWORK.md. "This
    identifies how an automation may eventually start. Do not
    implement scheduling, event handling, or condition evaluation." A
    plain `Enum` (not a `str` subclass), mirroring every other
    enumeration in this codebase's own shape.

Descriptive Only - No Scheduling, No Event Handling, No Condition
Evaluation:
    AutomationTrigger does not implement a scheduler, does not listen
    for or dispatch events, and does not evaluate any condition -
    there is no scheduling/event/condition subsystem anywhere in this
    codebase for it to integrate with yet. A future package's own
    Automation Engine would be the place any such behavior gets built;
    this module only names the four ways an Automation's own `trigger`
    field may currently be labeled.

MANUAL Is The Default:
    Continuing this codebase's own "the first-listed member is the
    default" convention, AutomationTrigger's own default is MANUAL -
    an Automation built without an explicit trigger requires a human
    or caller to invoke it directly, the most conservative reading of
    an unspecified trigger (no autonomous behavior is implied by
    default). This happens to coincide with this package's own literal
    first-listed member, unlike GoalPriority (038) / DecisionRecord
    Priority (039), which each had to deliberately override that
    mechanical default - no such override is needed here, since MANUAL
    is simultaneously the first-listed member and the most
    conservative choice.

Responsibilities:
    - AutomationTrigger: enumerate the four ways an Automation's own
      `trigger` field may currently be labeled.

Non-Responsibilities:
    - This module implements no scheduling, event handling, or
      condition evaluation of any kind - "Do not implement scheduling,
      event handling, or condition evaluation."
    - This module implements no transition logic - nothing in
      argus.automation ever changes an Automation's own trigger
      automatically.

Dependencies:
    None.
"""

from enum import Enum


class AutomationTrigger(Enum):
    """
    The closed set of ways an Automation may currently be labeled as
    starting. None of these members support ordering, scheduling,
    event dispatch, or condition evaluation - "Do not implement
    scheduling, event handling, or condition evaluation."

    MANUAL: started directly by a human or caller. Default for every
        Automation built via AutomationBuilder that never calls
        with_trigger().
    SCHEDULE: intended to start on a time-based schedule. No scheduler
        exists in this codebase yet - this member is descriptive only.
    EVENT: intended to start in response to an event. No event-driven
        dispatch to Automation exists in this codebase yet - this
        member is descriptive only.
    CONDITION: intended to start when some condition is met. No
        condition evaluation exists in this codebase yet - this
        member is descriptive only.
    """

    MANUAL = "manual"
    SCHEDULE = "schedule"
    EVENT = "event"
    CONDITION = "condition"
