from __future__ import annotations

from pathlib import Path

from trading_platform.kernel.application import Application
from trading_platform.kernel.configuration import ConfigurationService
from trading_platform.shared.logging.logger import configure_logging


def bootstrap(
    config_dir: Path,
    profile: str = "development",
) -> Application:
    """Create and initialize the application runtime."""

    configure_logging(config_dir / "logging.yaml")

    app = Application()

    configuration = ConfigurationService(config_dir)
    configuration.load(profile)

    app.container.register_singleton(
        "configuration",
        configuration,
    )

    app.runtime.environment = profile
    app.runtime.profile = profile
    app.runtime.register_service("configuration", configuration)

    app.start()

    return app