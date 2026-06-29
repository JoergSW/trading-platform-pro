from pathlib import Path
from trading_platform.kernel.application import Application
from trading_platform.kernel.configuration import ConfigurationService
from trading_platform.kernel.dependency_container import DependencyContainer
from trading_platform.shared.logging.logger import configure_logging


def bootstrap(config_dir: Path, profile: str = "development") -> Application:
    configure_logging(config_dir / "logging.yaml")

    container = DependencyContainer()
    configuration = ConfigurationService(config_dir)
    configuration.load(profile)

    container.register_singleton("configuration", configuration)

    app = Application(container=container)
    app.start()
    return app
