from __future__ import annotations

from pathlib import Path
from typing import Any

from trading_platform.infrastructure.config.provider import ConfigurationProvider


class ProfileConfigLoader:
    """Loads profile-specific configuration files."""

    def __init__(
        self,
        config_dir: Path,
        provider: ConfigurationProvider | None = None,
    ) -> None:
        self.config_dir = config_dir
        self.provider = provider or ConfigurationProvider()

    def load_profile(self, profile: str) -> dict[str, Any]:
        profile = profile.strip()

        if not profile:
            raise ValueError("Profile name must not be empty.")

        config_path = self.config_dir / f"{profile}.yaml"
        return self.provider.load(config_path)
