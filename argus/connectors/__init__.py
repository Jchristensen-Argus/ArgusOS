"""
Public re-exports for the ArgusOS Connector Framework package.

Purpose:
    Give callers a single, stable import surface
    (`from argus.connectors import ...`) instead of reaching into
    individual submodules, matching the convention established by
    argus/runtime/__init__.py, argus/planner/__init__.py,
    argus/plugins/__init__.py, and argus/capability/__init__.py.

Dependencies:
    argus.connectors.connector, argus.connectors.exceptions,
    argus.connectors.interfaces, argus.connectors.manager.
"""

from argus.connectors.connector import Connector
from argus.connectors.exceptions import (
    ConnectorDisabledError,
    ConnectorError,
    ConnectorInvocationError,
    ConnectorNotFoundError,
    DuplicateConnectorError,
    InvalidConnectorError,
    InvalidConnectorStateError,
)
from argus.connectors.interfaces import IConnector, IConnectorManager
from argus.connectors.manager import ConnectorManager, MockConnector

__all__ = [
    "Connector",
    "IConnector",
    "IConnectorManager",
    "ConnectorManager",
    "MockConnector",
    "ConnectorError",
    "InvalidConnectorError",
    "DuplicateConnectorError",
    "ConnectorNotFoundError",
    "ConnectorDisabledError",
    "InvalidConnectorStateError",
    "ConnectorInvocationError",
]
