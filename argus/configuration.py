"""
Configuration loading for ArgusOS.

Purpose:
    Provide a single source of truth for configuration values needed
    during application startup, per design/specifications/CONFIGURATION.md.

Scope:
    This is the minimal Bootstrap-stage implementation (Implementation
    Package 002). It loads configuration once at startup and exposes
    read access. Validation, feature flags, environment layering,
    hot-reload, and change notification via the Event Bus are deferred
    to a future implementation package, since Event Bus initialization
    is explicitly out of scope for Package 002 - Bootstrap.

Dependencies:
    None (standard library only).
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

DEFAULT_CONFIG_PATH = Path("config/default.json")

DEFAULT_CONFIG: Dict[str, Any] = {
    "app_name": "ArgusOS",
    "environment": "development",
    "logging": {
        "level": "INFO",
    },
}


class ConfigurationError(Exception):
    """Raised when configuration cannot be loaded or parsed."""


class Configuration:
    """
    Holds configuration values loaded at startup.

    Responsibilities:
        - Load configuration from a JSON file, falling back to built-in
          defaults when no file is present.
        - Provide read access to configuration values.

    Non-Responsibilities (deferred to a future package):
        - Runtime validation
        - Feature flags
        - Hot reload
        - Change notification via the Event Bus

    Dependencies:
        None.
    """

    def __init__(self, values: Dict[str, Any]) -> None:
        self._values = values

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "Configuration":
        """
        Load configuration from a JSON file, merged over built-in defaults.

        Parameters:
            path: Optional path to a JSON configuration file. Defaults to
                config/default.json. If the file does not exist, the
                built-in defaults are used as-is.

        Returns:
            A populated Configuration instance.

        Raises:
            ConfigurationError: If the file exists but cannot be read or
                parsed.
        """
        config_path = path or DEFAULT_CONFIG_PATH

        if not config_path.exists():
            return cls(dict(DEFAULT_CONFIG))

        try:
            with config_path.open("r", encoding="utf-8") as file:
                values = json.load(file)
        except (OSError, json.JSONDecodeError) as error:
            raise ConfigurationError(
                f"Failed to load configuration from {config_path}: {error}"
            ) from error

        if not isinstance(values, dict):
            raise ConfigurationError(
                f"Configuration file {config_path} must contain a JSON object."
            )

        merged = {**DEFAULT_CONFIG, **values}
        return cls(merged)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a configuration value.

        Parameters:
            key: The configuration key to retrieve.
            default: Value returned if the key is not present.

        Returns:
            The configuration value, or the provided default.
        """
        return self._values.get(key, default)

    def as_dict(self) -> Dict[str, Any]:
        """Return a copy of all configuration values."""
        return dict(self._values)
