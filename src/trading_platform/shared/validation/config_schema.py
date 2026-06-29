from typing import Any
from trading_platform.shared.exceptions.base import ConfigurationError


REQUIRED_APPLICATION_KEYS = ("name", "profile")


def validate_application_config(settings: dict[str, Any]) -> None:
    app = settings.get("application")
    if not isinstance(app, dict):
        raise ConfigurationError("Missing required configuration section: application")

    missing = [key for key in REQUIRED_APPLICATION_KEYS if key not in app]
    if missing:
        raise ConfigurationError(f"Missing application configuration keys: {', '.join(missing)}")
