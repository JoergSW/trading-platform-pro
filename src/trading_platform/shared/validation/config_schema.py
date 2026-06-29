from __future__ import annotations

from typing import Any

from trading_platform.shared.exceptions.base import ConfigurationError


REQUIRED_APPLICATION_KEYS = frozenset(
    {
        "name",
        "profile",
    }
)


def validate_application_config(settings: dict[str, Any]) -> None:
    if not isinstance(settings, dict):
        raise ConfigurationError(
            "Configuration root must be a dictionary."
        )

    application = settings.get("application")

    if not isinstance(application, dict):
        raise ConfigurationError(
            "Missing required configuration section: application."
        )

    missing = sorted(
        REQUIRED_APPLICATION_KEYS.difference(application.keys())
    )

    if missing:
        raise ConfigurationError(
            "Missing application configuration keys: "
            + ", ".join(missing)
        )

    for key in REQUIRED_APPLICATION_KEYS:
        value = application[key]

        if not isinstance(value, str):
            raise ConfigurationError(
                f"Configuration value 'application.{key}' must be a string."
            )

        if not value.strip():
            raise ConfigurationError(
                f"Configuration value 'application.{key}' must not be empty."
            )