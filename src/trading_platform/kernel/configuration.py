from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from trading_platform.shared.exceptions.base import ConfigurationError
from trading_platform.shared.validation.config_schema import validate_application_config


class ConfigurationService:
    def __init__(self, config_dir: Path) -> None:
        self.config_dir = config_dir
        self.profile: str | None = None
        self.settings: dict[str, Any] = {}

    def load(self, profile: str) -> dict[str, Any]:
        if not profile or not profile.strip():
            raise ConfigurationError("Configuration profile must not be empty.")

        normalized_profile = profile.strip()
        path = self.config_dir / f"{normalized_profile}.yaml"

        if not path.exists():
            raise ConfigurationError(f"Configuration file not found: {path}")

        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}

        if not isinstance(data, dict):
            raise ConfigurationError(
                f"Configuration file must contain a mapping: {path}"
            )

        validate_application_config(data)

        self.profile = normalized_profile
        self.settings = dict(data)

        return dict(self.settings)

    def get(self, dotted_key: str, default: Any = None) -> Any:
        if not dotted_key or not dotted_key.strip():
            return default

        current: Any = self.settings

        for part in dotted_key.split("."):
            if not part:
                return default
            if not isinstance(current, dict) or part not in current:
                return default
            current = current[part]

        return current