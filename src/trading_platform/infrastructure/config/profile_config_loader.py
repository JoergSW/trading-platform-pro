from pathlib import Path
from trading_platform.infrastructure.config.provider import ConfigurationProvider

class ProfileConfigLoader:
    def __init__(self, config_dir: Path, provider: ConfigurationProvider | None = None) -> None:
        self.config_dir = config_dir
        self.provider = provider or ConfigurationProvider()

    def load_profile(self, profile: str):
        return self.provider.load(self.config_dir / f"{profile}.yaml")
