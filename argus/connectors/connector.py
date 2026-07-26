"""
The Connector value object for the ArgusOS Connector Framework.

Purpose:
    Represent a single, immutable snapshot of one registered
    connector's identity and metadata - id, name, description,
    version, enabled flag, and the operations it exposes - per
    factory/packages/017_CONNECTOR_FRAMEWORK.md. A Connector is pure
    data: it does not connect to anything, does not invoke anything,
    and holds no live reference to the behavioral implementation that
    backs it. ConnectorManager (argus/connectors/manager.py) is the
    only component that advances a Connector's state, and does so by
    constructing new Connector instances via dataclasses.replace,
    never by mutating an existing one - matching the precedent set by
    PluginManager's treatment of Plugin (Package 014), Planner's
    treatment of Plan (Package 015), and AgentRuntime's treatment of
    Execution (Package 016).

Naming Note - `id`, not `connector_id`:
    This package's work order suggests `connector_id` as a Connector
    field name. Every prior value object in this codebase names its
    own identity field `id` (Capability.id, Plugin.id, Plan.id,
    PlanStep.id, Execution.id) and is referenced by outside callers
    via a `*_id`-suffixed parameter name instead (e.g.
    PluginManager.get(plugin_id)). This module follows that
    established convention: the field here is `id`; ConnectorManager's
    own public methods use `connector_id` for the parameter name that
    refers to it - exactly mirroring Execution.id vs.
    AgentRuntime.get_execution(execution_id) (Package 016's Decision
    5).

Capabilities Note - Plain Strings, Not the Capability Registry's
`Capability`:
    "capabilities" here means the set of operation names a connector
    exposes to invoke() (e.g. "send_email", "list_events") - a
    connector-local, descriptive concept. It is NOT
    argus.capability.capability.Capability, which is a Dispatcher-
    facing concept tied to IntentType/action_kind/workflow_id and has
    no relevance to external-system connectivity. Connector.capabilities
    is therefore modeled as a plain tuple of strings, and this module
    has no dependency on argus.capability - keeping the Connector
    Framework's "owns connectivity only" boundary intact.

Responsibilities:
    - Connector: hold connector identity and metadata as an immutable
      value object.

Non-Responsibilities:
    - Connector does not connect, disconnect, invoke, or health-check
      anything - see argus.connectors.interfaces.IConnector and
      argus.connectors.manager.MockConnector for the behavioral
      counterpart.
    - This module has no dependency on any other argus.connectors
      module, matching the "pure, dependency-free leaf" precedent set
      by argus.capability.capability, argus.plugins.plugin,
      argus.planner.plan, and argus.runtime.execution.

Dependencies:
    None beyond the standard library.
"""

import uuid
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class Connector:
    """
    An immutable record of one registered connector's identity and
    metadata.

    Purpose:
        Let ConnectorManager track what connectors exist, what they
        are called, what operations they expose, and whether they are
        currently enabled - without holding any live, callable
        reference to the implementation that actually performs
        connect()/invoke()/health_check() (that reference is held
        separately by ConnectorManager; see
        argus/connectors/manager.py).

    Fields:
        name: Human-readable connector name. Required, non-empty.
        description: Free-text description of what this connector
            does. Not validated beyond being a string.
        version: The connector's own version string. Required,
            non-empty.
        id: Unique identifier for this connector. Defaults to a
            fresh uuid4 string.
        enabled: Whether this connector may currently be invoked.
            Defaults to True. Set only by ConnectorManager.
            enable_connector()/disable_connector().
        capabilities: The operation names this connector exposes to
            invoke(). Defaults to an empty tuple. Purely descriptive
            in Version 1 - ConnectorManager.invoke() does not check
            that `operation` is a member of this tuple.
        metadata: Arbitrary additional information. Defaults to an
            empty mapping.
    """

    name: str
    description: str
    version: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    enabled: bool = True
    capabilities: Sequence[str] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "capabilities", tuple(self.capabilities))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
