from __future__ import annotations

from pathlib import Path

from trading_platform.kernel.application import Application
from trading_platform.kernel.configuration import ConfigurationService
from trading_platform.kernel.dependency_container import DependencyContainer
from trading_platform.shared.logging.logger import configure_logging


def bootstrap(
    config_dir: Path,
    profile: str = "development",
) -> Application:
    """
    Bootstrap the Trading Platform runtime.

    Responsibilities:
    - configure logging
    - load configuration
    - register core services
    - create application
    - start runtime
    """

    configure_logging(config_dir / "logging.yaml")

    container = DependencyContainer()

    configuration = ConfigurationService(config_dir)
    configuration.load(profile)

    container.register_singleton(
        "configuration",
        configuration,
    )

    application = Application()

    application.container.register_singleton(
        "configuration",
        configuration,
    )

    application.start()

    return application