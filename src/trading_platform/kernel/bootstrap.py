from __future__ import annotations

from pathlib import Path

from trading_platform.kernel.application import Application
from trading_platform.kernel.bootstrap_pipeline import BootstrapPipeline
from trading_platform.kernel.configuration import ConfigurationService
from trading_platform.shared.logging.logger import configure_logging


def bootstrap(
    config_dir: Path,
    profile: str = "development",
) -> Application:
    app = Application()

    pipeline = BootstrapPipeline()

    pipeline.add_step(
        lambda: configure_logging(config_dir / "logging.yaml")
    )

    configuration = ConfigurationService(config_dir)

    pipeline.add_step(
        lambda: configuration.load(profile)
    )

    pipeline.add_step(
        lambda: app.container.register_singleton(
            "configuration",
            configuration,
        )
    )

    pipeline.add_step(
        lambda: app.runtime.register_service(
            "configuration",
            configuration,
        )
    )

    pipeline.add_step(
        lambda: setattr(app.runtime, "environment", profile)
    )

    pipeline.add_step(
        app.start
    )

    pipeline.execute()

    return app