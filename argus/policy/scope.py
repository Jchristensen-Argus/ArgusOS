"""
The PolicyScope enumeration for the ArgusOS Policy Framework.

Purpose:
    Represent the closed set of organizational levels a Policy may
    eventually apply to, per
    factory/packages/040_POLICY_FRAMEWORK.md. "This enum simply
    describes where a policy may eventually apply. No inheritance or
    evaluation logic." A plain `Enum` (not a `str` subclass), mirroring
    every other enumeration in this codebase's own shape.

Descriptive Only - No Inheritance, No Evaluation, No Enforcement:
    Unlike a real scope/permission system, PolicyScope does not encode
    which levels contain which other levels, does not compute whether
    a GLOBAL-scoped Policy also applies at WORKSPACE scope, and is
    never consulted by any evaluation logic anywhere in this codebase
    - there is no evaluation logic to consult it, since no Policy
    Engine exists yet. A future package's own Policy Engine would be
    the place any such inheritance/evaluation semantics get built;
    this module only names the seven levels a Policy's own `scope`
    field may currently be labeled with.

Member Order Mirrors The Organizational Hierarchy, Widest First:
    GLOBAL, WORKSPACE, PROJECT, GOAL, PLAN, TASK, CAPABILITY - the
    same top-to-bottom order this codebase's own architectural
    hierarchy diagrams already use (`Workspace -> Project -> Goal ->
    Plan -> Task`), with GLOBAL prepended above Workspace (a Policy
    with no narrower scope, applying everywhere) and CAPABILITY
    appended below Task (the narrowest addressable unit introduced so
    far, Package 013/033/034). This ordering is presentational only -
    PolicyScope grants no ordering behavior (see the module's own "No
    Inheritance" note above); members compare only for
    equality/identity like every other enum in this codebase.

GLOBAL Is The Default:
    Continuing this codebase's own "the first-listed member is the
    default" convention, PolicyScope's own default is GLOBAL - a
    Policy built without an explicit scope is presumed to apply
    everywhere until a caller narrows it, the most conservative
    (widest) reading of an unspecified scope.

Responsibilities:
    - PolicyScope: enumerate the seven organizational levels a
      Policy's own `scope` field may currently be labeled with.

Non-Responsibilities:
    - This module implements no inheritance, evaluation, ordering, or
      enforcement logic of any kind - "No inheritance or evaluation
      logic."
    - This module implements no transition logic - scope, like
      priority on Goal (038)/DecisionRecord (039), was never described
      as something that transitions, but for the avoidance of doubt:
      nothing in argus.policy ever changes a Policy's own scope
      automatically.

Dependencies:
    None.
"""

from enum import Enum


class PolicyScope(Enum):
    """
    The closed set of organizational levels a Policy may currently be
    labeled as applying to. None of these members support ordering,
    inheritance, or evaluation against each other - "No inheritance or
    evaluation logic." See the module docstring for why member order
    mirrors this codebase's own organizational hierarchy diagrams
    without granting any behavioral significance to that order.

    GLOBAL: applies everywhere, no narrower scope. Default for every
        Policy built via PolicyBuilder that never calls with_scope().
    WORKSPACE: scoped to a single Workspace.
    PROJECT: scoped to a single Project.
    GOAL: scoped to a single Goal.
    PLAN: scoped to a single Plan.
    TASK: scoped to a single Task.
    CAPABILITY: scoped to a single Capability.
    """

    GLOBAL = "global"
    WORKSPACE = "workspace"
    PROJECT = "project"
    GOAL = "goal"
    PLAN = "plan"
    TASK = "task"
    CAPABILITY = "capability"
