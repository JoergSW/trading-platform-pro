from __future__ import annotations

import logging
from logging.config import dictConfig
from pathlib import Path
from typing import Any

import yaml


def configure(path: str | Path) -> logging.Logger:
    """
    Configure the application logger from a YAML configuration file.

    Args:
        path: Path to the logging configuration.

    Returns:
        Configured logger instance.
    """
    config_path = Path(path)

    if not config_path.exists():
        raise FileNotFoundError(f"Logging configuration not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as stream:
        configuration: dict[str, Any] = yaml.safe_load(stream)

    if not configuration:
        raise ValueError(f"Logging configuration is empty: {config_path}")

    dictConfig(configuration)

    return logging.getLogger("trading_platform")
