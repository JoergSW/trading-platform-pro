from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class ConfigurationProvider:
    """Loads YAML configuration files."""

    def load(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        with path.open("r", encoding="utf-8") as stream:
            configuration = yaml.safe_load(stream)

        if configuration is None:
            return {}

        if not isinstance(configuration, dict):
            raise ValueError(f"Expected mapping in configuration file: {path}")

        return configuration
