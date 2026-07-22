"""
Logging initialization for ArgusOS.

Purpose:
    Initialize application-wide logging per
    design/specifications/LOGGING.md, so that no part of the system
    needs to use print(), per the coding standard.

Scope:
    This is the minimal Bootstrap-stage implementation (Implementation
    Package 002). It configures the standard library logging module
    using the log level supplied by Configuration. Structured log
    storage, retention policies, audit logging, and log querying are
    infrastructure-level responsibilities deferred to a future
    implementation package.

Dependencies:
    Configuration, for the log level. LOGGING.md lists Configuration as
    a required dependency of the Logging Service, so Configuration must
    be loaded before logging is initialized.
"""

import logging
import sys
from typing import Optional

from argus.configuration import Configuration

LOGGER_NAME = "argus"


def initialize_logging(configuration: Configuration) -> logging.Logger:
    """
    Configure and return the ArgusOS application logger.

    Parameters:
        configuration: The loaded application Configuration, used to
            determine the log level.

    Returns:
        A configured Logger instance for the "argus" namespace.
    """
    logging_settings = configuration.get("logging", {})
    level_name = logging_settings.get("level", "INFO")
    level = getattr(logging, str(level_name).upper(), logging.INFO)

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(stream=sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.propagate = False
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieve a named logger under the "argus" namespace.

    Parameters:
        name: Optional sub-logger name (e.g. "bootstrap"). If omitted,
            returns the root "argus" logger.

    Returns:
        A Logger instance.
    """
    if name:
        return logging.getLogger(f"{LOGGER_NAME}.{name}")
    return logging.getLogger(LOGGER_NAME)
