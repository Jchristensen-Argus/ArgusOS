"""
Exceptions raised by the ArgusOS Connector Framework.

Purpose:
    Give callers explicit, catchable failure modes for connector
    registration, lookup, lifecycle, and invocation, per the coding
    standard's "raise meaningful exceptions... never silently ignore
    errors" and factory/packages/017_CONNECTOR_FRAMEWORK.md. Mirrors
    the exception hierarchy shape already established by
    argus.runtime.exceptions (Package 016), argus.planner.exceptions
    (Package 015), and argus.plugins.exceptions (Package 014).

Responsibilities:
    - Provide a general connector-subsystem error base, and more
      specific subtypes for "invalid input," "duplicate," "not
      found," "disabled," "invalid lifecycle state," and "invocation
      failed" failures.

Non-Responsibilities:
    - These exceptions carry no behavior beyond a message; they do
      not log, retry, or recover.

Dependencies:
    None.
"""


class ConnectorError(Exception):
    """Base exception for the connector subsystem. Raised directly for
    failures that are not one of the more specific subtypes below."""


class InvalidConnectorError(ConnectorError):
    """Raised when register_connector() is given something that is
    not a Connector instance, or a Connector with an empty id, name,
    or version - or when any lookup or lifecycle method is given
    something that is not the expected type (a non-string
    connector_id, a non-string/empty operation)."""


class DuplicateConnectorError(ConnectorError):
    """Raised when register_connector() is called with a connector_id
    that is already registered. Callers must call
    unregister_connector() first to replace an existing connector."""


class ConnectorNotFoundError(ConnectorError):
    """Raised when get_connector(), unregister_connector(),
    enable_connector(), disable_connector(), or invoke() references a
    connector_id with no corresponding registered Connector."""


class ConnectorDisabledError(ConnectorError):
    """Raised by invoke() when the referenced Connector's `enabled`
    flag is False. Callers must call enable_connector() first."""


class InvalidConnectorStateError(ConnectorError):
    """Raised by invoke() when the ConnectorManager's own IService
    lifecycle state is not RUNNING."""


class ConnectorInvocationError(ConnectorError):
    """Raised when a connector implementation's connect() or
    invoke() call raises. Wraps the underlying error; the triggering
    failure is published as CONNECTOR_FAILED before this is raised."""
